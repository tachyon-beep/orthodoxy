"""Tests for deck list parsing functionality."""

import pytest
from unittest.mock import Mock
from io import StringIO

from src.utils.models import CardReference
from src.io.parsers.deck import (
    DeckListParser,
    DeckParserError,
    InvalidDeckFormatError,
    EmptyDeckError
)
from src.utils.interfaces import LoggingInterface


@pytest.fixture
def mock_logger() -> LoggingInterface:
    """Create a mock logger implementing the LoggingInterface protocol."""
    logger = Mock()
    logger.error = Mock()
    logger.warning = Mock()
    logger.info = Mock()
    logger.debug = Mock()
    return logger


@pytest.fixture
def parser(mock_logger) -> DeckListParser:
    """Create a DeckListParser instance with mock logger."""
    return DeckListParser(mock_logger)


def test_parse_valid_line(parser):
    """Test parsing a valid deck list line."""
    line = "2 Lightning Bolt (LEA) 168"
    result = parser.parse_line(line)
    
    assert isinstance(result, CardReference)
    assert result.name == "Lightning Bolt"
    assert result.set_code == "LEA"
    assert result.collector_number == "168"
    assert result.quantity == 2


def test_parse_double_faced_card(parser):
    """Test parsing a line with a double-faced card name.
    The parser should treat it as a normal card name, as the double-face handling
    is done by the extractor."""
    line = "4 Lodestone Needle (LCI) 62"
    result = parser.parse_line(line)
    
    assert isinstance(result, CardReference)
    assert result.name == "Lodestone Needle"  # Just the front face
    assert result.set_code == "LCI"
    assert result.collector_number == "62"
    assert result.quantity == 4


def test_parse_card_with_special_characters(parser):
    """Test parsing a line with a card name containing special characters."""
    line = "2 Fire // Ice (APC) 128"
    result = parser.parse_line(line)
    
    assert isinstance(result, CardReference)
    assert result.name == "Fire // Ice"  # Should preserve special characters
    assert result.set_code == "APC"
    assert result.collector_number == "128"
    assert result.quantity == 2


def test_parse_invalid_line(parser):
    """Test parsing an invalid deck list line."""
    line = "Invalid Card Entry"
    with pytest.raises(InvalidDeckFormatError) as exc_info:
        parser.parse_line(line)
    assert "Invalid line format" in str(exc_info.value)


def test_parse_empty_line(parser):
    """Test parsing an empty line."""
    with pytest.raises(InvalidDeckFormatError) as exc_info:
        parser.parse_line("")
    assert "Empty line" in str(exc_info.value)


def test_parse_section_header(parser):
    """Test handling section headers in deck list."""
    line = "Sideboard:"
    with pytest.raises(InvalidDeckFormatError) as exc_info:
        parser.parse_line(line)
    assert "Section header" in str(exc_info.value)


def test_parse_deck_list_file(parser):
    """Test parsing a complete deck list from a file-like object."""
    deck_content = """
    # Main Deck
    4 Lightning Bolt (LEA) 168
    3 Dark Ritual (LEA) 98
    2 Fire // Ice (APC) 128
    4 Lodestone Needle (LCI) 62
    
    # Sideboard
    2 Disenchant (LEA) 25
    """
    
    deck_file = StringIO(deck_content)
    results = parser.parse_deck_list_file(deck_file)
    
    assert len(results) == 5
    assert all(isinstance(card, CardReference) for card in results)
    
    # Check specific cards
    assert any(
        card.name == "Lightning Bolt" and card.quantity == 4
        for card in results
    )
    assert any(
        card.name == "Dark Ritual" and card.quantity == 3
        for card in results
    )
    assert any(
        card.name == "Fire // Ice" and card.quantity == 2
        for card in results
    )
    assert any(
        card.name == "Lodestone Needle" and card.quantity == 4
        for card in results
    )
    assert any(
        card.name == "Disenchant" and card.quantity == 2
        for card in results
    )


def test_parse_empty_deck_list(parser):
    """Test parsing an empty deck list."""
    deck_file = StringIO("")
    with pytest.raises(EmptyDeckError):
        parser.parse_deck_list_file(deck_file)


def test_parse_deck_list_with_invalid_lines(parser, mock_logger):
    """Test parsing deck list with mix of valid and invalid lines."""
    deck_content = """
    Invalid Line
    4 Lightning Bolt (LEA) 168
    Also Invalid
    3 Dark Ritual (LEA) 98
    """
    
    deck_file = StringIO(deck_content)
    results = parser.parse_deck_list_file(deck_file)
    
    # Should get two valid cards
    assert len(results) == 2
    
    # Should log warnings for invalid lines
    assert mock_logger.warning.call_count == 2


def test_parse_deck_list_file_not_found(parser):
    """Test handling non-existent deck list file."""
    with pytest.raises(FileNotFoundError):
        parser.parse_deck_list("nonexistent_file.txt")


def test_parse_deck_list_with_comments(parser):
    """Test parsing deck list with comments and empty lines."""
    deck_content = """
    # Main Deck
    
    4 Lightning Bolt (LEA) 168
    
    # Creatures
    3 Shivan Dragon (LEA) 170
    
    # Sideboard
    2 Disenchant (LEA) 25
    """
    
    deck_file = StringIO(deck_content)
    results = parser.parse_deck_list_file(deck_file)
    
    assert len(results) == 3
    assert not any(card.name.startswith('#') for card in results)


def test_parse_line_with_extra_whitespace(parser):
    """Test parsing line with extra whitespace."""
    line = "  4   Lightning Bolt   (LEA)   168  "
    result = parser.parse_line(line)
    
    assert result.name == "Lightning Bolt"
    assert result.quantity == 4


def test_parse_invalid_quantity(parser):
    """Test parsing line with invalid quantity."""
    line = "invalid Lightning Bolt (LEA) 168"
    with pytest.raises(InvalidDeckFormatError):
        parser.parse_line(line)


def test_error_propagation(parser):
    """Test that errors are properly propagated and logged."""
    try:
        parser.parse_line("Invalid Line")
    except DeckParserError as e:
        assert isinstance(e, InvalidDeckFormatError)
        assert "Invalid line format" in str(e)


def test_parse_card_with_spaces_in_name(parser):
    """Test parsing a line with a card name containing multiple spaces."""
    line = "2 Nicol Bolas, the Ravager (M19) 218"
    result = parser.parse_line(line)
    
    assert isinstance(result, CardReference)
    assert result.name == "Nicol Bolas, the Ravager"
    assert result.set_code == "M19"
    assert result.collector_number == "218"
    assert result.quantity == 2
