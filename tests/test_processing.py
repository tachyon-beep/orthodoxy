"""Tests for the card processor module."""

import pytest
from typing import Dict, Any, List
from src.analysis.decks import CardProcessorInterface
from src.core.config import CardFilterConfig

@pytest.fixture
def config():
    """Create a test configuration."""
    config = CardFilterConfig()
    config.default_schema = ["name", "type", "colors", "text"]
    config.valid_operators = {"eq", "contains", "gt", "lt"}
    return config

@pytest.fixture
def processor(config):
    """Create a CardProcessorInterface instance."""
    return CardProcessorInterface(config)

@pytest.fixture
def sample_card():
    """Create a sample card for testing."""
    return {
        "name": "Test Card",
        "type": "Creature",
        "colors": ["W", "U"],
        "text": "Test card text",
        "convertedManaCost": 3,
        "foreignData": [
            {"language": "German", "name": "Test Karte"},
            {"language": "French", "name": "Carte Test"}
        ]
    }

@pytest.fixture
def normalized_card(sample_card):
    """Create a normalized version of the sample card."""
    return {
        "name": "Test Card",
        "type": "Creature",
        "colors": ["W", "U"],
        "text": "Test card text",
        "convertedManaCost": 3,
        "colorIdentity": [],
        "edhrecSaltiness": 0.0,
        "availability": []
    }

@pytest.fixture
def normalized_card_with_languages(normalized_card, sample_card):
    """Create a normalized version of the sample card with languages."""
    result = normalized_card.copy()
    result["foreignData"] = sample_card["foreignData"]
    return result

