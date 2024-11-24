"""Module for card matching functionality.

This module provides functionality for finding and matching cards in archives,
implementing flexible matching strategies with fallbacks.
"""

from typing import Dict, Optional, Protocol, List
from ..utils.models import CardReference


class LoggingInterface(Protocol):
    """Protocol defining the logging interface."""
    def warning(self, message: str) -> None: ...
    def debug(self, message: str) -> None: ...


class CardMatcher:
    """Handles finding and matching cards in archives.
    
    This class implements the logic for finding cards in archives,
    with support for exact and fallback matching strategies.
    """

    def __init__(self, logger: LoggingInterface):
        """Initialize with logger for warnings and debug output.
        
        Args:
            logger: Thread-safe logging interface
        """
        self.logger = logger

    def _matches_card_name(self, card_name: str, reference_name: str) -> bool:
        """Check if a card name matches the reference name.
        
        Handles both simple matches and double-faced cards.
        
        Args:
            card_name: The name from the card data
            reference_name: The name we're looking for
            
        Returns:
            bool: True if names match, False otherwise
        """
        return card_name.startswith(reference_name + " //") or card_name == reference_name

    def _get_cards_from_set(self, set_data: Dict) -> List[Dict]:
        """Extract cards list from set data.
        
        Args:
            set_data: The set data dictionary
            
        Returns:
            List[Dict]: List of cards, empty if no cards found
        """
        return set_data.get("cards", [])

    def _print_debug(self, card_ref: CardReference, match_type: str, set_code: str = "", card_number: str = "", debug: bool = False) -> None:
        """Print debug information if debug is enabled.
        
        Args:
            card_ref: The card reference being matched
            match_type: Type of match result
            set_code: Optional set code for logging
            card_number: Optional collector number for logging
            debug: Whether debug output is enabled
        """
        if not debug:
            return

        if match_type == "exact":
            print(f"Found exact match for {card_ref.name} in requested set {card_ref.set_code}")
        elif match_type == "fallback_candidate":
            print(f"Found '{card_ref.name}' in set {set_code} (number {card_number}) - continuing to search for exact match in {card_ref.set_code}")
        elif match_type == "fallback_used":
            print(f"Using fallback match for {card_ref.name} from different set (exact match in {card_ref.set_code} not found)")

    def _find_exact_match(self, card_ref: CardReference, set_data: Dict, debug: bool = False) -> Optional[Dict]:
        """Try to find an exact match by name, set code, and collector number.
        
        Args:
            card_ref: The validated card reference
            set_data: The set data to search in
            debug: Whether to show debug output
            
        Returns:
            Optional[Dict]: The matching card data, or None if not found
        """
        for card in self._get_cards_from_set(set_data):
            card_name = card.get("name", "")
            if (self._matches_card_name(card_name, card_ref.name) and
                str(card.get("number", "")) == card_ref.collector_number):
                self._print_debug(card_ref, "exact", debug=debug)
                self.logger.debug(f"Found exact match for {card_ref.name} in requested set {card_ref.set_code}")
                return card
        return None

    def _find_fallback_match(self, card_ref: CardReference, archive_data: Dict, debug: bool = False) -> Optional[Dict]:
        """Try to find a fallback match by name only.
        
        Args:
            card_ref: The validated card reference
            archive_data: The archive data to search in
            debug: Whether to show debug output
            
        Returns:
            Optional[Dict]: The first matching card data, or None if not found
        """
        fallback_match = None
        fallback_set = ""

        for set_code, set_data in archive_data["data"].items():
            if set_code == card_ref.set_code:
                continue  # Skip requested set, as it was already checked
            for card in self._get_cards_from_set(set_data):
                card_name = card.get("name", "")
                if self._matches_card_name(card_name, card_ref.name):
                    self._print_debug(
                        card_ref,
                        "fallback_candidate",
                        set_code,
                        str(card.get("number", "")),
                        debug=True
                    )
                    if not fallback_match:  # Keep the first match as fallback
                        fallback_match = card
                        fallback_set = set_code

        if fallback_match:
            self._print_debug(card_ref, "fallback_used", fallback_set, debug=debug)
            self.logger.debug(f"Using fallback match for {card_ref.name} from different set (exact match in {card_ref.set_code} not found)")
            return fallback_match
        return None

    def find_card(self, card_ref: CardReference, archive_data: Dict, debug: bool = False) -> Optional[Dict]:
        """Find a card in the archive with fallback matching.
        
        Implements a two-stage search strategy:
        1. Exact match by name, set code, and collector number
        2. Fallback match by name only if exact match fails
        
        Args:
            card_ref: The validated card reference
            archive_data: The loaded archive data
            debug: Whether to show debug output
            
        Returns:
            Optional[Dict]: The matching card data, or None if not found
        """
        if "data" not in archive_data:
            self.logger.warning("Archive missing 'data' section")
            return None

        # Try exact match first
        if card_ref.set_code in archive_data["data"]:
            if match := self._find_exact_match(card_ref, archive_data["data"][card_ref.set_code], debug):
                return match

        # Try fallback match if exact match fails
        if match := self._find_fallback_match(card_ref, archive_data, debug):
            return match

        return None
