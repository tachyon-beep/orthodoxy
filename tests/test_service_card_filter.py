"""Tests for service layer card filtering functionality."""

import pytest
from unittest.mock import Mock, MagicMock, patch, PropertyMock
import io
from typing import BinaryIO, Optional, List, Dict, Any, Union

from src.services.analysis import (
    CardFilterService,
    CardFilterServiceError
)
from src.utils.interfaces import LoggingInterface, CardProcessorInterface, FileHandlerInterface
from src.utils.container import Container
from src.core.config import CardFilterConfig


@pytest.fixture
def mock_logger() -> LoggingInterface:
    """Create a mock logger."""
    logger = Mock()
    logger.error = Mock()
    logger.warning = Mock()
    logger.info = Mock()
    logger.debug = Mock()
    return logger


@pytest.fixture
def mock_file_handler() -> FileHandlerInterface:
    """Create a mock file handler."""
    handler = Mock()
    handler.validate_input_file = Mock(return_value=True)
    
    # Create a BytesIO object with sample JSON content
    sample_json = b'{"meta": {"version": "1.0"}, "data": {}}'
    mock_file = io.BytesIO(sample_json)
    
    # Configure open_file to return a context manager
    mock_context = MagicMock()
    mock_context.__enter__.return_value = mock_file
    handler.open_file.return_value = mock_context
    
    return handler


@pytest.fixture
def mock_card_processor() -> CardProcessorInterface:
    """Create a mock card processor."""
    processor = Mock()
    processor.process_card = Mock(return_value={"name": "Test Card", "type": "Creature"})
    return processor


@pytest.fixture
def mock_file_processor():
    """Create a mock file processor."""
    processor = Mock()
    processor.process_file_stream = Mock()
    processor.write_schema_file = Mock()
    return processor


@pytest.fixture
def mock_container(mock_logger, mock_file_handler, mock_card_processor) -> Union[Container, Mock]:
    """Create a mock container with dependencies."""
    container = Mock()
    container.logging_service = Mock(return_value=mock_logger)
    container.file_service = Mock(return_value=mock_file_handler)
    container.card_processor = Mock(return_value=mock_card_processor)
    container.config = Mock(return_value=CardFilterConfig())
    return container


@pytest.fixture
def service(mock_container, mock_file_processor) -> CardFilterService:
    """Create a CardFilterService instance with mocked file processor."""
    service = CardFilterService(mock_container)
    service.processor = mock_file_processor
    return service


def test_process_cards_basic(service, mock_file_handler):
    """Test basic card processing without filters or schema."""
    service.process_cards(
        input_file="input.json",
        output_file="output.json"
    )
    
    # Verify input validation
    mock_file_handler.validate_input_file.assert_called_once_with("input.json")
    
    # Verify file operations
    assert mock_file_handler.open_file.call_count == 2
    mock_file_handler.open_file.assert_any_call("input.json", mode='rb')
    mock_file_handler.open_file.assert_any_call("output.json", mode='wb')
    
    # Verify processing
    assert service.processor.process_file_stream.called


def test_process_cards_with_options(service, mock_file_handler):
    """Test card processing with filters, schema, and languages."""
    service.process_cards(
        input_file="input.json",
        output_file="output.json",
        schema=["name", "type"],
        filters={"colors": {"contains": "W"}},
        additional_languages=["Japanese"]
    )
    
    # Verify file operations with options
    assert mock_file_handler.open_file.call_count == 2
    
    # Verify processing with options
    service.processor.process_file_stream.assert_called_once()
    call_args = service.processor.process_file_stream.call_args[1]
    assert call_args["schema"] == ["name", "type"]
    assert call_args["filters"] == {"colors": {"contains": "W"}}
    assert call_args["additional_languages"] == ["Japanese"]


def test_process_cards_with_schema_dump(service, mock_file_handler):
    """Test card processing with schema dumping."""
    service.process_cards(
        input_file="input.json",
        output_file="output.json",
        dump_schema="schema.json"
    )
    
    # Verify schema file operation
    service.processor.write_schema_file.assert_called_once_with("schema.json")


def test_process_cards_invalid_input(service, mock_file_handler, mock_logger):
    """Test handling invalid input file."""
    mock_file_handler.validate_input_file.return_value = False
    
    with pytest.raises(ValueError) as exc_info:
        service.process_cards(
            input_file="invalid.json",
            output_file="output.json"
        )
    
    assert "Invalid input file" in str(exc_info.value)
    mock_logger.error.assert_called()


def test_process_cards_file_not_found(service, mock_file_handler, mock_logger):
    """Test handling non-existent input file."""
    mock_file_handler.open_file.side_effect = FileNotFoundError("Test error")
    
    with pytest.raises(FileNotFoundError):
        service.process_cards(
            input_file="nonexistent.json",
            output_file="output.json"
        )
    
    mock_logger.error.assert_called()


def test_process_cards_io_error(service, mock_file_handler, mock_logger):
    """Test handling IO errors."""
    mock_file_handler.open_file.side_effect = IOError("Test error")
    
    with pytest.raises(IOError):
        service.process_cards(
            input_file="input.json",
            output_file="output.json"
        )
    
    mock_logger.error.assert_called()


def test_process_cards_processing_error(service, mock_logger):
    """Test handling processing errors."""
    service.processor.process_file_stream.side_effect = Exception("Test error")
    
    with pytest.raises(CardFilterServiceError) as exc_info:
        service.process_cards(
            input_file="input.json",
            output_file="output.json"
        )
    
    assert "Test error" in str(exc_info.value)
    mock_logger.error.assert_called()


def test_process_cards_schema_error(service, mock_logger):
    """Test handling schema dumping errors."""
    service.processor.write_schema_file.side_effect = Exception("Test error")
    
    with pytest.raises(CardFilterServiceError):
        service.process_cards(
            input_file="input.json",
            output_file="output.json",
            dump_schema="schema.json"
        )
    
    mock_logger.error.assert_called()


def test_error_propagation(service, mock_file_handler, mock_logger):
    """Test error propagation in service."""
    # Test FileNotFoundError propagation
    mock_file_handler.open_file.side_effect = FileNotFoundError("Test error")
    with pytest.raises(FileNotFoundError) as exc_info:
        service.process_cards("input.json", "output.json")
    assert "Test error" in str(exc_info.value)
    
    # Reset mock
    mock_file_handler.open_file.side_effect = None
    
    # Test ValueError propagation
    mock_file_handler.validate_input_file.return_value = False
    with pytest.raises(ValueError) as exc_info:
        service.process_cards("input.json", "output.json")
    assert "Invalid input file" in str(exc_info.value)
    
    # Reset validate_input_file for next test
    mock_file_handler.validate_input_file.return_value = True
    
    # Test CardFilterServiceError wrapping
    service.processor.process_file_stream.side_effect = Exception("Test error")
    with pytest.raises(CardFilterServiceError) as exc_info:
        service.process_cards("input.json", "output.json")
    assert "Test error" in str(exc_info.value)
