"""Deck list parsing module for Magic: The Gathering card extraction.

This module provides functionality for parsing deck lists in various formats,
with support for set codes and collector numbers. It handles different deck list
formats and provides detailed error reporting.

Features:
- Parses deck lists with quantities, card names, set codes, and collector numbers
- Supports multiple deck list formats
- Provides detailed error reporting and validation
- Handles section headers and empty lines gracefully
- Logs parsing operations and warnings

Example:
    Basic usage:
    ```python
    parser = DeckListParser(logger)
    
    # Parse a deck list file
    try:
        cards = parser.parse_deck_list("deck.txt")
        for card in cards:
            print(f"{card.quantity}x {card.name} ({card.set_code}) {card.collector_number}")
    except DeckParserError as e:
        print(f"Error parsing deck: {e}")
    ```

    Example deck list format:
    ```
    4 Shoreline Looter (BLB) 70
    2 Island (BRO) 280
    3 Consider (DMU) 44
    ```

Note:
    The parser is designed to be flexible while maintaining strict validation
    to ensure data integrity. It will skip invalid lines with warnings rather
    than failing completely, allowing for partial deck list processing.
"""

import re
from typing import List, TextIO, Optional
from ...utils.models import CardReference
from ...utils.interfaces import LoggingInterface
from ...core.errors import CardFilterError


class DeckParserError(CardFilterError):
    """Base exception for deck parsing errors.
    
    This exception is raised for general parsing errors that don't fit into
    more specific error categories.
    
    Example:
        ```python
        try:
            cards = parser.parse_deck_list("deck.txt")
        except DeckParserError as e:
            print(f"Failed to parse deck: {e}")
        ```
    """
    pass


class InvalidDeckFormatError(DeckParserError):
    """Exception raised when deck list format is invalid.
    
    This exception is raised when a line in the deck list doesn't match
    the expected format of "{quantity} {card name} ({set code}) {collector number}".
    
    Example:
        ```python
        try:
            card_ref = parser.parse_line("Invalid Format")
        except InvalidDeckFormatError as e:
            print(f"Invalid line format: {e}")
        ```
    """
    pass


class EmptyDeckError(DeckParserError):
    """Exception raised when no valid cards are found in deck list.
    
    This exception is raised when a deck list file contains no valid
    card references after parsing all lines.
    
    Example:
        ```python
        try:
            cards = parser.parse_deck_list("empty_deck.txt")
        except EmptyDeckError as e:
            print(f"Deck list is empty: {e}")
        ```
    """
    pass


