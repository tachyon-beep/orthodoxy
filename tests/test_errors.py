"""Tests for error handling and custom exceptions."""

import pytest
from src.core.errors import (
    CardFilterError,
    InvalidFilterError,
    SchemaValidationError,
    CardProcessingError,
    BatchProcessingError
)
from src.services.filter_parser import (
    FilterParseError,
    CardDataParseError
)

def test_batch_processing_error():
    """Test BatchProcessingError requires one positional argument for message."""
    error = BatchProcessingError("batch error message")
    assert str(error) == "batch error message"

def test_card_processing_error():
    """Test CardProcessingError requires one positional argument for message."""
    error = CardProcessingError("card error message")
    assert str(error) == "card error message"

def test_error_hierarchy():
    """Test error class inheritance hierarchy."""
    assert issubclass(InvalidFilterError, CardFilterError)
    assert issubclass(SchemaValidationError, CardFilterError)
    assert issubclass(CardProcessingError, CardFilterError)
    assert issubclass(BatchProcessingError, CardFilterError)

def test_filter_parse_error():
    """Test FilterParseError with invalid JSON."""
    error = FilterParseError("Invalid JSON syntax: {invalid json}")
    assert "Invalid JSON syntax" in str(error)

def test_schema_validation_error():
    """Test SchemaValidationError with all attributes."""
    error = SchemaValidationError("Invalid type")
    error.field_name = "power"
    error.expected_type = "number"
    error.actual_value = "N/A"
    
    assert str(error) == "Invalid type"
    assert error.field_name == "power"
    assert error.expected_type == "number"
    assert error.actual_value == "N/A"

def test_invalid_filter_error():
    """Test InvalidFilterError with filter data."""
    filter_data = {"colors": {"invalid_op": "R"}}
    error = InvalidFilterError("Invalid filter", filter_data)
    assert str(error) == "Invalid filter"
    assert error.filter_data == filter_data

def test_card_data_parse_error():
    """Test CardDataParseError with format issues."""
    error = CardDataParseError("Invalid card data format")
    assert str(error) == "Invalid card data format"

def test_error_chaining():
    """Test error chaining and context preservation."""
    try:
        try:
            raise ValueError("Original error")
        except ValueError as e:
            raise CardProcessingError("Processing failed") from e
    except CardProcessingError as e:
        assert str(e) == "Processing failed"
        assert isinstance(e.__cause__, ValueError)
        assert str(e.__cause__) == "Original error"

def test_service_error_handling():
    """Test error handling in a service-like context."""
    def process_card(card_data):
        if not isinstance(card_data, dict):
            raise CardProcessingError("Invalid card data type")
        if "name" not in card_data:
            error = SchemaValidationError("Missing required field")
            error.field_name = "name"
            error.expected_type = "string"
            return error
        return card_data

    # Test invalid data type
    with pytest.raises(CardProcessingError) as exc:
        process_card([])  # Pass list instead of dict
    assert "Invalid card data type" in str(exc.value)

    # Test missing required field
    result = process_card({"power": "2"})  # Missing name field
    assert isinstance(result, SchemaValidationError)
    assert "Missing required field" in str(result)
    assert result.field_name == "name"
    assert result.expected_type == "string"

def test_error_handling_integration():
    """Test error handling across multiple layers."""
    class MockCardProcessor:
        def process_card(self, card_data):
            if not isinstance(card_data, dict):
                raise CardProcessingError("Invalid card data type")
            if "name" not in card_data:
                error = SchemaValidationError("Missing required field")
                error.field_name = "name"
                error.expected_type = "string"
                return error
            return card_data

    class MockBatchProcessor:
        def __init__(self):
            self.card_processor = MockCardProcessor()

        def process_batch(self, cards):
            results = []
            errors = []
            for card in cards:
                try:
                    result = self.card_processor.process_card(card)
                    if isinstance(result, Exception):
                        errors.append(result)
                    else:
                        results.append(result)
                except CardFilterError as e:
                    errors.append(e)
            return results, errors

    processor = MockBatchProcessor()
    cards = [
        {"name": "Valid Card"},  # Valid
        [],  # Invalid type
        {"power": "2"}  # Missing required field
    ]

    results, errors = processor.process_batch(cards)

    assert len(results) == 1
    assert len(errors) == 2
    assert isinstance(errors[0], CardProcessingError)
    assert isinstance(errors[1], SchemaValidationError)
    assert "Invalid card data type" in str(errors[0])
    assert "Missing required field" in str(errors[1])
