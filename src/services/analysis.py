"""Main service module for coordinating type-safe card filtering operations.

This module provides the primary service layer for the card filtering application,
implementing type-safe coordination between various components to process and
filter Magic: The Gathering card data.

Architecture:
- Uses CardProcessorInterface for type-safe card processing
- Uses FileProcessor for validated stream operations
- Uses CardParser for type-checked filter parsing
- Implements validated interfaces for component consistency
- Uses dependency injection for type-safe component coupling

Features:
- Type-safe dependency injection and coordination
- Validated input/output file operations
- Schema validation and management
- Type-checked filter application
- Encoding-aware language support
- Comprehensive error handling with context
- Resource cleanup and management

Example:
    ```python
    # Initialize with type-safe container
    service = CardFilterService(container)
    
    try:
        # Process cards with validation
        service.process_cards(
            input_file="cards.json",
            output_file="filtered.json",
            schema=["name", "manaCost"],
            filters={"colors": {"contains": "R"}},
            additional_languages=["Japanese"]
        )
    except FileNotFoundError as e:
        print(f"Input file error: {e}")
    except ValueError as e:
        print(f"Validation error: {e}")
    except CardFilterServiceError as e:
        print(f"Processing error: {e}")
    ```
"""

from typing import Optional, List, Dict, Any, cast, BinaryIO

from ..utils.container import Container
from ..utils.interfaces import LoggingInterface, CardProcessorInterface, FileHandlerInterface
from ..core.errors import CardFilterError
from .file_stream import FileProcessor
from .filter_parser import CardParser


class CardFilterServiceError(CardFilterError):
    """Base exception for card filter service errors with context.
    
    This exception provides detailed error context for service-level
    failures, preserving the error chain for debugging.
    
    Example:
        ```python
        try:
            service.process_cards(...)
        except CardFilterServiceError as e:
            print(f"Service error: {e}")
            if e.__cause__:
                print(f"Caused by: {e.__cause__}")
        ```
    """
    pass


class CardFilterService:
    """Main service for coordinating type-safe filtering operations.
    
    This service acts as the primary coordinator for the card filtering
    pipeline, implementing type-safe component interaction and comprehensive
    error handling throughout the process.

    Features:
    - Type-safe dependency management
    - Validated component coordination
    - Resource management
    - Error context preservation
    - Comprehensive logging
    """

    def __init__(self, container: Container):
        """Initialize service with type-safe dependency injection.
        
        Args:
            container: Validated dependency container
            
        Example:
            ```python
            # Initialize with validated components
            container = Container()
            container.register_logging(logger)
            container.register_processor(processor)
            
            service = CardFilterService(container)
            ```
        """
        self.config = container.config()
        self.logging: LoggingInterface = container.logging_service()
        self.file_service: FileHandlerInterface = container.file_service()
        self.card_processor: CardProcessorInterface = container.card_processor()
        self.processor = FileProcessor(container)
        self.parser = CardParser(container)

    def process_filter_string(self, filter_str: str) -> Dict[str, Any]:
        """Process a filter string with type validation.
        
        Args:
            filter_str: Validated JSON filter string
            
        Returns:
            Dict: Type-checked filter conditions
            
        Raises:
            FilterParseError: If parsing or validation fails
            
        Example:
            ```python
            try:
                filters = service.process_filter_string(
                    '{"colors": {"contains": "R"}}'
                )
                print(f"Parsed filters: {filters}")
            except FilterParseError as e:
                print(f"Invalid filter: {e}")
            ```
        """
        return self.parser.parse_filter_string(filter_str)

    def process_cards(
        self,
        input_file: str,
        output_file: str,
        schema: Optional[List[str]] = None,
        dump_schema: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        additional_languages: Optional[List[str]] = None,
    ) -> None:
        """Process and filter cards with comprehensive validation.
        
        This method coordinates the complete card processing pipeline
        with type safety and proper resource management:
        1. Validates input file size and accessibility
        2. Opens streams with proper encoding and buffering
        3. Processes cards with type checking
        4. Manages schema validation and output
        
        Args:
            input_file: Validated input JSON path
            output_file: Validated output path
            schema: Optional validated field list
            dump_schema: Optional schema output path
            filters: Optional type-checked filters
            additional_languages: Optional validated language codes
            
        Raises:
            FileNotFoundError: If input file is invalid
            ValueError: If validation fails
            IOError: If file operations fail
            CardFilterServiceError: For processing errors
            
        Example:
            ```python
            try:
                # Process with validation
                service.process_cards(
                    input_file="cards.json",
                    output_file="filtered.json",
                    schema=["name", "manaCost"],
                    filters={
                        "colors": {"contains": "R"},
                        "convertedManaCost": {"lte": 3}
                    },
                    additional_languages=["Japanese", "German"]
                )
                
            except FileNotFoundError as e:
                print(f"File error: {e}")
            except ValueError as e:
                print(f"Validation error: {e}")
            except CardFilterServiceError as e:
                print(f"Processing error: {e}")
                if e.__cause__:
                    print(f"Caused by: {e.__cause__}")
            ```
        """
        try:
            # Validate input with type checking
            if not self.file_service.validate_input_file(input_file):
                error_msg = f"Invalid input file: {input_file}"
                self.logging.error(error_msg)
                raise ValueError(error_msg)

            # Process streams with resource management
            with self.file_service.open_file(input_file, mode='rb') as infile, \
                 self.file_service.open_file(output_file, mode='wb') as outfile:
                
                try:
                    self.processor.process_file_stream(
                        infile=cast(BinaryIO, infile),
                        outfile=cast(BinaryIO, outfile),
                        card_processor=self.card_processor,
                        schema=schema,
                        filters=filters,
                        additional_languages=additional_languages
                    )
                except Exception as e:
                    error_msg = f"Error processing cards: {str(e)}"
                    self.logging.error(error_msg)
                    raise CardFilterServiceError(error_msg) from e

            # Write schema with validation
            if dump_schema:
                try:
                    self.processor.write_schema_file(dump_schema)
                except Exception as e:
                    error_msg = f"Failed to write schema file: {str(e)}"
                    self.logging.error(error_msg)
                    raise CardFilterServiceError(error_msg) from e

        except (ValueError, CardFilterServiceError):
            # These errors have already been logged
            raise
        except Exception as e:
            # Log unexpected errors with context
            self.logging.error(str(e))
            raise
