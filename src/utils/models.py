"""Data models for Magic: The Gathering card filtering operations.

This module defines the core data models used throughout the card filtering application.
It provides enums and dataclasses that represent various states and statistics during
the card processing and writing operations.

Features:
- Strongly typed data structures with validation
- State management for card writing operations
- Statistics tracking for various operations
- Card reference parsing and validation
- Deck list processing statistics

Example:
    Basic usage of models:
    ```python
    # Track writing statistics
    stats = WriterStats()
    stats.cards_written += 1
    stats.sets_processed += 1
    
    print(f"Processed {stats.cards_written} cards in {stats.sets_processed} sets")
    print(f"Encountered {stats.errors_encountered} errors")

    # Create and validate a card reference
    try:
        card = CardReference(
            name="Lightning Bolt",
            set_code="2ED",
            collector_number="157",
            quantity=4
        )
        print(f"Adding {card.quantity}x {card.name} from {card.set_code}")
    except ValueError as e:
        print(f"Invalid card reference: {e}")
    ```

Note:
    All models include validation to ensure data integrity. Invalid data will
    raise appropriate exceptions with descriptive error messages.
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional


class WriterState(Enum):
    """Represents the possible states of the CardSetWriter.
    
    This enum is used to track and manage the state of card writing operations,
    ensuring proper sequencing of operations and preventing invalid state
    transitions.

    Attributes:
        INITIAL: Initial state before any writing has occurred
        SET_OPEN: A card set is currently open for writing
        SET_CLOSED: The current card set has been closed

    Example:
        ```python
        state = WriterState.INITIAL
        
        # Check if we can start writing
        if state == WriterState.INITIAL:
            state = WriterState.SET_OPEN
            start_writing()
            
        # Check if we can add cards
        if state == WriterState.SET_OPEN:
            write_card(card)
            
        # Close the set when done
        if state == WriterState.SET_OPEN:
            state = WriterState.SET_CLOSED
            finish_writing()
        ```
    """
    INITIAL = auto()
    SET_OPEN = auto()
    SET_CLOSED = auto()


@dataclass
class WriterStats:
    """Statistics for card writing operations.
    
    This class tracks various metrics during card writing operations,
    providing insights into the processing results and any issues
    encountered.

    Attributes:
        cards_written (int): Number of cards successfully written
        sets_processed (int): Number of card sets processed
        errors_encountered (int): Number of errors encountered during processing

    Example:
        ```python
        stats = WriterStats()
        
        # Process some cards
        try:
            stats.cards_written += 1
            process_card(card)
        except Exception:
            stats.errors_encountered += 1
            
        # Process a new set
        stats.sets_processed += 1
        
        # Report statistics
        print(f"Processed {stats.cards_written} cards")
        print(f"Completed {stats.sets_processed} sets")
        if stats.errors_encountered:
            print(f"Encountered {stats.errors_encountered} errors")
        ```
    """
    cards_written: int = 0
    sets_processed: int = 0
    errors_encountered: int = 0


@dataclass
class CardReference:
    """Structured reference to a card from a deck list.
    
    This class represents a single card entry from a deck list, including
    all necessary information to uniquely identify the card and specify
    its quantity.

    Attributes:
        name (str): The name of the card (e.g., "Lightning Bolt")
        set_code (str): The three-letter set code (e.g., "2ED")
        collector_number (str): The collector number within the set
        quantity (int): Number of copies in the deck (must be positive)

    Raises:
        ValueError: If any of the following validation rules are violated:
            - Card name is empty
            - Set code is not exactly 3 characters
            - Collector number is empty
            - Quantity is less than 1

    Example:
        ```python
        # Create a valid card reference
        try:
            card = CardReference(
                name="Counterspell",
                set_code="3ED",
                collector_number="54",
                quantity=2
            )
            print(f"Adding {card.quantity}x {card.name}")
            print(f"From set {card.set_code}, number {card.collector_number}")
            
        except ValueError as e:
            print(f"Invalid card reference: {e}")
            
        # This will raise ValueError (invalid set code)
        try:
            invalid_card = CardReference(
                name="Island",
                set_code="INVALID",  # Must be exactly 3 characters
                collector_number="1",
                quantity=4
            )
        except ValueError as e:
            print(f"Validation error: {e}")
        ```
    """
    name: str
    set_code: str
    collector_number: str
    quantity: int

    def __post_init__(self):
        """Validate the card reference data after initialization.
        
        This method performs validation on all fields to ensure they meet
        the required format and constraints. It raises ValueError with a
        descriptive message if any validation fails.

        Raises:
            ValueError: If any field fails validation
        """
        if not self.name:
            raise ValueError("Card name cannot be empty")
        if not self.set_code or len(self.set_code) != 3:
            raise ValueError("Set code must be exactly 3 characters")
        if not self.collector_number:
            raise ValueError("Collector number cannot be empty")
        if self.quantity < 1:
            raise ValueError("Quantity must be positive")


@dataclass
class DeckListStats:
    """Statistics for deck list processing operations.
    
    This class tracks statistics about deck list processing, including
    success rates and missing cards. It provides insights into the
    completeness and accuracy of deck list processing.

    Attributes:
        cards_found (int): Number of cards successfully found in archive
        cards_missing (int): Number of cards not found in archive
        total_cards (int): Total number of unique cards in deck list

    Example:
        ```python
        stats = DeckListStats()
        
        # Process deck list
        for card in deck_list:
            stats.total_cards += 1
            if find_card(card):
                stats.cards_found += 1
            else:
                stats.cards_missing += 1
                
        # Report results
        print(f"Found {stats.cards_found} of {stats.total_cards} cards")
        print(f"Missing: {stats.cards_missing}")
        print(f"Success rate: {stats.success_rate:.1f}%")
        
        # Check if we found everything
        if stats.success_rate == 100.0:
            print("All cards found!")
        else:
            print("Some cards are missing")
        ```
    """
    cards_found: int = 0
    cards_missing: int = 0
    total_cards: int = 0

    @property
    def success_rate(self) -> float:
        """Calculate the percentage of cards successfully found.
        
        This property calculates the success rate as a percentage of cards
        found versus total cards. It handles the case of zero total cards
        gracefully.

        Returns:
            float: Percentage of cards found (0-100)

        Example:
            ```python
            stats = DeckListStats(
                cards_found=45,
                cards_missing=5,
                total_cards=50
            )
            print(f"Success rate: {stats.success_rate:.1f}%")  # "90.0%"
            ```
        """
        if self.total_cards == 0:
            return 0.0
        return (self.cards_found / self.total_cards) * 100
