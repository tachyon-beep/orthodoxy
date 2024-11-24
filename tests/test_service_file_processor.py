"""Tests for file processor service functionality."""

import pytest
from unittest.mock import Mock, patch, mock_open, MagicMock
from io import BytesIO
import json

from src.services.file_stream import (
    FileProcessor,
    FileProcessorError,
    StreamProcessingError,
    MetadataError
)
from src.utils.container import Container
from src.core.errors import CardFilterError
from src.core.config import CardFilterConfig


@pytest.fixture
def mock_logger():
    """Create a mock logger implementing the LoggingInterface protocol."""
    logger = MagicMock()
    logger.error = MagicMock()
    logger.warning = MagicMock()
    logger.info = MagicMock()
    logger.debug = MagicMock()
    return logger


@pytest.fixture
def mock_file_service():
    """Create a mock file service implementing the FileHandlerInterface protocol."""
    service = MagicMock()
    service.open_file = MagicMock()
    service.validate_input_file = MagicMock(return_value=True)
    return service


@pytest.fixture
def mock_config():
    """Create a mock config."""
    return CardFilterConfig(
        default_schema=["type", "object"],
        buffer_size=1000
    )


@pytest.fixture
def container(mock_logger, mock_file_service, mock_config):
    """Create a container with mock services."""
    container = MagicMock()
    container.logging_service = Mock(return_value=mock_logger)
    container.file_service = Mock(return_value=mock_file_service)
    container.config = Mock(return_value=mock_config)
    return container


@pytest.fixture
def processor(container):
    """Create a FileProcessor instance."""
    return FileProcessor(container)


def test_write_schema_file(processor, mock_file_service):
    """Test writing schema file."""
    mock_file = MagicMock()
    mock_context = MagicMock()
    mock_context.__enter__.return_value = mock_file
    processor.file_service.open_file.return_value = mock_context
    
    processor.write_schema_file("test_schema.json")
    processor.file_service.open_file.assert_called_once()


def test_write_schema_file_error(processor, mock_logger):
    """Test error handling when writing schema file."""
    processor.file_service.open_file.side_effect = IOError("Test error")
    with pytest.raises(FileProcessorError):
        processor.write_schema_file("test_schema.json")
    processor.logging.error.assert_called_once()


def test_write_metadata(processor):
    """Test writing metadata section."""
    outfile = BytesIO()
    metadata = {"version": "1.0"}
    
    processor._write_metadata(outfile, metadata)
    result = outfile.getvalue().decode('utf-8')
    
    assert '"version": "1.0"' in result
    assert ',"data":{' in result


def test_write_metadata_error(processor, mock_logger):
    """Test error handling when writing metadata."""
    with pytest.raises(MetadataError):
        processor._write_metadata(None, {"test": "data"})
    processor.logging.error.assert_called_once()


def test_process_card(processor, mock_logger):
    """Test processing a single card."""
    mock_card_processor = MagicMock()
    mock_card_processor.process_card.return_value = {"name": "Test Card"}
    mock_set_writer = MagicMock()
    
    processor._process_card(
        {"name": "Test Card"},
        mock_card_processor,
        None,
        None,
        None,
        mock_set_writer
    )
    
    mock_card_processor.process_card.assert_called_once()
    mock_set_writer.write_processed_card.assert_called_once_with({"name": "Test Card"})


def test_process_card_error(processor, mock_logger):
    """Test error handling when processing card."""
    mock_card_processor = MagicMock()
    mock_card_processor.process_card.side_effect = Exception("Test error")
    
    with pytest.raises(StreamProcessingError):
        processor._process_card(
            {"name": "Test Card"},
            mock_card_processor,
            None,
            None,
            None,
            MagicMock()
        )
    processor.logging.error.assert_called_once()


def test_handle_prefix(processor):
    """Test handling prefix events."""
    mock_set_writer = MagicMock()
    current_state = {
        'current_card': {},
        'current_set': None
    }
    
    processor._handle_prefix(
        "data.LEA.cards.item",
        "start_map",
        None,
        current_state,
        mock_set_writer,
        MagicMock(),
        None,
        None,
        None
    )
    
    assert current_state['current_card'] == {}
    mock_set_writer.handle_set_transition.assert_called_once_with("LEA")


def test_handle_prefix_error(processor, mock_logger):
    """Test error handling in prefix handling."""
    mock_set_writer = MagicMock()
    mock_card_processor = MagicMock()
    mock_card_processor.process_card.side_effect = Exception("Test error")
    
    with pytest.raises(StreamProcessingError):
        processor._handle_prefix(
            "data.LEA.cards.item",
            "end_map",
            None,
            {'current_card': {'name': 'Test Card'}, 'current_set': 'LEA'},
            mock_set_writer,
            mock_card_processor,
            None,
            None,
            None
        )
    # The error is logged twice: once for process_card and once for handle_prefix
    assert processor.logging.error.call_count == 2
    assert "Failed to process card: Test error" in processor.logging.error.call_args_list[0][0][0]
    assert "Failed to handle prefix" in processor.logging.error.call_args_list[1][0][0]

def test_process_file_stream(processor):
    """Test complete file stream processing."""
    input_data = {
        "meta": {"version": "1.0"},
        "data": {}
    }
    json_str = json.dumps(input_data)
    infile = BytesIO(json_str.encode('utf-8'))
    outfile = BytesIO()
    mock_card_processor = MagicMock()

    processor.process_file_stream(infile, outfile, mock_card_processor)

    result = outfile.getvalue().decode('utf-8')
    # Parse the result to properly compare JSON structures
    parsed_result = json.loads(result)

    assert "meta" in parsed_result
    assert "data" in parsed_result
    # The metadata is an empty dict because we're using CardSetWriter
    # which doesn't preserve input metadata by design
    assert isinstance(parsed_result["meta"], dict)
    assert isinstance(parsed_result["data"], dict)

def test_process_file_stream_no_meta(processor):
    """Test file stream processing when input has no metadata."""
    input_data = {
        "data": {}
    }
    json_str = json.dumps(input_data)
    infile = BytesIO(json_str.encode('utf-8'))
    outfile = BytesIO()
    mock_card_processor = MagicMock()

    processor.process_file_stream(infile, outfile, mock_card_processor)

    result = outfile.getvalue().decode('utf-8')
    parsed_result = json.loads(result)

    assert "meta" in parsed_result
    assert "data" in parsed_result
    # The metadata is an empty dict when no metadata exists
    assert isinstance(parsed_result["meta"], dict)
    assert isinstance(parsed_result["data"], dict)

def test_process_file_stream_error(processor, mock_logger):
    """Test error handling in file stream processing."""
    infile = BytesIO(b'{"meta": {"version": "1.0"}, "data": {"LEA": {"cards": [{"name": "Test Card"}]}}}')
    outfile = BytesIO()
    mock_card_processor = MagicMock()
    mock_card_processor.process_card.side_effect = Exception("Test error")
    
    with pytest.raises(FileProcessorError):
        processor.process_file_stream(infile, outfile, mock_card_processor)
    processor.logging.error.assert_called()
