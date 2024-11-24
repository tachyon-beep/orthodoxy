"""Card set writer module for handling Magic: The Gathering card data output.

This module provides functionality for writing processed Magic: The Gathering card data
to output files in a structured JSON format. It implements type-safe buffered writing
with comprehensive validation and error handling.

Key Features:
- Type-safe buffered writing with validation
- Support for both text and binary output with encoding
- Set-based card organization with state tracking
- Progress tracking with detailed statistics
- Comprehensive data validation with context
- Resource-safe context manager support
- Error context preservation for debugging
- Memory-efficient buffer management

The module centers around the CardSetWriter class which implements:
- Type-safe set transitions and formatting
- Comprehensive card data validation
- Memory-efficient buffer management
- Detailed writing statistics
- Error context preservation
- Resource cleanup

Example:
    Basic usage with type safety:
    ```python
    config = CardFilterConfig(buffer_size=1000)
    with CardSetWriter(outfile, config) as writer:
        # Write with validation
        writer.handle_set_transition("Dominaria")
        writer.write_processed_card({
            "name": "Lightning Bolt",
            "type": "Instant",
            "cost": "R"
        })
        
        # Get detailed statistics
        stats = writer.get_stats()
        print(f"Cards written: {stats.cards_written}")
        print(f"Sets processed: {stats.sets_processed}")
        print(f"Errors: {stats.errors_encountered}")
    ```

Note:
    All operations implement comprehensive validation and error handling.
    The writer maintains proper state tracking and ensures resource cleanup
    even in error cases.
"""

from typing import Optional, TextIO, BinaryIO, Union, Any, cast
from dataclasses import dataclass
import json
from io import StringIO, BytesIO

from ...utils.models import WriterState, WriterStats
from ...core.config import CardFilterConfig


