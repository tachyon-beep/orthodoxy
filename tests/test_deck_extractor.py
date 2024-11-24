"""Tests for the DeckExtractorService class functionality."""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch
from src.analysis.decks import DeckExtractorService
from src.analysis.cards import CardProcessorInterface
from src.utils.models import DeckListStats
from src.core.config import CardFilterConfig


@pytest.fixture
def config() -> CardFilterConfig:
    """Provides a CardFilterConfig instance for testing."""
    return CardFilterConfig()


@pytest.fixture
def mock_logger():
    """Create a mock logger."""
    logger = Mock()
    logger.error = Mock()
    logger.warning = Mock()
    logger.info = Mock()
    logger.debug = Mock()
    return logger


@pytest.fixture
def card_processor(config) -> CardProcessorInterface:
    """Provides a CardProcessorInterface instance for testing."""
    return CardProcessorInterface(config)


@pytest.fixture
def deck_extractor(card_processor, mock_logger) -> DeckExtractorService:
    """Provides a DeckExtractorService instance for testing."""
    return DeckExtractorService(card_processor=card_processor, logger=mock_logger)


@pytest.fixture
def sample_archive(tmp_path) -> Path:
    """Creates a sample card archive file for testing."""
    archive_data = {
        "data": {
            "BLB": {
                "cards": [
                    {
                        "name": "Shoreline Looter",
                        "setCode": "BLB",
                        "number": "70",
                        "type": "Creature",
                        "text": "Sample text",
                        "colors": ["U"],
                        "colorIdentity": ["U"]
                    }
                ]
            },
            "ONE": {
                "cards": [
                    {
                        "name": "Elesh Norn, Mother of Machines",
                        "setCode": "ONE",
                        "number": "10",
                        "type": "Legendary Creature",
                        "text": "Sample text",
                        "colors": ["W"],
                        "colorIdentity": ["W"]
                    }
                ]
            },
            "LCI": {
                "cards": [
                    {
                        "name": "Lodestone Needle // Guidestone Compass",
                        "setCode": "LCI",
                        "number": "62",
                        "type": "Artifact // Artifact",
                        "text": "Sample text",
                        "colors": [],
                        "colorIdentity": []
                    },
                    {
                        "name": "Waterlogged Hulk // Watertight Gondola",
                        "setCode": "LCI",
                        "number": "83",
                        "type": "Artifact // Artifact Vehicle",
                        "text": "Sample text",
                        "colors": [],
                        "colorIdentity": []
                    }
                ]
            },
            "FDN": {
                "cards": [
                    {
                        "name": "Temple of Deceit",
                        "setCode": "FDN",
                        "number": "697",
                        "type": "Land",
                        "text": "Sample text",
                        "colors": [],
                        "colorIdentity": ["U", "B"]
                    }
                ]
            }
        }
    }
    
    archive_file = tmp_path / "cards.json"
    archive_file.write_text(json.dumps(archive_data))
    return archive_file


@pytest.fixture
def sample_decklist(tmp_path) -> Path:
    """Creates a sample deck list file for testing."""
    decklist = """
Deck
4 Shoreline Looter (BLB) 70
2 Elesh Norn, Mother of Machines (ONE) 10
4 Lodestone Needle (LCI) 62
2 Waterlogged Hulk (LCI) 83
1 Temple of Deceit (THB) 245
1 Missing Card (XXX) 99
    """
    decklist_file = tmp_path / "deck.txt"
    decklist_file.write_text(decklist)
    return decklist_file


