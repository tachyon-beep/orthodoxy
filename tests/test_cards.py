"""Tests for card processing functionality."""

import pytest
from typing import Dict, Any, Optional, List

from src.analysis.cards import CardProcessorInterface, FilterStrategy
from src.core.config import CardFilterConfig
from src.utils.interfaces import CardProcessorInterface as CardProcessorProtocol
from src.core.errors import CardFilterError


@pytest.fixture
def config() -> CardFilterConfig:
    """Create a test configuration."""
    return CardFilterConfig()


@pytest.fixture
def processor(config) -> CardProcessorProtocol:
    """Create a CardProcessorInterface instance."""
    return CardProcessorInterface(config)


def test_create_base_card(processor):
    """Test creating base card with defaults."""
    input_card = {"name": "Test Card", "type": "Creature"}
    result = processor.create_base_card(input_card)
    
    # Check required fields
    assert result["name"] == "Test Card"
    assert result["type"] == "Creature"
    
    # Check default values
    assert result["colors"] == []
    assert result["colorIdentity"] == []
    assert result["convertedManaCost"] == 0
    assert result["text"] == ""
    assert result["edhrecSaltiness"] == pytest.approx(0.0)
    assert result["language"] == "English"
    assert result["foreignData"] == []
    assert result["availability"] == []


def test_filter_foreign_data(processor):
    """Test filtering foreign language data."""
    card_data = {
        "foreignData": [
            {"language": "Japanese", "name": "テスト"},
            {"language": "German", "name": "Test"},
            {"language": "French", "name": "Test"}
        ]
    }
    
    # Test with specific languages
    result = processor.filter_foreign_data(card_data, ["Japanese", "German"])
    assert len(result) == 2
    assert result[0]["language"] == "Japanese"
    assert result[1]["language"] == "German"
    
    # Test with no languages
    result = processor.filter_foreign_data(card_data, None)
    assert result == []
    
    # Test with empty languages list
    result = processor.filter_foreign_data(card_data, [])
    assert result == []


def test_apply_schema(processor):
    """Test applying schema to card data."""
    card = {
        "name": "Test Card",
        "type": "Creature",
        "text": "Test text",
        "language": "English",
        "extra": "value"
    }
    
    # Test with specific schema
    result = processor.apply_schema(card, ["name", "type"])
    assert set(result.keys()) == {"name", "type"}
    assert result["name"] == "Test Card"
    
    # Test with no schema (should exclude internal fields)
    result = processor.apply_schema(card, None)
    assert "language" not in result
    assert "name" in result
    
    # Test with empty schema
    result = processor.apply_schema(card, [])
    assert result == {}


def test_evaluate_filters(processor):
    """Test filter evaluation logic."""
    card = {
        "name": "Test Card",
        "colors": ["W", "U"],
        "convertedManaCost": 3,
        "type": "Creature"
    }
    
    # Test simple equality filter
    assert processor.evaluate_filters(card, {"name": {"eq": "Test Card"}})
    
    # Test numeric comparison
    assert processor.evaluate_filters(card, {"convertedManaCost": {"lt": 4}})
    assert not processor.evaluate_filters(card, {"convertedManaCost": {"gt": 4}})
    
    # Test list contains
    assert processor.evaluate_filters(card, {"colors": {"contains": "W"}})
    assert not processor.evaluate_filters(card, {"colors": {"contains": "B"}})
    
    # Test multiple conditions
    assert processor.evaluate_filters(card, {
        "colors": {"contains": "W"},
        "convertedManaCost": {"lte": 3}
    })


def test_process_card(processor):
    """Test complete card processing pipeline."""
    input_card = {
        "name": "Test Card",
        "type": "Creature",
        "colors": ["W", "U"],
        "convertedManaCost": 3,
        "text": "Test text",
        "foreignData": [
            {"language": "Japanese", "name": "テスト"},
            {"language": "German", "name": "Test"}
        ]
    }
    
    # Test with filters, schema, and languages
    result = processor.process_card(
        input_card,
        filters={"colors": {"contains": "W"}},
        schema=["name", "colors", "convertedManaCost", "foreignData"],
        additional_languages=["Japanese"]
    )
    
    assert result is not None
    assert set(result.keys()) == {"name", "colors", "convertedManaCost", "foreignData"}
    assert len(result["foreignData"]) == 1
    assert result["foreignData"][0]["language"] == "Japanese"
    
    # Test card that doesn't match filters
    result = processor.process_card(
        input_card,
        filters={"colors": {"contains": "B"}},
        schema=None,
        additional_languages=None
    )
    assert result is None


def test_filter_strategy():
    """Test filter strategy evaluation."""
    strategy = FilterStrategy()
    
    # Test numeric comparisons with integers
    assert strategy.evaluate_condition(3, 2, "gt")
    assert strategy.evaluate_condition(2, 3, "lt")
    assert strategy.evaluate_condition(3, 3, "gte")
    assert strategy.evaluate_condition(3, 3, "lte")
    assert strategy.evaluate_condition(3, 3, "eq")
    
    # Test string operations
    assert strategy.evaluate_condition("test", "test", "eq")
    assert not strategy.evaluate_condition("test", "other", "eq")
    
    # Test list operations
    assert strategy.evaluate_condition(["A", "B"], "A", "contains")
    assert not strategy.evaluate_condition(["A", "B"], "C", "contains")


def test_error_handling(processor):
    """Test error handling in card processing."""
    # Test missing required fields
    with pytest.raises(ValueError) as exc_info:
        processor.process_card({}, None, None, None)
    assert "missing required fields" in str(exc_info.value).lower()
    
    # Test invalid filter operator
    with pytest.raises(ValueError) as exc_info:
        processor.process_card(
            {"name": "Test", "type": "Creature"},
            {"test": {"invalid": "value"}},
            None,
            None
        )
    assert "invalid operator" in str(exc_info.value).lower()
    
    # Test invalid numeric comparison
    with pytest.raises(ValueError) as exc_info:
        processor.process_card(
            {"name": "Test", "type": "Creature", "power": "X"},
            {"power": {"gt": "2"}},
            None,
            None
        )
    assert "invalid value type" in str(exc_info.value).lower()


def test_process_card_with_schema_only(processor):
    """Test processing card with only schema specified."""
    input_card = {
        "name": "Test Card",
        "type": "Creature",
        "colors": ["W", "U"],
        "text": "Test text"
    }
    
    result = processor.process_card(
        input_card,
        filters=None,
        schema=["name", "type"],
        additional_languages=None
    )
    
    assert result is not None
    assert set(result.keys()) == {"name", "type"}
    assert result["name"] == "Test Card"
    assert result["type"] == "Creature"


def test_process_card_with_languages_only(processor):
    """Test processing card with only languages specified."""
    input_card = {
        "name": "Test Card",
        "type": "Creature",
        "foreignData": [
            {"language": "Japanese", "name": "テスト"},
            {"language": "German", "name": "Test"}
        ]
    }
    
    result = processor.process_card(
        input_card,
        filters=None,
        schema=None,
        additional_languages=["Japanese"]
    )
    
    assert result is not None
    assert len(result["foreignData"]) == 1
    assert result["foreignData"][0]["language"] == "Japanese"
