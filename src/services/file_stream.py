"""File processing module for handling streaming operations and progress tracking.

This module provides efficient file processing capabilities for large JSON card data files.
It is part of the service layer that coordinates file operations:

Component Relationships:
- Works with CardFilterService for overall processing flow
- Uses CardParser for JSON parsing operations
- Integrates with CardProcessorInterface for card data processing
- Uses CardSetWriter for output management
- Leverages shared interfaces for consistency

Features:
- Memory-efficient streaming using ijson for parsing
- Progress tracking with tqdm
- Set-based card organization
- Metadata handling and preservation
- Error recovery and logging
- Buffered I/O operations
"""

import json
import ijson
from typing import BinaryIO, Optional, List, Dict, Any, cast
from tqdm import tqdm

from ..utils.container import Container
from ..io.writers.card import CardSetWriter
from ..utils.interfaces import LoggingInterface, CardProcessorInterface, FileHandlerInterface
from ..core.errors import CardFilterError
from ..core.config import CardFilterConfig


class FileProcessorError(CardFilterError):
    """Base exception for file processing errors."""
    pass


class StreamProcessingError(FileProcessorError):
    """Exception raised when stream processing fails."""
    pass


class MetadataError(FileProcessorError):
    """Exception raised when metadata handling fails."""
    pass


