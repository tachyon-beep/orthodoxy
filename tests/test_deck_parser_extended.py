"""Extended tests for deck parser module to improve coverage."""

import pytest
from unittest.mock import MagicMock, mock_open, patch
from src.io.parsers.deck import (
    DeckListParser,
    DeckParserError,
    InvalidDeckFormatError,
    EmptyDeckError
)
from src.utils.interfaces import LoggingInterface
from io import StringIO

class MockLogger(LoggingInterface):
    def __init__(self):
        self.messages = []
    
    def error(self, message: str) -> None:
        self.messages.append(("ERROR", message))
    
    def warning(self, message: str) -> None:
        self.messages.append(("WARNING", message))
    
    def info(self, message: str) -> None:
        self.messages.append(("INFO", message))
    
    def debug(self, message: str) -> None:
        self.messages.append(("DEBUG", message))

def test_section_header_handling():
    """Test handling of section headers in deck list."""
    logger = MockLogger()
    parser = DeckListParser(logger)
    
    # Test section headers
    with pytest.raises(InvalidDeckFormatError, match="Section header 'Sideboard:' not supported in this format"):
        parser.parse_line("Sideboard:")
    
    with pytest.raises(InvalidDeckFormatError, match="Section header 'Mainboard:' not supported in this format"):
        parser.parse_line("Mainboard:")

def test_section_header_logging():
    """Test logging of section header errors."""
    logger = MockLogger()
    parser = DeckListParser(logger)
    
    try:
        parser.parse_line("Sideboard:")
    except InvalidDeckFormatError:
        pass
    
    assert any("Section header 'Sideboard:' not supported in this format" in msg[1] for msg in logger.messages)
    
    try:
        parser.parse_line("Mainboard:")
    except InvalidDeckFormatError:
        pass
    
    assert any("Section header 'Mainboard:' not supported in this format" in msg[1] for msg in logger.messages)

def test_parse_deck_list_error_handling():
    """Test error handling in parse_deck_list method."""
    logger = MockLogger()
    parser = DeckListParser(logger)
    
    # Test file not found
    with patch('builtins.open', side_effect=FileNotFoundError()):
        with pytest.raises(FileNotFoundError, match="Deck list file not found"):
            parser.parse_deck_list("nonexistent.txt")
        assert any("Deck list file not found" in msg[1] for msg in logger.messages)
    
    # Test empty deck file
    with patch('builtins.open', mock_open(read_data="")):
        with pytest.raises(ValueError, match="No valid card references found in deck list"):
            parser.parse_deck_list("empty.txt")
        assert any("No valid card references found" in msg[1] for msg in logger.messages)
    
    # Test file with only invalid entries
    invalid_content = "Invalid Entry\nAlso Invalid\n"
    with patch('builtins.open', mock_open(read_data=invalid_content)):
        with pytest.raises(ValueError, match="No valid card references found in deck list"):
            parser.parse_deck_list("invalid.txt")
        assert any("No valid card references found" in msg[1] for msg in logger.messages)
    
    # Test file with read error
    with patch('builtins.open', side_effect=Exception("Read error")):
        with pytest.raises(DeckParserError, match="Error reading deck list"):
            parser.parse_deck_list("error.txt")
        assert any("Error reading deck list" in msg[1] for msg in logger.messages)

def test_parse_deck_list_file_edge_cases():
    """Test edge cases in parse_deck_list_file method."""
    logger = MockLogger()
    parser = DeckListParser(logger)
    
    # Test with only whitespace lines
    deck_file = StringIO("\n   \n  \n")
    with pytest.raises(EmptyDeckError):
        parser.parse_deck_list_file(deck_file)
    
    # Test with mixed whitespace and invalid lines
    deck_file = StringIO("\n   \nInvalid Line\n  \n")
    with pytest.raises(EmptyDeckError):
        parser.parse_deck_list_file(deck_file)
    
    # Test with valid and invalid lines, including edge cases
    deck_content = """
    4 Valid Card (SET) 123
    
    Invalid Line
    2 Card With Spaces (ABC) 456
    1 Card-With-Dashes (XYZ) 789
    Not a card
    3 Card.With.Dots (DEF) 101112
    """
    
    deck_file = StringIO(deck_content)
    card_refs = parser.parse_deck_list_file(deck_file)
    
    # Verify valid cards were parsed
    assert len(card_refs) == 4
    assert card_refs[0].name == "Valid Card"
    assert card_refs[1].name == "Card With Spaces"
    assert card_refs[2].name == "Card-With-Dashes"
    assert card_refs[3].name == "Card.With.Dots"
    
    # Verify warnings for invalid lines
    warnings = [msg for msg in logger.messages if msg[0] == "WARNING"]
    assert len(warnings) == 3  # Three invalid lines: empty line, "Invalid Line", and "Not a card"

def test_parse_line_special_characters():
    """Test parsing lines with special characters."""
    logger = MockLogger()
    parser = DeckListParser(logger)
    
    # Test valid lines with special characters
    valid_cases = [
        "1 Æther Vial (DST) 91",
        "2 Jötun Grunt (CSP) 8",
        "3 Lim-Dûl's Vault (ALL) 51",
        "4 Márton Stromgald (ICE) 199",
        "1 Søg (POR) 43"
    ]
    
    for line in valid_cases:
        card_ref = parser.parse_line(line)
        assert card_ref is not None
        assert card_ref.quantity > 0
        assert len(card_ref.set_code) == 3
        assert len(card_ref.collector_number) > 0

def test_parse_line_invalid_formats():
    """Test parsing invalid line formats."""
    logger = MockLogger()
    parser = DeckListParser(logger)
    
    invalid_cases = [
        "",  # Empty line
        "Not a card entry",  # No quantity
        "1 Card",  # Missing set and collector number
        "1 Card (SET)",  # Missing collector number
        "1 Card 123",  # Missing set
        "Card (SET) 123",  # Missing quantity
        "-1 Card (SET) 123",  # Invalid quantity
        "1.5 Card (SET) 123",  # Non-integer quantity
        "1 Card (TOOLONG) 123",  # Set code too long
        "1 Card (ST) 123",  # Set code too short
    ]
    
    for line in invalid_cases:
        with pytest.raises(InvalidDeckFormatError):
            parser.parse_line(line)
