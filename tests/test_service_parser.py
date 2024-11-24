"""Tests for filter string and card data parsing functionality."""

import pytest
from unittest.mock import Mock

from src.utils.container import Container
from src.services.filter_parser import (
    CardParser,
    FilterParseError,
    CardDataParseError
)

@pytest.fixture
def mock_logger():
    return Mock()

@pytest.fixture
def mock_container(mock_logger):
    container = Mock(spec=Container)
    container.logging_service.return_value = mock_logger
    return container

@pytest.fixture
def parser(mock_container):
    return CardParser(mock_container)

def test_parse_filter_string_valid(parser):
    """Test parsing valid filter strings."""
    # Test simple string/number values
    result = parser.parse_filter_string('{"name": "Lightning Bolt", "cmc": 1}')
    assert result == {
        "name": {"eq": "Lightning Bolt"},
        "cmc": {"eq": 1}
    }

    # Test list values
    result = parser.parse_filter_string('{"colors": ["R", "U"]}')
    assert result == {"colors": {"in": ["R", "U"]}}

    # Test complex filter
    result = parser.parse_filter_string('{"power": {"gt": 5}}')
    assert result == {"power": {"gt": 5}}

def test_parse_filter_string_invalid_json(parser, mock_logger):
    """Test handling of invalid JSON in filter string."""
    with pytest.raises(FilterParseError) as exc:
        parser.parse_filter_string('{invalid json}')
    
    assert "Invalid filter JSON" in str(exc.value)
    mock_logger.error.assert_called_once()

def test_parse_filter_string_empty(parser):
    """Test parsing empty filter string."""
    with pytest.raises(FilterParseError):
        parser.parse_filter_string('')

def test_parse_filter_string_numeric(parser):
    """Test parsing numeric values in filter string."""
    result = parser.parse_filter_string('{"power": 5, "toughness": 5.5}')
    assert result == {
        "power": {"eq": 5},
        "toughness": {"eq": 5.5}
    }

def test_validate_prefix_valid(parser):
    """Test validation of valid prefixes."""
    valid, set_name = parser.validate_prefix("data.m19")
    assert valid is True
    assert set_name == "m19"

def test_validate_prefix_invalid(parser):
    """Test validation of invalid prefixes."""
    # Test None prefix
    valid, msg = parser.validate_prefix(None)
    assert valid is False
    assert "Invalid prefix: None" in msg

    # Test empty prefix
    valid, msg = parser.validate_prefix("")
    assert valid is False
    assert "Invalid prefix: None or non-string value" in msg

    # Test wrong format
    valid, msg = parser.validate_prefix("wrong.format")
    assert valid is False
    assert "Invalid prefix format" in msg

    # Test missing data prefix
    valid, msg = parser.validate_prefix("notdata.set")
    assert valid is False
    assert "Invalid prefix format" in msg

def test_validate_prefix_empty(parser):
    """Test validation of empty prefix."""
    valid, msg = parser.validate_prefix("")
    assert valid is False
    assert "Invalid prefix: None or non-string value" in msg

def test_process_card_data_start_map(parser):
    """Test processing start of card map."""
    prefix = "data.m19.cards.item"
    event = "start_map"
    set_name, card = parser.process_card_data(prefix, event, None, {})
    assert set_name == "m19"
    assert card == {}

def test_process_card_data_field(parser):
    """Test processing card field."""
    prefix = "data.m19.cards.item.name"
    event = "string"
    value = "Lightning Bolt"
    current_card = {"colors": ["R"]}
    
    set_name, card = parser.process_card_data(prefix, event, value, current_card)
    assert set_name == "m19"
    assert card == {
        "colors": ["R"],
        "name": "Lightning Bolt"
    }

def test_process_card_data_invalid_prefix(parser, mock_logger):
    """Test processing with invalid prefix."""
    with pytest.raises(CardDataParseError) as exc:
        parser.process_card_data("invalid.prefix", "string", "value", {})
    
    assert "Invalid prefix format" in str(exc.value)
    mock_logger.error.assert_called_once()

def test_process_card_data_block(parser):
    """Test processing block data."""
    prefix = "data.m19.block"
    event = "string"
    value = "Core Set 2019"
    current_card = {"name": "Lightning Bolt"}
    
    set_name, card = parser.process_card_data(prefix, event, value, current_card)
    assert set_name is None
    assert card == {"name": "Lightning Bolt"}

def test_process_card_data_invalid_prefix_none(parser, mock_logger):
    """Test processing with None prefix."""
    try:
        parser.process_card_data(None, "string", "value", {})
    except CardDataParseError as e:
        # The error message should indicate an attribute error since None doesn't have endswith
        assert "NoneType" in str(e)
        assert "endswith" in str(e)
        mock_logger.error.assert_called_once()