class FileProcessor:
    """Handles file processing operations with streaming and progress tracking.
    
    This processor is responsible for:
    - Coordinating streaming file operations
    - Managing progress tracking
    - Handling metadata preservation
    - Coordinating with other components for processing
    """

    def __init__(self, container: Container):
        """Initialize processor with container for services.
        
        Args:
            container: Dependency injection container providing access to services
        """
        self.config: CardFilterConfig = container.config()
        self.logging: LoggingInterface = container.logging_service()
        self.file_service: FileHandlerInterface = container.file_service()

    def write_schema_file(self, dump_schema: str) -> None:
        """Write default schema to file.
        
        Args:
            dump_schema: Path where schema will be written
            
        Raises:
            FileProcessorError: If schema writing fails
        """
        try:
            with self.file_service.open_file(dump_schema, 'w', encoding='utf-8') as schema_file:
                json.dump(self.config.default_schema, schema_file, indent=4)
        except Exception as e:
            error_msg = f"Failed to write schema file: {str(e)}"
            self.logging.error(error_msg)
            raise FileProcessorError(error_msg) from e

    def _process_card(
        self,
        current_card: Dict[str, Any],
        card_processor: CardProcessorInterface,
        filters: Optional[Dict[str, Any]],
        schema: Optional[List[str]],
        additional_languages: Optional[List[str]],
        set_writer: CardSetWriter
    ) -> None:
        """Process a single card and write if it passes filters.
        
        Args:
            current_card: Card data to process
            card_processor: Processor for card data
            filters: Optional filter conditions
            schema: Optional schema for field selection
            additional_languages: Optional languages to include
            set_writer: Writer for card sets
            
        Raises:
            StreamProcessingError: If card processing fails
        """
        try:
            processed_card = card_processor.process_card(
                current_card, filters, schema, additional_languages
            )
            if processed_card is not None:
                set_writer.write_processed_card(processed_card)
        except Exception as e:
            error_msg = f"Failed to process card: {str(e)}"
            self.logging.error(error_msg)
            raise StreamProcessingError(error_msg) from e

    def _handle_prefix(
        self,
        prefix: str,
        event: str,
        value: Any,
        current_state: Dict[str, Any],
        set_writer: CardSetWriter,
        card_processor: CardProcessorInterface,
        filters: Optional[Dict[str, Any]],
        schema: Optional[List[str]],
        additional_languages: Optional[List[str]]
    ) -> None:
        """Handle a single prefix event from the JSON parser.
        
        Args:
            prefix: Current JSON path prefix
            event: Parser event type
            value: Current value
            current_state: Current processing state
            set_writer: Writer for card sets
            card_processor: Processor for card data
            filters: Optional filter conditions
            schema: Optional schema for field selection
            additional_languages: Optional languages to include
            
        Raises:
            StreamProcessingError: If prefix handling fails
        """
        try:
            if prefix.startswith("data."):
                if prefix.endswith(".block"):
                    return

                set_name = prefix.split(".")[1]
                
                if prefix.endswith(".cards.item"):
                    if event == "start_map":
                        current_state['current_card'] = {}
                        if set_name != current_state['current_set']:
                            set_writer.handle_set_transition(set_name)
                            current_state['current_set'] = set_name
                    elif event == "end_map":
                        self._process_card(
                            current_state['current_card'],
                            card_processor,
                            filters,
                            schema,
                            additional_languages,
                            set_writer
                        )
                elif prefix.startswith(f"data.{set_name}.cards.item."):
                    card_key = prefix.split(".")[-1]
                    current_state['current_card'][card_key] = value
        except Exception as e:
            error_msg = f"Failed to handle prefix {prefix}: {str(e)}"
            self.logging.error(error_msg)
            raise StreamProcessingError(error_msg) from e

    def _write_metadata(self, outfile: BinaryIO, value: Any) -> None:
        """Write metadata section to output file.
        
        Args:
            outfile: Output file stream
            value: Metadata value to write
            
        Raises:
            MetadataError: If metadata writing fails
        """
        try:
            # Just write the opening brace
            outfile.write(b'{')
            # Write metadata
            metadata_json = json.dumps(value).encode('utf-8')
            outfile.write(b'"meta":')
            outfile.write(metadata_json)
            # Write data section opening
            outfile.write(b',"data":{}')
        except Exception as e:
            error_msg = f"Failed to write metadata: {str(e)}"
            self.logging.error(error_msg)
            raise MetadataError(error_msg) from e

    def process_file_stream(
        self,
        infile: BinaryIO,
        outfile: BinaryIO,
        card_processor: CardProcessorInterface,
        schema: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        additional_languages: Optional[List[str]] = None,
    ) -> None:
        """Process a file stream with progress tracking."""
        try:
            set_writer = CardSetWriter(outfile, cast(CardFilterConfig, self.config))
            
            parser = ijson.parse(infile)
            file_size = infile.seek(0, 2)
            infile.seek(0)
            
            current_state = {
                'meta_written': False,
                'current_card': {},
                'current_set': None,
                'meta_value': None
            }
            
            progress_bar = None
            if isinstance(file_size, int):
                progress_bar = tqdm(total=file_size, unit='B', unit_scale=True, desc="Processing file")
            
            try:
                # First pass: collect metadata
                for prefix, event, value in parser:
                    if prefix == 'meta':
                        current_state['meta_value'] = value
                        break
                
                # Reset file position for main processing
                infile.seek(0)
                
                # Write metadata section
                self._write_metadata(outfile, current_state['meta_value'] or {})
                current_state['meta_written'] = True
                
                # Main processing pass
                parser = ijson.parse(infile)
                for prefix, event, value in parser:
                    if prefix.startswith("data."):
                        self._handle_prefix(
                            prefix, event, value,
                            current_state, set_writer,
                            card_processor, filters,
                            schema, additional_languages
                        )
                    if progress_bar:
                        progress_bar.update(1)
                        
            except ijson.JSONError as e:
                error_msg = f"JSON parsing error: {str(e)}"
                self.logging.error(error_msg)
                raise StreamProcessingError(error_msg) from e
            finally:
                if progress_bar:
                    progress_bar.close()
            
            # Close out the JSON structure
            outfile.write(b"}")  # Close root object
            
        except Exception as e:
            if not isinstance(e, (StreamProcessingError, MetadataError)):
                error_msg = f"File processing error: {str(e)}"
                self.logging.error(error_msg)
                raise FileProcessorError(error_msg) from e
            raise