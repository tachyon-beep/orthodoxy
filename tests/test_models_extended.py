"""Extended tests for models module to improve coverage."""

import pytest
from src.utils.models import CardReference, DeckListStats, WriterState, WriterStats

def test_card_reference_validation():
    """Test CardReference validation rules."""
    # Valid card reference
    card = CardReference(
        name="Test Card",
        set_code="ABC",
        collector_number="123",
        quantity=1
    )
    assert card.name == "Test Card"
    assert card.set_code == "ABC"
    
    # Test empty name validation
    with pytest.raises(ValueError, match="Card name cannot be empty"):
        CardReference(
            name="",
            set_code="ABC",
            collector_number="123",
            quantity=1
        )
    
    # Test invalid set code length
    with pytest.raises(ValueError, match="Set code must be exactly 3 characters"):
        CardReference(
            name="Test Card",
            set_code="AB",  # Too short
            collector_number="123",
            quantity=1
        )
    
    with pytest.raises(ValueError, match="Set code must be exactly 3 characters"):
        CardReference(
            name="Test Card",
            set_code="ABCD",  # Too long
            collector_number="123",
            quantity=1
        )
    
    # Test empty collector number
    with pytest.raises(ValueError, match="Collector number cannot be empty"):
        CardReference(
            name="Test Card",
            set_code="ABC",
            collector_number="",
            quantity=1
        )
    
    # Test invalid quantity
    with pytest.raises(ValueError, match="Quantity must be positive"):
        CardReference(
            name="Test Card",
            set_code="ABC",
            collector_number="123",
            quantity=0
        )
    
    with pytest.raises(ValueError, match="Quantity must be positive"):
        CardReference(
            name="Test Card",
            set_code="ABC",
            collector_number="123",
            quantity=-1
        )

def test_deck_list_stats_success_rate():
    """Test DeckListStats success rate calculation."""
    # Test with zero total cards
    stats = DeckListStats()
    assert stats.success_rate == 0.0
    
    # Test with some cards found
    stats = DeckListStats(cards_found=7, cards_missing=3, total_cards=10)
    assert stats.success_rate == 70.0
    
    # Test with all cards found
    stats = DeckListStats(cards_found=10, cards_missing=0, total_cards=10)
    assert stats.success_rate == 100.0
    
    # Test with no cards found
    stats = DeckListStats(cards_found=0, cards_missing=10, total_cards=10)
    assert stats.success_rate == 0.0

def test_writer_state_transitions():
    """Test WriterState enum values and transitions."""
    # Test initial state
    state = WriterState.INITIAL
    assert state != WriterState.SET_OPEN
    assert state != WriterState.SET_CLOSED
    
    # Test state transitions
    state = WriterState.SET_OPEN
    assert state != WriterState.INITIAL
    assert state != WriterState.SET_CLOSED
    
    state = WriterState.SET_CLOSED
    assert state != WriterState.INITIAL
    assert state != WriterState.SET_OPEN

def test_writer_stats_initialization():
    """Test WriterStats initialization and updates."""
    # Test default initialization
    stats = WriterStats()
    assert stats.cards_written == 0
    assert stats.sets_processed == 0
    assert stats.errors_encountered == 0
    
    # Test custom initialization
    stats = WriterStats(
        cards_written=10,
        sets_processed=2,
        errors_encountered=1
    )
    assert stats.cards_written == 10
    assert stats.sets_processed == 2
    assert stats.errors_encountered == 1
    
    # Test attribute updates
    stats.cards_written += 5
    stats.sets_processed += 1
    stats.errors_encountered += 2
    assert stats.cards_written == 15
    assert stats.sets_processed == 3
    assert stats.errors_encountered == 3