class DeckListParser:
    """Parser for Magic: The Gathering deck lists.
    
    This class handles parsing of deck lists in the format:
    {quantity} {card name} ({set code}) {collector number}
    
    It provides methods for parsing both individual lines and complete
    deck list files, with comprehensive error handling and logging.

    Attributes:
        card_regex (re.Pattern): Compiled regex for matching card entries
        section_regex (re.Pattern): Compiled regex for matching section headers
        logger (LoggingInterface): LoggingInterface instance for operation logging

    Example:
        ```python
        parser = DeckListParser(logger)
        
        # Parse a complete deck list
        try:
            cards = parser.parse_deck_list("deck.txt")
            print(f"Successfully parsed {len(cards)} cards")
            
            for card in cards:
                print(f"{card.quantity}x {card.name}")
                
        except FileNotFoundError:
            print("Deck list file not found")
        except EmptyDeckError:
            print("No valid cards found in deck list")
        except DeckParserError as e:
            print(f"Error parsing deck: {e}")
        ```
    """

    # Regex pattern for deck list entries
    # Matches: "{quantity} {card name} ({set code}) {collector number}"
    # Set code can be any length of letters/numbers
    # Collector number can contain letters and numbers
    CARD_PATTERN = r'^(\d+)\s+([^(]+?)\s+\(([A-Z0-9]+)\)\s+([A-Za-z0-9]+)$'
    SECTION_PATTERN = r'^[A-Za-z]+:$'

    def __init__(self, logger: LoggingInterface):
        """Initialize the DeckListParser.
        
        Args:
            logger (LoggingInterface): LoggingInterface service for recording operations and errors
            
        Example:
            ```python
            from .interfaces import LoggingInterface
            
            class CustomLogger(LoggingInterface):
                def error(self, message: str) -> None:
                    print(f"ERROR: {message}")
                def warning(self, message: str) -> None:
                    print(f"WARNING: {message}")
            
            parser = DeckListParser(CustomLogger())
            ```
        """
        self.card_regex = re.compile(self.CARD_PATTERN)
        self.section_regex = re.compile(self.SECTION_PATTERN)
        self.logger = logger

    def parse_line(self, line: str) -> CardReference:
        """Parse a single line from a deck list.
        
        This method parses a single line in the format:
        {quantity} {card name} ({set code}) {collector number}
        
        Args:
            line (str): A line from the deck list file
            
        Returns:
            CardReference: Structured reference to the card
            
        Raises:
            InvalidDeckFormatError: If the line format is invalid
            
        Example:
            ```python
            try:
                card_ref = parser.parse_line("4 Lightning Bolt (2ED) 157")
                print(f"Parsed: {card_ref.quantity}x {card_ref.name}")
                print(f"Set: {card_ref.set_code}")
                print(f"Collector Number: {card_ref.collector_number}")
            except InvalidDeckFormatError as e:
                print(f"Invalid format: {e}")
            ```
        """
        # Strip whitespace and skip empty lines
        line = line.strip()
        if not line:
            raise InvalidDeckFormatError("Empty line")

        # Check if line is a section header
        if self.section_regex.match(line):
            error_msg = f"Section header '{line}' not supported in this format"
            self.logger.error(error_msg)
            raise InvalidDeckFormatError(error_msg)

        # Match the line against the pattern
        match = self.card_regex.match(line)
        if not match:
            raise InvalidDeckFormatError(f"Invalid line format: {line}")

        # Extract components
        try:
            quantity, name, set_code, collector_number = match.groups()
            return CardReference(
                name=name.strip(),
                set_code=set_code.strip(),
                collector_number=collector_number.strip(),
                quantity=int(quantity)
            )
        except ValueError as e:
            raise InvalidDeckFormatError(f"Invalid card reference data: {str(e)}")

    def parse_deck_list(self, file_path: str) -> List[CardReference]:
        """Parse a deck list file into card references.
        
        This method reads a deck list file and parses all valid card entries,
        skipping invalid lines with warnings.
        
        Args:
            file_path (str): Path to the deck list file
            
        Returns:
            List[CardReference]: List of parsed card references
            
        Raises:
            FileNotFoundError: If the deck list file doesn't exist
            EmptyDeckError: If no valid cards are found
            DeckParserError: For other parsing errors
            
        Example:
            ```python
            try:
                cards = parser.parse_deck_list("deck.txt")
                print(f"Successfully parsed {len(cards)} cards:")
                
                for card in cards:
                    print(f"{card.quantity}x {card.name} ({card.set_code})")
                    
            except FileNotFoundError:
                print("Deck list file not found")
            except EmptyDeckError:
                print("No valid cards found in deck list")
            except DeckParserError as e:
                print(f"Error parsing deck: {e}")
            ```
        """
        try:
            with open(file_path, 'r') as deck_file:
                return self.parse_deck_list_file(deck_file)
        except FileNotFoundError:
            error_msg = f"Deck list file not found: {file_path}"
            self.logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        except EmptyDeckError:
            error_msg = "No valid card references found in deck list"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        except Exception as e:
            error_msg = f"Error reading deck list: {str(e)}"
            self.logger.error(error_msg)
            raise DeckParserError(error_msg) from e

    def parse_deck_list_file(self, deck_file: TextIO) -> List[CardReference]:
        """Parse a deck list from an already opened file.
        
        This method processes an opened file object containing a deck list,
        parsing all valid card entries and handling errors for invalid lines.
        
        Args:
            deck_file (TextIO): An opened file object containing the deck list
            
        Returns:
            List[CardReference]: List of parsed card references
            
        Raises:
            EmptyDeckError: If no valid cards are found
            DeckParserError: For other parsing errors
            
        Example:
            ```python
            with open("deck.txt", "r") as file:
                try:
                    cards = parser.parse_deck_list_file(file)
                    print(f"Parsed {len(cards)} cards")
                    
                    # Group cards by set
                    sets = {}
                    for card in cards:
                        sets.setdefault(card.set_code, []).append(card)
                        
                    for set_code, set_cards in sets.items():
                        print(f"\nSet {set_code}:")
                        for card in set_cards:
                            print(f"  {card.quantity}x {card.name}")
                            
                except EmptyDeckError:
                    print("No valid cards found")
                except DeckParserError as e:
                    print(f"Parsing error: {e}")
            ```
        """
        card_references = []
        for line_number, line in enumerate(deck_file, 1):
            try:
                # Skip empty lines and attempt to parse valid lines
                if line.strip():
                    try:
                        card_ref = self.parse_line(line)
                        card_references.append(card_ref)
                    except InvalidDeckFormatError as e:
                        self.logger.warning(
                            f"Error on line {line_number}: {str(e)}"
                        )
            except Exception as e:
                self.logger.warning(f"Warning on line {line_number}: {str(e)}")

        if not card_references:
            raise EmptyDeckError("No valid card references found in deck list")

        return card_references
