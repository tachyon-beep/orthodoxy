"""Parser module for handling filter strings and file parsing operations.

This module provides parsing functionality for both filter criteria and card data:

Features:
- JSON filter string parsing with automatic type inference
- Structured filter format validation
- Streaming card data parsing
- Metadata preservation and handling
- Error recovery and detailed error reporting
- Memory-efficient processing
"""

import json
import ijson
from typing import Dict, Any, IO, Iterator, Tuple, Optional

from ..utils.container import Container
from ..utils.interfaces import LoggingInterface
from ..core.errors import CardFilterError

class ParserError(CardFilterError):
    """Base exception for parsing errors."""
    pass


class FilterParseError(ParserError):
    """Exception raised when filter parsing fails."""
    pass


class CardDataParseError(ParserError):
    """Exception raised when card data parsing fails."""
    pass


class CardParser:
    """Handles parsing of filter strings and card data."""

    def __init__(self, container: Container):
        """Initialize parser with container for services.
        
        Args:
            container: Dependency injection container providing access to services
        """
        # Get the logger instance directly
        self.logger: LoggingInterface = container.logging_service()

    def parse_filter_string(self, filter_str: str) -> Dict[str, Any]:
        """Parse filter string into structured format.
        
        Args:
            filter_str: JSON string containing filter criteria
            
        Returns:
            Dict containing structured filter conditions
            
        Raises:
            FilterParseError: If filter parsing fails
        """
        try:
            raw_filters = json.loads(filter_str)
            return {
                k: (
                    {"eq": v}
                    if isinstance(v, (str, int, float))
                    else {"in": v} if isinstance(v, list) else v
                )
                for k, v in raw_filters.items()
            }
        except json.JSONDecodeError as e:
            error_msg = f"Invalid filter JSON: {str(e)}"
            self.logger.error(error_msg)
            raise FilterParseError(error_msg) from e
        except Exception as e:
            error_msg = f"Error parsing filter: {str(e)}"
            self.logger.error(error_msg)
            raise FilterParseError(error_msg) from e

    def validate_prefix(self, prefix: str) -> Tuple[bool, str]:
        """Validate the prefix format and extract set name.
        
        Args:
            prefix: The prefix to validate
            
        Returns:
            Tuple containing:
            - Boolean indicating if prefix is valid
            - Set name if valid, error message if invalid
        """
        if not prefix or not isinstance(prefix, str):
            return False, "Invalid prefix: None or non-string value"

        parts = prefix.split(".")
        if len(parts) < 2:
            return False, f"Invalid prefix format: {prefix}"
            
        if parts[0] != "data":
            return False, f"Invalid prefix format: {prefix}"

        return True, parts[1]

    def process_card_data(self, prefix: str, event: str, value: Any, current_card: dict) -> Tuple[Optional[str], dict]:
        """Process card data from parser events.
        
        Args:
            prefix: Current path in the JSON structure
            event: Type of parsing event
            value: Value associated with the event
            current_card: Current card being processed
            
        Returns:
            Tuple containing:
            - Set name (or None if not applicable)
            - Updated card dictionary
            
        Raises:
            CardDataParseError: If card data processing fails
        """
        try:
            if prefix.endswith(".block"):
                return None, current_card

            valid, result = self.validate_prefix(prefix)
            if not valid:
                self.logger.error(result)
                raise CardDataParseError(result)

            set_name = result
            
            if prefix.endswith(".cards.item") and event == "start_map":
                return set_name, {}
            elif prefix.endswith(".cards.item") and event == "end_map":
                return set_name, current_card
            elif prefix.startswith(f"data.{set_name}.cards.item."):
                card_key = prefix.split(".")[-1]
                current_card[card_key] = value
                
            return set_name, current_card
        except CardDataParseError:
            raise
        except Exception as e:
            error_msg = f"Error processing card data: {str(e)}"
            self.logger.error(error_msg)
            raise CardDataParseError(error_msg) from e
