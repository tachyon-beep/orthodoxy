"""Service for extracting card data based on deck lists with validation.

This module provides functionality for extracting complete card data from a JSON
archive based on deck list references, implementing comprehensive validation,
type safety, and error handling.
"""

from typing import Dict, List, Optional, Union, Protocol
from datetime import datetime
from ..utils.models import CardReference, DeckListStats
from ..io.parsers.deck import DeckListParser
from ..analysis.cards import CardProcessorInterface
from .archive import ArchiveLoader
from .card_resolver import CardMatcher
from .schema import SchemaValidator
from .writer import DeckWriter


class LoggingInterface(Protocol):
    """Protocol defining the logging interface with type safety."""
    def error(self, message: str) -> None: ...
    def warning(self, message: str) -> None: ...
    def info(self, message: str) -> None: ...
    def debug(self, message: str) -> None: ...


class DeckExtractorService:
    """Service for extracting card data with validation.
    
    This service handles the extraction of card data from JSON archives
    based on deck list references, implementing comprehensive validation
    and error handling.

    Features:
    - Type-safe data extraction
    - Schema validation
    - Flexible card matching
    - Statistics tracking
    - Error context preservation
    """

    def __init__(self, card_processor: CardProcessorInterface, logger: LoggingInterface):
        """Initialize with validated components.
        
        Args:
            card_processor: Type-safe card processor
            logger: Thread-safe logging interface
        """
        self.card_processor = card_processor
        self.logger = logger
        self.deck_parser = DeckListParser(logger=logger)
        self.card_matcher = CardMatcher(logger=logger)
        self.stats = DeckListStats()

    def _load_archive(self, archive_path: str) -> Dict:
        """Delegate archive loading to ArchiveLoader."""
        return ArchiveLoader.load_archive(archive_path)

    def _get_required_fields(self, schema: Union[str, Dict, None]) -> Optional[List[str]]:
        """Delegate schema validation to SchemaValidator."""
        return SchemaValidator.get_required_fields(schema)

    def _find_card(self, card_ref: CardReference, archive_data: Dict, debug: bool = False) -> Optional[Dict]:
        """Delegate card finding to CardMatcher."""
        return self.card_matcher.find_card(card_ref, archive_data, debug)

    def extract_deck_cards(
        self,
        archive_path: str,
        decklist_path: str,
        output_path: str,
        schema: Optional[Union[str, Dict]] = None,
        debug: bool = False
    ) -> DeckListStats:
        """Extract card data with comprehensive validation.
        
        This method implements the complete extraction process with
        proper validation, error handling, and statistics tracking.
        
        Args:
            archive_path: Path to the JSON archive file
            decklist_path: Path to the deck list file
            output_path: Path for the output JSON file
            schema: Optional schema for validation
            debug: Whether to show debug output
            
        Returns:
            DeckListStats: Detailed extraction statistics
            
        Raises:
            FileNotFoundError: If input files don't exist
            ValueError: If input formats are invalid
        """
        # Reset statistics
        self.stats = DeckListStats()

        # Load and validate the archive
        archive_data = self._load_archive(archive_path)

        # Get required fields from schema
        required_fields = self._get_required_fields(schema)

        # Parse the deck list with validation
        card_references = self.deck_parser.parse_deck_list(decklist_path)
        self.stats.total_cards = len(card_references)

        # Extract matching cards with validation
        extracted_cards = []
        missing_cards = []
        
        for card_ref in card_references:
            card_data = self._find_card(card_ref, archive_data, debug)
            
            if card_data:
                # Process the card with validation
                processed_card = self.card_processor.process_card(
                    card_data,
                    filters=None,
                    schema=required_fields,
                    additional_languages=None
                )
                
                if processed_card:
                    # Add quantity information
                    processed_card["quantity"] = card_ref.quantity
                    extracted_cards.append(processed_card)
                    self.stats.cards_found += 1
            else:
                self.stats.cards_missing += 1
                missing_cards.append(f"{card_ref.name} ({card_ref.set_code}) {card_ref.collector_number}")

        # Report missing cards
        if missing_cards:
            print("\nMissing cards:")
            for card in missing_cards:
                print(f"  {card}")

        # Write the output with validation
        DeckWriter.write_deck(output_path, extracted_cards)

        return self.stats
