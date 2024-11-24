"""Tests for the CardSetWriter class functionality.

This module contains tests for the CardSetWriter class, which handles writing
processed cards to output files.
"""

import pytest
from src.io.writers.card import CardSetWriter
from src.utils.models import WriterState


@pytest.fixture
def writer(config, mock_file) -> CardSetWriter:
    """Provides a CardSetWriter instance for testing.

    Args:
        config: The CardFilterConfig fixture.
        mock_file: The mock file fixture.

    Returns:
        A new CardSetWriter instance.
    """
    return CardSetWriter(mock_file, config)


def test_initial_state(writer: CardSetWriter):
    """Tests the initial state of the writer."""
    assert writer._state == WriterState.INITIAL
    assert writer._is_first_card is True
    assert writer.stats.cards_written == 0
    assert len(writer.buffer) == 0


def test_handle_set_transition(writer: CardSetWriter):
    """Tests handling a set transition."""
    writer.handle_set_transition("test_set")
    assert writer.current_set == "test_set"
    assert writer._state == WriterState.SET_OPEN
    assert writer.stats.sets_processed == 1
    assert writer.first_set_written is True


def test_write_processed_card(writer: CardSetWriter):
    """Tests writing a processed card."""
    writer.handle_set_transition("test_set")
    test_card = {"name": "Test Card", "type": "Creature"}
    writer.write_processed_card(test_card)
    assert writer.stats.cards_written == 1
    assert len(writer.buffer) == 1


def test_buffer_handling(writer: CardSetWriter):
    """Tests buffer handling when writing multiple cards."""
    writer.handle_set_transition("test_set")
    writer.buffer_size = 2

    # Write first card
    card1 = {"name": "Card 1", "type": "Creature"}
    writer.write_processed_card(card1)
    assert len(writer.buffer) == 1

    # Write second card - should trigger buffer flush
    card2 = {"name": "Card 2", "type": "Creature"}
    writer.write_processed_card(card2)
    assert len(writer.buffer) == 0


def test_invalid_card_validation(writer: CardSetWriter):
    """Tests validation of invalid card data."""
    writer.handle_set_transition("test_set")
    invalid_card = ["not a dict"]
    with pytest.raises(ValueError, match="Expected dict, got <class 'list'>"):
        writer.write_processed_card(invalid_card)  # type: ignore


def test_missing_required_fields(writer: CardSetWriter):
    """Tests validation of cards with missing required fields."""
    writer.handle_set_transition("test_set")
    invalid_card = {"name": "Test Card"}  # missing type field
    with pytest.raises(ValueError, match="Missing required fields: {'type'}"):
        writer.write_processed_card(invalid_card)


def test_error_handling_with_card_name(writer: CardSetWriter):
    """Tests error handling with card name in error message."""
    writer.handle_set_transition("test_set")
    invalid_card = {"name": "Problem Card"}
    with pytest.raises(ValueError, match="Error writing card Problem Card:"):
        writer.write_processed_card(invalid_card)
