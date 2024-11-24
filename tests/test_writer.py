"""Tests for the card set writer module."""

import pytest
import json
from unittest.mock import Mock, patch
from io import StringIO, BytesIO
from typing import Union, BinaryIO, TextIO

from src.io.writers.card import CardSetWriter
from src.utils.models import WriterState, WriterStats
from src.core.config import CardFilterConfig

@pytest.fixture
def config():
    """Create a test configuration."""
    config = Mock(spec=CardFilterConfig)
    config.buffer_size = 2  # Small buffer for testing
    return config

@pytest.fixture
def text_output():
    """Create a StringIO buffer for text output testing."""
    return StringIO()

@pytest.fixture
def binary_output():
    """Create a BytesIO buffer for binary output testing."""
    return BytesIO()

class TestCardSetWriter:
    def test_initialization(self, config, text_output):
        """Test writer initialization."""
        writer = CardSetWriter(text_output, config)
        assert writer._state == WriterState.INITIAL
        assert writer._is_first_card is True
        assert isinstance(writer.stats, WriterStats)
        assert writer.buffer == []
        assert writer.buffer_size == config.buffer_size

    def test_context_manager(self, config, text_output):
        """Test writer as context manager."""
        with CardSetWriter(text_output, config) as writer:
            assert isinstance(writer, CardSetWriter)
        # Verify file is properly closed
        assert text_output.closed is False  # StringIO doesn't actually close

    def test_write_text_mode(self, config, text_output):
        """Test writing in text mode."""
        writer = CardSetWriter(text_output, config)
        writer._write("test")
        assert text_output.getvalue() == "test"

    def test_write_binary_mode(self, config, binary_output):
        """Test writing in binary mode."""
        writer = CardSetWriter(binary_output, config)
        writer._write("test")
        assert binary_output.getvalue() == b"test"

    def test_handle_set_transition_first_set(self, config, text_output):
        """Test handling first set transition."""
        writer = CardSetWriter(text_output, config)
        writer.handle_set_transition("test_set")
        
        assert writer.current_set == "test_set"
        assert writer.first_set_written is True
        assert writer._state == WriterState.SET_OPEN
        assert writer._is_first_card is True
        assert writer.stats.sets_processed == 1
        assert '"test_set":{"block":null,"cards":[' in text_output.getvalue()

    def test_handle_set_transition_multiple_sets(self, config, text_output):
        """Test handling multiple set transitions."""
        writer = CardSetWriter(text_output, config)
        
        # First set
        writer.handle_set_transition("set1")
        initial_output = text_output.getvalue()
        
        # Second set
        writer.handle_set_transition("set2")
        second_output = text_output.getvalue()
        
        assert writer.stats.sets_processed == 2
        assert '},"set2":{"block":null,"cards":[' in second_output
        assert second_output.startswith(initial_output)

    def test_handle_same_set_transition(self, config, text_output):
        """Test handling transition to same set."""
        writer = CardSetWriter(text_output, config)
        writer.handle_set_transition("test_set")
        initial_output = text_output.getvalue()
        
        writer.handle_set_transition("test_set")
        assert text_output.getvalue() == initial_output
        assert writer.stats.sets_processed == 1

    def test_write_processed_card_none(self, config, text_output):
        """Test writing None card."""
        writer = CardSetWriter(text_output, config)
        writer.handle_set_transition("test_set")
        writer.write_processed_card(None)
        assert writer.stats.cards_written == 0

    def test_write_processed_card_success(self, config, text_output):
        """Test successful card writing."""
        writer = CardSetWriter(text_output, config)
        writer.handle_set_transition("test_set")
        
        card = {"name": "Test Card", "type": "Creature"}
        writer.write_processed_card(card)
        
        assert writer.stats.cards_written == 1
        assert writer._is_first_card is False
        assert json.dumps(card) in writer.buffer

    def test_write_processed_card_invalid_state(self, config, text_output):
        """Test writing card in invalid state."""
        writer = CardSetWriter(text_output, config)
        card = {"name": "Test Card", "type": "Creature"}
        
        with pytest.raises(RuntimeError) as exc_info:
            writer.write_processed_card(card)
        assert "Invalid state" in str(exc_info.value)

    def test_write_processed_card_invalid_data(self, config, text_output):
        """Test writing invalid card data."""
        writer = CardSetWriter(text_output, config)
        writer.handle_set_transition("test_set")
        
        invalid_card = {"name": "Test Card"}  # Missing required 'type' field
        
        with pytest.raises(ValueError) as exc_info:
            writer.write_processed_card(invalid_card)
        assert "Missing required fields" in str(exc_info.value)
        assert writer.stats.errors_encountered == 1

    def test_buffer_flushing(self, config, text_output):
        """Test buffer flushing mechanism."""
        writer = CardSetWriter(text_output, config)
        writer.handle_set_transition("test_set")
        
        # Write enough cards to trigger buffer flush
        card1 = {"name": "Card 1", "type": "Creature"}
        card2 = {"name": "Card 2", "type": "Creature"}
        card3 = {"name": "Card 3", "type": "Creature"}
        
        writer.write_processed_card(card1)
        assert len(writer.buffer) == 1
        
        writer.write_processed_card(card2)
        assert len(writer.buffer) == 0  # Buffer should have flushed
        
        writer.write_processed_card(card3)
        assert len(writer.buffer) == 1

    def test_close_writer(self, config, text_output):
        """Test closing the writer."""
        writer = CardSetWriter(text_output, config)
        writer.handle_set_transition("test_set")
        writer.write_processed_card({"name": "Test Card", "type": "Creature"})
        
        writer.close()
        assert writer._state == WriterState.SET_CLOSED
        assert text_output.getvalue().endswith("]}")

    def test_get_stats(self, config, text_output):
        """Test getting writer statistics."""
        writer = CardSetWriter(text_output, config)
        writer.handle_set_transition("test_set")
        writer.write_processed_card({"name": "Test Card", "type": "Creature"})
        
        stats = writer.get_stats()
        assert isinstance(stats, WriterStats)
        assert stats.sets_processed == 1
        assert stats.cards_written == 1
        assert stats.errors_encountered == 0

    def test_validate_card(self, config, text_output):
        """Test card validation."""
        writer = CardSetWriter(text_output, config)
        
        # Test valid card
        valid_card = {"name": "Test Card", "type": "Creature"}
        assert writer._validate_card(valid_card) is True
        
        # Test invalid type
        with pytest.raises(ValueError) as exc_info:
            writer._validate_card([])  # Not a dict
        assert "Expected dict" in str(exc_info.value)
        
        # Test missing fields
        with pytest.raises(ValueError) as exc_info:
            writer._validate_card({"name": "Test Card"})  # Missing type
        assert "Missing required fields" in str(exc_info.value)
