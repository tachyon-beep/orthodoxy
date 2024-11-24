"""Tests for the card filter service functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any
from io import BytesIO, StringIO
from contextlib import contextmanager

from src.services.filter_parser import CardParser
from src.services.file_stream import FileProcessor
from src.services.analysis import CardFilterService, CardFilterServiceError
from src.utils.container import Container


@pytest.fixture
def mock_logger():
    """Create a mock logger."""
    logger = Mock()
    # Explicitly set up the expected methods
    logger.error = Mock()
    logger.warning = Mock()
    logger.info = Mock()
    logger.debug = Mock()
    return logger


@pytest.fixture
def mock_file_service():
    """Create a mock file service."""
    service = Mock()
    service.validate_input_file = Mock(return_value=True)
    
    # Create a mock context manager for open_file
    cm = Mock()
    cm.__enter__ = Mock()
    cm.__exit__ = Mock(return_value=False)
    service.open_file = Mock(return_value=cm)
    
    return service


@pytest.fixture
def mock_card_processor():
    """Create a mock card processor."""
    processor = Mock()
    processor.process_card = Mock()
    return processor


@pytest.fixture
def mock_config():
    """Create a mock config."""
    config = Mock()
    config.default_schema = {"type": "object"}
    return config


@pytest.fixture
def container(mock_logger, mock_file_service, mock_card_processor, mock_config):
    """Create a container with mock services."""
    container = Container()
    # Override with mock instances directly
    container.logging_service = Mock(return_value=mock_logger)
    container.file_service = Mock(return_value=mock_file_service)
    container.card_processor = Mock(return_value=mock_card_processor)
    container.config = Mock(return_value=mock_config)
    return container


@pytest.fixture
def service(container):
    """Create a CardFilterService instance."""
    return CardFilterService(container)


def test_service_initialization(service):
    """Test service initialization."""
    assert isinstance(service.parser, CardParser)
    assert isinstance(service.processor, FileProcessor)


def test_process_filter_string(service):
    """Test filter string processing."""
    filter_str = '{"name": "Test Card"}'
    result = service.process_filter_string(filter_str)
    assert isinstance(result, dict)
    assert result["name"] == {"eq": "Test Card"}


def test_process_filter_string_error(service, mock_logger):
    """Test filter string processing error handling."""
    with pytest.raises(Exception):
        service.process_filter_string("{invalid json}")
    mock_logger.error.assert_called_once()


def test_process_cards_basic(service, mock_file_service):
    """Test basic card processing without filters or schema."""
    # Mock file-like objects
    mock_infile = BytesIO(b'{"meta": {"version": "1.0"}, "data": {}}')
    mock_outfile = BytesIO()
    
    # Set up the context manager returns
    mock_file_service.open_file.return_value.__enter__.side_effect = [mock_infile, mock_outfile]
    
    service.process_cards(
        input_file="input.json",
        output_file="output.json"
    )
    
    mock_file_service.validate_input_file.assert_called_once()
    assert mock_file_service.open_file.call_count == 2


def test_process_cards_with_options(service, mock_file_service):
    """Test card processing with filters, schema, and languages."""
    # Mock file-like objects
    mock_infile = BytesIO(b'{"meta": {"version": "1.0"}, "data": {}}')
    mock_outfile = BytesIO()
    
    # Set up the context manager returns
    mock_file_service.open_file.return_value.__enter__.side_effect = [mock_infile, mock_outfile]
    
    service.process_cards(
        input_file="input.json",
        output_file="output.json",
        schema=["name", "type"],
        filters={"colors": {"in": ["W"]}},  # Changed from contains to in
        additional_languages=["Japanese"]
    )
    
    mock_file_service.validate_input_file.assert_called_once()
    assert mock_file_service.open_file.call_count == 2


def test_process_cards_with_schema_dump(service, mock_file_service):
    """Test card processing with schema dumping."""
    # Mock file-like objects
    mock_infile = BytesIO(b'{"meta": {"version": "1.0"}, "data": {}}')
    mock_outfile = BytesIO()
    mock_schema_file = StringIO()  # Use StringIO for text file
    
    # Create context managers for each file
    @contextmanager
    def mock_context(file_obj):
        yield file_obj
    
    # Set up the open_file mock to return appropriate context managers
    def open_file_side_effect(path, mode='rb', encoding=None):
        if path == "input.json":
            return mock_context(mock_infile)
        elif path == "output.json":
            return mock_context(mock_outfile)
        elif path == "schema.json":
            return mock_context(mock_schema_file)
    
    mock_file_service.open_file.side_effect = open_file_side_effect
    
    service.process_cards(
        input_file="input.json",
        output_file="output.json",
        dump_schema="schema.json"
    )
    
    mock_file_service.validate_input_file.assert_called_once()
    assert mock_file_service.open_file.call_count == 3


def test_process_cards_invalid_input(service, mock_file_service, mock_logger):
    """Test handling invalid input file."""
    mock_file_service.validate_input_file.return_value = False
    
    with pytest.raises(ValueError):
        service.process_cards("input.json", "output.json")
    
    mock_logger.error.assert_called_once_with("Invalid input file: input.json")


def test_process_cards_processing_error(service, mock_logger):
    """Test handling processing errors."""
    mock_processor = Mock()
    mock_processor.process_file_stream.side_effect = Exception("Test error")
    service.processor = mock_processor
    
    with pytest.raises(CardFilterServiceError) as exc_info:
        service.process_cards(
            input_file="input.json",
            output_file="output.json"
        )
    
    assert "Test error" in str(exc_info.value)
    mock_logger.error.assert_called_once()


def test_process_cards_schema_error(service, mock_logger):
    """Test handling schema writing errors."""
    mock_processor = Mock()
    mock_processor.write_schema_file.side_effect = Exception("Test error")
    service.processor = mock_processor
    
    with pytest.raises(CardFilterServiceError) as exc_info:
        service.process_cards(
            input_file="input.json",
            output_file="output.json",
            dump_schema="schema.json"
        )
    
    assert "Failed to write schema file" in str(exc_info.value)
    mock_logger.error.assert_called_once()


def test_error_propagation(service, mock_file_service, mock_logger):
    """Test error propagation in service."""
    # Test FileNotFoundError propagation
    mock_file_service.open_file.side_effect = FileNotFoundError("Test error")
    with pytest.raises(FileNotFoundError) as exc_info:
        service.process_cards("input.json", "output.json")
    assert "Test error" in str(exc_info.value)
    
    # Reset mock
    mock_file_service.open_file.side_effect = None
    mock_logger.error.reset_mock()
    
    # Test ValueError propagation
    mock_file_service.validate_input_file.return_value = False
    with pytest.raises(ValueError):
        service.process_cards("input.json", "output.json")
    mock_logger.error.assert_called_once_with("Invalid input file: input.json")
    
    # Reset validate_input_file and logger for next test
    mock_file_service.validate_input_file.return_value = True
    mock_logger.error.reset_mock()
    
    # Test CardFilterServiceError wrapping
    mock_processor = Mock()
    mock_processor.process_file_stream.side_effect = Exception("Test error")
    service.processor = mock_processor
    
    with pytest.raises(CardFilterServiceError) as exc_info:
        service.process_cards("input.json", "output.json")
    assert "Test error" in str(exc_info.value)
    mock_logger.error.assert_called_once()