class TestCardProcessor:
    def test_process_card_no_filters(self, processor, sample_card, normalized_card):
        """Test processing card without any filters."""
        result = processor.process_card(sample_card, None, None, None)
        assert result == normalized_card

    def test_process_card_with_filters_eq(self, processor, sample_card, normalized_card):
        """Test processing card with equality filter."""
        filters = {"type": {"eq": "Creature"}}
        result = processor.process_card(sample_card, filters, None, None)
        assert result == normalized_card

        filters = {"type": {"eq": "Instant"}}
        result = processor.process_card(sample_card, filters, None, None)
        assert result is None

    def test_process_card_with_filters_contains(self, processor, sample_card, normalized_card):
        """Test processing card with contains filter."""
        filters = {"colors": {"contains": "W"}}
        result = processor.process_card(sample_card, filters, None, None)
        assert result == normalized_card

        filters = {"colors": {"contains": "R"}}
        result = processor.process_card(sample_card, filters, None, None)
        assert result is None

    def test_process_card_with_filters_gt_lt(self, processor, sample_card, normalized_card):
        """Test processing card with greater than/less than filters."""
        filters = {"convertedManaCost": {"lt": 4}}
        result = processor.process_card(sample_card, filters, None, None)
        assert result == normalized_card

        filters = {"convertedManaCost": {"gt": 4}}
        result = processor.process_card(sample_card, filters, None, None)
        assert result is None

    def test_process_card_with_multiple_filters(self, processor, sample_card, normalized_card):
        """Test processing card with multiple filters."""
        filters = {
            "type": {"eq": "Creature"},
            "colors": {"contains": "W"},
            "convertedManaCost": {"lt": 4}
        }
        result = processor.process_card(sample_card, filters, None, None)
        assert result == normalized_card

        filters["convertedManaCost"] = {"gt": 4}
        result = processor.process_card(sample_card, filters, None, None)
        assert result is None

    def test_process_card_with_additional_languages(self, processor, sample_card, normalized_card_with_languages):
        """Test processing card with language filtering."""
        result = processor.process_card(
            sample_card,
            None,
            None,
            ["German", "French"]
        )
        assert result == normalized_card_with_languages

        result = processor.process_card(
            sample_card,
            None,
            None,
            ["German"]
        )
        assert len(result["foreignData"]) == 1
        assert result["foreignData"][0]["language"] == "German"

    def test_process_card_with_schema_and_languages(self, processor, sample_card):
        """Test processing card with both schema and language filtering."""
        result = processor.process_card(
            sample_card,
            None,
            ["name", "type", "foreignData"],
            ["German"]
        )
        assert set(result.keys()) == {"name", "type", "foreignData"}
        assert len(result["foreignData"]) == 1
        assert result["foreignData"][0]["language"] == "German"

    def test_process_card_with_filters_and_schema(self, processor, sample_card):
        """Test processing card with both filters and schema."""
        filters = {"type": {"eq": "Creature"}}
        schema = ["name", "type"]
        result = processor.process_card(sample_card, filters, schema, None)
        assert set(result.keys()) == set(schema)
        assert result["name"] == sample_card["name"]
        assert result["type"] == sample_card["type"]

    def test_process_card_with_all_options(self, processor, sample_card):
        """Test processing card with filters, schema, and languages."""
        filters = {"type": {"eq": "Creature"}}
        schema = ["name", "type", "foreignData"]
        languages = ["German"]
        result = processor.process_card(sample_card, filters, schema, languages)
        assert set(result.keys()) == set(schema)
        assert len(result["foreignData"]) == 1
        assert result["foreignData"][0]["language"] == "German"

    def test_process_card_invalid_operator(self, processor, sample_card):
        """Test processing card with invalid operator."""
        filters = {"type": {"invalid_op": "Creature"}}
        with pytest.raises(ValueError) as exc_info:
            processor.process_card(sample_card, filters, None, None)
        assert "Invalid operator" in str(exc_info.value)

    def test_process_card_invalid_value_type(self, processor, sample_card):
        """Test processing card with invalid value type."""
        filters = {"convertedManaCost": {"gt": "not a number"}}
        with pytest.raises(ValueError) as exc_info:
            processor.process_card(sample_card, filters, None, None)
        assert "Invalid value type" in str(exc_info.value)

    def test_process_card_missing_field(self, processor, sample_card):
        """Test processing card with filter for missing field."""
        filters = {"nonexistent_field": {"eq": "value"}}
        result = processor.process_card(sample_card, filters, None, None)
        assert result is None

    def test_process_card_empty_filters(self, processor, sample_card, normalized_card):
        """Test processing card with empty filters."""
        filters = {}
        result = processor.process_card(sample_card, filters, None, None)
        assert result == normalized_card

    def test_process_card_empty_schema(self, processor, sample_card):
        """Test processing card with empty schema."""
        schema = []
        result = processor.process_card(sample_card, None, schema, None)
        assert result == {}

    def test_process_card_empty_languages(self, processor, sample_card, normalized_card):
        """Test processing card with empty languages list."""
        result = processor.process_card(sample_card, None, None, [])
        assert result == normalized_card

    def test_process_card_nonexistent_language(self, processor, sample_card, normalized_card):
        """Test processing card with nonexistent language."""
        result = processor.process_card(
            sample_card,
            None,
            None,
            ["Nonexistent"]
        )
        expected = normalized_card.copy()
        expected["foreignData"] = []
        assert result == expected

    def test_process_card_no_foreign_data(self, processor, normalized_card):
        """Test processing card without foreign data."""
        card = {
            "name": "Test Card",
            "type": "Creature"
        }
        result = processor.process_card(card, None, None, ["German"])
        expected = normalized_card.copy()
        expected.update({
            "name": "Test Card",
            "type": "Creature",
            "colors": [],
            "text": "",
            "convertedManaCost": 0,
            "foreignData": []
        })
        assert result == expected

    def test_process_card_with_availability(self, processor: CardProcessorInterface):
        """Tests processing a card with availability field."""
        test_card = {
            "name": "Test Card",
            "type": "Creature",
            "availability": ["paper", "arena"]
        }
        result = processor.process_card(test_card, None, None, None)
        assert result is not None
        assert "availability" in result
        assert result["availability"] == ["paper", "arena"]

        # Test card with different availability
        test_card["availability"] = ["arena"]
        result = processor.process_card(test_card, None, None, None)
        assert result is not None
        assert "availability" in result
        assert result["availability"] == ["arena"]

        # Test card with no availability field (should default to empty list)
        del test_card["availability"]
        result = processor.process_card(test_card, None, None, None)
        assert result is not None
        assert "availability" in result
        assert result["availability"] == []
