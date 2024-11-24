"""Tests for pytest fixtures to improve coverage of conftest.py."""

import pytest
from io import BytesIO
from unittest.mock import MagicMock
from src.core.config import CardFilterConfig
from src.utils.container import LoggingService, FileService

def test_create_mock_context(create_mock_context):
    """Test the create_mock_context fixture with different return values."""
    # Test with MagicMock return value
    mock_return = MagicMock()
    context = create_mock_context(mock_return)
    
    with context as result:
        assert result == mock_return
    
    # Test with BytesIO return value
    bio = BytesIO(b"test data")
    context = create_mock_context(bio)
    
    with context as result:
        assert result == bio
    
    # Verify context manager methods were called
    assert context.__enter__.called
    assert context.__exit__.called

def test_config_fixture(config):
    """Test the config fixture provides expected defaults."""
    assert isinstance(config, CardFilterConfig)
    # Verify default config values
    assert hasattr(config, 'log_level')
    assert hasattr(config, 'log_file')
    assert hasattr(config, 'buffer_size')
    assert hasattr(config, 'max_file_size_mb')

def test_mock_file_fixture(mock_file):
    """Test the mock_file fixture provides a usable BytesIO object."""
    assert isinstance(mock_file, BytesIO)
    
    # Test writing and reading
    test_data = b"test data"
    mock_file.write(test_data)
    mock_file.seek(0)
    assert mock_file.read() == test_data
    
    # Test seeking and truncating
    mock_file.seek(0)
    mock_file.truncate()
    mock_file.write(b"new data")
    mock_file.seek(0)
    assert mock_file.read() == b"new data"

def test_mock_file_service_fixture(mock_file_service, config):
    """Test the mock_file_service fixture provides expected functionality."""
    assert isinstance(mock_file_service, MagicMock)
    assert mock_file_service._spec_class == FileService
    
    # Test validate_input_file method with different arguments
    assert mock_file_service.validate_input_file("test.txt") is True
    assert mock_file_service.validate_input_file("test.txt", max_size_mb=10) is True
    
    # Test open_file method with different arguments
    mock_file_service.open_file("test.txt")
    mock_file_service.open_file("test.txt", mode='rb')
    mock_file_service.open_file("test.txt", encoding='utf-16')
    mock_file_service.open_file("test.txt", buffering=1024)
    
    # Verify all method calls
    assert mock_file_service.validate_input_file.call_count == 2
    assert mock_file_service.open_file.call_count == 4
    
    # Verify config attribute
    assert mock_file_service.config == config

def test_mock_logging_service_fixture(mock_logging_service, config):
    """Test the mock_logging_service fixture provides expected functionality."""
    assert isinstance(mock_logging_service, MagicMock)
    assert mock_logging_service._spec_class == LoggingService
    
    # Test all logging methods with different messages
    messages = [
        "error message",
        "warning: test failed",
        "info: process completed",
        "debug: variable x = 42"
    ]
    
    mock_logging_service.error(messages[0])
    mock_logging_service.warning(messages[1])
    mock_logging_service.info(messages[2])
    mock_logging_service.debug(messages[3])
    
    # Verify all method calls with correct arguments
    mock_logging_service.error.assert_called_with(messages[0])
    mock_logging_service.warning.assert_called_with(messages[1])
    mock_logging_service.info.assert_called_with(messages[2])
    mock_logging_service.debug.assert_called_with(messages[3])
    
    # Verify config attribute
    assert mock_logging_service.config == config

def test_mock_container_fixture(mock_container, config, mock_file_service, mock_logging_service):
    """Test the mock_container fixture provides expected functionality."""
    # Test config provider
    config1 = mock_container.config()
    config2 = mock_container.config()
    assert config1 == config2 == config
    
    # Test file service provider
    fs1 = mock_container.file_service()
    fs2 = mock_container.file_service()
    assert fs1 == fs2 == mock_file_service
    
    # Test logging service provider
    ls1 = mock_container.logging_service()
    ls2 = mock_container.logging_service()
    assert ls1 == ls2 == mock_logging_service
    
    # Verify provider call counts
    assert mock_container.config.call_count == 2
    assert mock_container.file_service.call_count == 2
    assert mock_container.logging_service.call_count == 2

def test_mock_container_provider_types(mock_container):
    """Test that mock_container providers return correct types."""
    # Test return types
    assert isinstance(mock_container.config(), CardFilterConfig)
    assert isinstance(mock_container.file_service(), MagicMock)
    assert isinstance(mock_container.logging_service(), MagicMock)
    
    # Test spec classes
    assert mock_container.file_service()._spec_class == FileService
    assert mock_container.logging_service()._spec_class == LoggingService
