"""Tests for the card matcher functionality."""

import pytest
from unittest.mock import Mock
from src.analysis.card_resolver import CardMatcher
from src.utils.models import CardReference


@pytest.fixture
def logger():
    """Create a mock logger for testing."""
    return Mock()


@pytest.fixture
def matcher(logger):
    """Create a CardMatcher instance for testing."""
    return CardMatcher(logger)


@pytest.fixture
def archive_data():
    """Create sample archive data for testing."""
    return {
        "data": {
            "SET1": {
                "cards": [
                    {"name": "Test Card", "number": "123"},
                    {"name": "Test Card // Side B", "number": "124"},
                ]
            },
            "SET2": {
                "cards": [
                    {"name": "Another Card", "number": "001"},
                    {"name": "Test Card", "number": "002"},
                ]
            }
        }
    }


def test_matches_card_name(matcher):
    """Test the _matches_card_name method."""
    # Test exact match
    assert matcher._matches_card_name("Test Card", "Test Card")
    
    # Test double-faced card match
    assert matcher._matches_card_name("Test Card // Side B", "Test Card")
    
    # Test non-match
    assert not matcher._matches_card_name("Different Card", "Test Card")


def test_get_cards_from_set(matcher):
    """Test the _get_cards_from_set method."""
    # Test with valid cards list
    set_data = {"cards": [{"name": "Card 1"}, {"name": "Card 2"}]}
    assert len(matcher._get_cards_from_set(set_data)) == 2
    
    # Test with empty cards list
    set_data = {"cards": []}
    assert len(matcher._get_cards_from_set(set_data)) == 0
    
    # Test with missing cards key
    set_data = {}
    assert len(matcher._get_cards_from_set(set_data)) == 0


def test_find_exact_match(matcher, archive_data):
    """Test the _find_exact_match method."""
    set_data = archive_data["data"]["SET1"]
    
    # Test finding exact match
    card_ref = CardReference(
        name="Test Card",
        set_code="SET",
        collector_number="123",
        quantity=1
    )
    match = matcher._find_exact_match(card_ref, set_data)
    assert match is not None
    assert match["name"] == "Test Card"
    assert match["number"] == "123"
    
    # Test finding double-faced card
    card_ref = CardReference(
        name="Test Card",
        set_code="SET",
        collector_number="124",
        quantity=1
    )
    match = matcher._find_exact_match(card_ref, set_data)
    assert match is not None
    assert match["name"] == "Test Card // Side B"
    
    # Test no match found
    card_ref = CardReference(
        name="Missing Card",
        set_code="SET",
        collector_number="999",
        quantity=1
    )
    match = matcher._find_exact_match(card_ref, set_data)
    assert match is None


def test_find_fallback_match(matcher, archive_data):
    """Test the _find_fallback_match method."""
    # Test finding fallback match in different set
    card_ref = CardReference(
        name="Test Card",
        set_code="SET",
        collector_number="999",
        quantity=1
    )
    match = matcher._find_fallback_match(card_ref, archive_data)
    assert match is not None
    assert match["name"] == "Test Card"
    
    # Test no fallback match found
    card_ref = CardReference(
        name="Missing Card",
        set_code="SET",
        collector_number="999",
        quantity=1
    )
    match = matcher._find_fallback_match(card_ref, archive_data)
    assert match is None


def test_find_card(matcher, archive_data):
    """Test the find_card method."""
    # Test exact match found
    card_ref = CardReference(
        name="Test Card",
        set_code="SET",
        collector_number="123",
        quantity=1
    )
    match = matcher.find_card(card_ref, archive_data)
    assert match is not None
    assert match["name"] == "Test Card"
    assert match["number"] == "123"
    
    # Test fallback match found
    card_ref = CardReference(
        name="Test Card",
        set_code="SET",
        collector_number="999",
        quantity=1
    )
    match = matcher.find_card(card_ref, archive_data)
    assert match is not None
    assert match["name"] == "Test Card"
    
    # Test no match found
    card_ref = CardReference(
        name="Missing Card",
        set_code="SET",
        collector_number="999",
        quantity=1
    )
    match = matcher.find_card(card_ref, archive_data)
    assert match is None
    
    # Test invalid archive data
    invalid_archive = {}
    match = matcher.find_card(card_ref, invalid_archive)
    assert match is None
    matcher.logger.warning.assert_called_once_with("Archive missing 'data' section")


def test_find_card_with_debug(matcher, archive_data):
    """Test the find_card method with debug logging enabled."""
    card_ref = CardReference(
        name="Test Card",
        set_code="SET",
        collector_number="123",
        quantity=1
    )
    match = matcher.find_card(card_ref, archive_data, debug=True)
    
    assert match is not None
    matcher.logger.debug.assert_called_once()