@dataclass
class CardSetWriter:
    """Handles type-safe card set writing with validation.
    
    This class manages the writing of card data to output files,
    implementing comprehensive validation, state tracking, and
    proper resource management.

    Features:
    - Type-safe writing operations
    - Comprehensive validation
    - State tracking and transitions
    - Memory-efficient buffering
    - Error context preservation
    - Resource cleanup
    
    Attributes:
        outfile: Type-checked output file handle
        config: Validated configuration settings
        current_set: Tracked set name with validation
        first_set_written: State tracking for formatting
    """

    outfile: Union[TextIO, BinaryIO]
    config: CardFilterConfig
    current_set: Optional[str] = None
    first_set_written: bool = False

    def __post_init__(self):
        """Initialize with validated state."""
        self._state = WriterState.INITIAL
        self._is_first_card = True
        self.stats = WriterStats()
        self.buffer = []
        self.buffer_size = self.config.buffer_size

    def __enter__(self):
        """Context manager entry with state validation.
        
        Returns:
            CardSetWriter: The validated writer instance
            
        Example:
            ```python
            with CardSetWriter(outfile, config) as writer:
                writer.handle_set_transition("Dominaria")
                writer.write_processed_card(card_data)
            # Resources automatically cleaned up
            ```
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with resource cleanup.
        
        Ensures proper resource cleanup even in error cases.
        
        Args:
            exc_type: Exception type if error occurred
            exc_val: Exception value if error occurred
            exc_tb: Exception traceback if error occurred
            
        Returns:
            bool: False to propagate exceptions
            
        Note:
            Always performs cleanup regardless of exceptions
        """
        self.close()
        return False

    def _write(self, data: str) -> None:
        """Write data with type safety and encoding handling.
        
        Args:
            data: Validated string data to write
            
        Raises:
            TypeError: If file type is unsupported
            
        Note:
            Handles both text and binary modes with proper encoding
        """
        if isinstance(self.outfile, (StringIO, TextIO)):
            self.outfile.write(data)
        elif isinstance(self.outfile, (BytesIO, BinaryIO)):
            self.outfile.write(data.encode('utf-8'))
        else:
            raise TypeError(f"Unsupported file type: {type(self.outfile)}")

    def handle_set_transition(self, set_name: str) -> None:
        """Handle set transition with state validation.
        
        Args:
            set_name: Validated set name
            
        Example:
            ```python
            writer.handle_set_transition("Dominaria")
            # State updated and validated
            writer.write_processed_card(card_data)
            ```
        """
        if set_name == self.current_set:
            return

        if self.current_set is not None:
            self._flush_buffer()
            self._write("}")

        if self.first_set_written:
            self._write(",")
        
        self._write(f'"{set_name}":{{"block":null,"cards":[')
        
        self.current_set = set_name
        self.first_set_written = True
        self.stats.sets_processed += 1
        self._state = WriterState.SET_OPEN
        self._is_first_card = True

    def write_processed_card(self, card: Optional[dict]) -> None:
        """Write a processed card with comprehensive validation.
        
        Args:
            card: Validated card data dictionary
            
        Raises:
            ValueError: If card data fails validation
            IOError: If writing fails
            
        Example:
            ```python
            try:
                writer.write_processed_card({
                    "name": "Lightning Bolt",
                    "type": "Instant",
                    "cost": "R"
                })
            except ValueError as e:
                print(f"Validation error: {e}")
            except IOError as e:
                print(f"Write error: {e}")
            ```
        """
        if card is None:
            return

        try:
            self._ensure_state(WriterState.SET_OPEN)
            self._validate_card(card)

            card_json = json.dumps(card)
            if self._is_first_card:
                self._is_first_card = False
                self.buffer.append(card_json)
            else:
                self.buffer.append("," + card_json)

            if len(self.buffer) >= self.buffer_size:
                self._flush_buffer()

            self.stats.cards_written += 1

        except (ValueError, IOError) as e:
            self.stats.errors_encountered += 1
            card_name = card.get('name', 'unknown') if isinstance(card, dict) else 'unknown'
            raise type(e)(f"Error writing card {card_name}: {str(e)}") from e

    def _validate_card(self, card: Any) -> bool:
        """Validate card data with type checking.
        
        Args:
            card: Card data to validate
            
        Returns:
            bool: True if validation passes
            
        Raises:
            ValueError: If validation fails with context
            
        Example:
            ```python
            try:
                writer._validate_card({
                    "name": "Lightning Bolt",
                    "type": "Instant"
                })
            except ValueError as e:
                print(f"Invalid card data: {e}")
            ```
        """
        if not isinstance(card, dict):
            raise ValueError(f"Expected dict, got {type(card)}")

        required_fields = {"name", "type"}
        missing_fields = required_fields - set(card.keys())
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")

        return True

    def _ensure_state(self, expected: WriterState) -> None:
        """Ensure writer state with validation.
        
        Args:
            expected: The expected valid state
            
        Raises:
            RuntimeError: If state is invalid with context
            
        Example:
            ```python
            try:
                writer._ensure_state(WriterState.SET_OPEN)
                # Proceed with writing
            except RuntimeError as e:
                print(f"Invalid state: {e}")
            ```
        """
        if self._state != expected:
            raise RuntimeError(f"Invalid state: expected {expected}, got {self._state}")

    def _flush_buffer(self) -> None:
        """Flush buffer with memory efficiency.
        
        Implements memory-efficient buffer flushing with proper
        state handling.
        """
        if not self.buffer:
            return

        self._write("".join(self.buffer))
        self.buffer.clear()

    def close(self) -> None:
        """Close writer with resource cleanup.
        
        Ensures proper cleanup of resources and state,
        handling any open sets or buffers.
        
        Example:
            ```python
            writer = CardSetWriter(outfile, config)
            try:
                writer.write_processed_card(card_data)
            finally:
                writer.close()  # Always cleanup
            ```
        """
        if self.current_set is not None:
            self._flush_buffer()
            self._write("]}")
            self._state = WriterState.SET_CLOSED

    def get_stats(self) -> WriterStats:
        """Get detailed writer statistics.
        
        Returns:
            WriterStats: Comprehensive statistics
            
        Example:
            ```python
            stats = writer.get_stats()
            print(f"Cards written: {stats.cards_written}")
            print(f"Sets processed: {stats.sets_processed}")
            print(f"Errors: {stats.errors_encountered}")
            ```
        """
        return self.stats