@pytest.fixture
def sample_schema(tmp_path) -> Path:
    """Creates a sample schema file for testing."""
    schema_data = {
        "properties": {
            "data": {
                "patternProperties": {
                    ".*": {
                        "properties": {
                            "cards": {
                                "items": {
                                    "required": ["name", "type", "colors"]
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    schema_file = tmp_path / "schema.json"
    schema_file.write_text(json.dumps(schema_data))
    return schema_file


def test_extract_deck_cards(deck_extractor, sample_archive, sample_decklist, tmp_path):
    """Test extracting cards from a deck list."""
    output_file = tmp_path / "output.json"
    
    stats = deck_extractor.extract_deck_cards(
        str(sample_archive),
        str(sample_decklist),
        str(output_file)
    )
    
    # Check statistics
    assert isinstance(stats, DeckListStats)
    assert stats.total_cards == 6
    assert stats.cards_found == 5  # All except Missing Card
    assert stats.cards_missing == 1
    assert stats.success_rate == pytest.approx(83.333333, rel=1e-3)
    
    # Check output file
    assert output_file.exists()
    with open(output_file) as f:
        output_data = json.load(f)
    
    # Verify meta information
    assert "meta" in output_data
    assert "date" in output_data["meta"]
    assert "version" in output_data["meta"]
    
    assert "data" in output_data
    assert "deck" in output_data["data"]
    assert "cards" in output_data["data"]["deck"]
    assert len(output_data["data"]["deck"]["cards"]) == 5
    
    # Check cards
    cards = {card["name"]: card for card in output_data["data"]["deck"]["cards"]}
    
    assert "Shoreline Looter" in cards
    assert cards["Shoreline Looter"]["quantity"] == 4
    
    assert "Lodestone Needle // Guidestone Compass" in cards
    assert cards["Lodestone Needle // Guidestone Compass"]["quantity"] == 4
    
    assert "Temple of Deceit" in cards  # Found in FDN instead of THB
    assert cards["Temple of Deceit"]["quantity"] == 1


@patch("builtins.print")
def test_extract_deck_cards_with_debug(mock_print, deck_extractor, sample_archive, sample_decklist, tmp_path):
    """Test extracting cards with debug output enabled."""
    output_file = tmp_path / "output.json"
    
    deck_extractor.extract_deck_cards(
        str(sample_archive),
        str(sample_decklist),
        str(output_file),
        debug=True
    )
    
    # Verify debug output was printed
    mock_print.assert_any_call("Found exact match for Shoreline Looter in requested set BLB")
    mock_print.assert_any_call("Found exact match for Lodestone Needle in requested set LCI")
    mock_print.assert_any_call("Found 'Temple of Deceit' in set FDN (number 697) - continuing to search for exact match in THB")
    mock_print.assert_any_call("Using fallback match for Temple of Deceit from different set (exact match in THB not found)")


def test_find_double_faced_card(deck_extractor, sample_archive):
    """Test finding a double-faced card in the archive."""
    with open(sample_archive) as f:
        archive_data = json.load(f)
    
    # Test finding double-faced card by front face name
    card_ref = deck_extractor.deck_parser.parse_line("4 Lodestone Needle (LCI) 62")
    card = deck_extractor._find_card(card_ref, archive_data)
    
    assert card is not None
    assert card["name"] == "Lodestone Needle // Guidestone Compass"
    assert card["setCode"] == "LCI"
    assert card["number"] == "62"


def test_find_card_in_different_set(deck_extractor, sample_archive):
    """Test finding a card that exists in a different set than requested."""
    with open(sample_archive) as f:
        archive_data = json.load(f)
    
    # Test finding card that exists in FDN but is requested from THB
    card_ref = deck_extractor.deck_parser.parse_line("1 Temple of Deceit (THB) 245")
    card = deck_extractor._find_card(card_ref, archive_data)
    
    assert card is not None
    assert card["name"] == "Temple of Deceit"
    assert card["setCode"] == "FDN"  # Found in different set
    assert card["number"] == "697"


def test_extract_deck_cards_with_schema(deck_extractor, sample_archive, sample_decklist, tmp_path, sample_schema):
    """Test extracting cards with a custom schema."""
    output_file = tmp_path / "output.json"
    
    stats = deck_extractor.extract_deck_cards(
        str(sample_archive),
        str(sample_decklist),
        str(output_file),
        schema=str(sample_schema)
    )
    
    assert stats.cards_found == 5
    
    with open(output_file) as f:
        output_data = json.load(f)
    
    card = output_data["data"]["deck"]["cards"][0]
    # Only name, type, colors (from schema) and quantity (added by extractor) should be present
    assert set(card.keys()) == {"name", "type", "colors", "quantity"}


def test_extract_deck_cards_missing_archive(deck_extractor, sample_decklist, tmp_path):
    """Test handling a missing archive file."""
    output_file = tmp_path / "output.json"
    
    with pytest.raises(FileNotFoundError, match="Archive file not found"):
        deck_extractor.extract_deck_cards(
            "nonexistent.json",
            str(sample_decklist),
            str(output_file)
        )


def test_extract_deck_cards_invalid_archive(deck_extractor, tmp_path, sample_decklist):
    """Test handling an invalid archive file."""
    # Create invalid JSON file
    invalid_archive = tmp_path / "invalid.json"
    invalid_archive.write_text("invalid json")
    output_file = tmp_path / "output.json"
    
    with pytest.raises(ValueError, match="Invalid JSON in archive"):
        deck_extractor.extract_deck_cards(
            str(invalid_archive),
            str(sample_decklist),
            str(output_file)
        )


def test_extract_deck_cards_missing_decklist(deck_extractor, sample_archive, tmp_path):
    """Test handling a missing deck list file."""
    output_file = tmp_path / "output.json"
    
    with pytest.raises(FileNotFoundError, match="Deck list file not found"):
        deck_extractor.extract_deck_cards(
            str(sample_archive),
            "nonexistent.txt",
            str(output_file)
        )


def test_extract_deck_cards_empty_deck(deck_extractor, sample_archive, tmp_path):
    """Test handling an empty deck list."""
    decklist_file = tmp_path / "empty.txt"
    decklist_file.write_text("")
    output_file = tmp_path / "output.json"
    
    with pytest.raises(ValueError, match="No valid card references found"):
        deck_extractor.extract_deck_cards(
            str(sample_archive),
            str(decklist_file),
            str(output_file)
        )


def test_extract_deck_cards_output_error(deck_extractor, sample_archive, sample_decklist, tmp_path):
    """Test handling output file write errors."""
    # Create a directory instead of a file to cause write error
    output_file = tmp_path / "output.json"
    output_file.mkdir()
    
    with pytest.raises(IOError, match="Error writing output file"):
        deck_extractor.extract_deck_cards(
            str(sample_archive),
            str(sample_decklist),
            str(output_file)
        )


def test_load_archive_invalid_format(deck_extractor, tmp_path):
    """Test loading archive with invalid format (not a dict)."""
    invalid_archive = tmp_path / "invalid_format.json"
    invalid_archive.write_text(json.dumps([1, 2, 3]))  # Array instead of object
    
    with pytest.raises(ValueError, match="Archive must be a JSON object"):
        deck_extractor._load_archive(str(invalid_archive))


def test_get_required_fields_from_file(deck_extractor, sample_schema):
    """Test getting required fields from schema file."""
    required_fields = deck_extractor._get_required_fields(str(sample_schema))
    assert required_fields == ["name", "type", "colors"]


def test_get_required_fields_from_dict(deck_extractor):
    """Test getting required fields from schema dict."""
    schema = {
        "properties": {
            "data": {
                "patternProperties": {
                    ".*": {
                        "properties": {
                            "cards": {
                                "items": {
                                    "required": ["name", "power", "toughness"]
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    required_fields = deck_extractor._get_required_fields(schema)
    assert required_fields == ["name", "power", "toughness"]


def test_get_required_fields_invalid_schema(deck_extractor):
    """Test getting required fields from invalid schema structures."""
    # Test with empty schema
    assert deck_extractor._get_required_fields({}) is None
    
    # Test with missing properties
    assert deck_extractor._get_required_fields({"wrong": {}}) is None
    
    # Test with missing data section
    assert deck_extractor._get_required_fields({"properties": {}}) is None
    
    # Test with missing patternProperties
    schema = {"properties": {"data": {}}}
    assert deck_extractor._get_required_fields(schema) is None
    
    # Test with missing wildcard pattern
    schema = {"properties": {"data": {"patternProperties": {}}}}
    assert deck_extractor._get_required_fields(schema) is None


def test_find_card_missing_data_section(deck_extractor):
    """Test finding card in archive with missing data section."""
    archive_data = {}  # Missing data section
    card_ref = deck_extractor.deck_parser.parse_line("1 Any Card (SET) 123")
    
    result = deck_extractor._find_card(card_ref, archive_data)
    assert result is None
    
    # Verify warning was logged
    deck_extractor.logger.warning.assert_called_once_with("Archive missing 'data' section")


def test_find_card_missing_cards_section(deck_extractor):
    """Test finding card in set with missing cards section."""
    archive_data = {
        "data": {
            "SET": {}  # Missing cards section
        }
    }
    card_ref = deck_extractor.deck_parser.parse_line("1 Any Card (SET) 123")
    
    result = deck_extractor._find_card(card_ref, archive_data)
    assert result is None


def test_get_required_fields_deeply_invalid_schema(deck_extractor):
    """Test getting required fields from deeply invalid schema structures."""
    # Test with invalid cards property
    schema1 = {
        "properties": {
            "data": {
                "patternProperties": {
                    ".*": {
                        "properties": {
                            "cards": "invalid"
                        }
                    }
                }
            }
        }
    }
    assert deck_extractor._get_required_fields(schema1) is None
    
    # Test with invalid items property
    schema2 = {
        "properties": {
            "data": {
                "patternProperties": {
                    ".*": {
                        "properties": {
                            "cards": {
                                "items": "invalid"
                            }
                        }
                    }
                }
            }
        }
    }
    assert deck_extractor._get_required_fields(schema2) is None
    
    # Test with missing required field
    schema3 = {
        "properties": {
            "data": {
                "patternProperties": {
                    ".*": {
                        "properties": {
                            "cards": {
                                "items": {}
                            }
                        }
                    }
                }
            }
        }
    }
    assert deck_extractor._get_required_fields(schema3) is None


def test_get_required_fields_attribute_errors(deck_extractor):
    """Test getting required fields with schema that raises AttributeError."""
    # Test with non-dict values that would raise AttributeError when accessed
    schema1 = {
        "properties": {
            "data": {
                "patternProperties": {
                    ".*": None  # Will raise AttributeError when accessed
                }
            }
        }
    }
    assert deck_extractor._get_required_fields(schema1) is None
    
    schema2 = {
        "properties": {
            "data": {
                "patternProperties": None  # Will raise AttributeError when accessed
            }
        }
    }
    assert deck_extractor._get_required_fields(schema2) is None
    
    schema3 = {
        "properties": {
            "data": None  # Will raise AttributeError when accessed
        }
    }
    assert deck_extractor._get_required_fields(schema3) is None
