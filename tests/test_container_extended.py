"""Extended test coverage for container module components."""

import pytest
import logging
from pathlib import Path
from src.utils.container import LoggingService, FileService, Container
from src.core.config import CardFilterConfig

def test_logging_service_all_levels(tmp_path):
    """Test logging service across all log levels."""
    log_file = tmp_path / "test.log"
    config = CardFilterConfig()
    config.log_file = str(log_file)
    config.log_level = "DEBUG"
    config.log_format = "%(levelname)s: %(message)s"
    
    service = LoggingService(config)
    
    # Test all logging methods
    test_msg = "test message"
    service.debug(test_msg)
    service.info(test_msg)
    service.warning(test_msg)
    service.error(test_msg)
    
    # Verify log contents
    log_content = log_file.read_text()
    assert "DEBUG: test message" in log_content
    assert "INFO: test message" in log_content
    assert "WARNING: test message" in log_content
    assert "ERROR: test message" in log_content

def test_file_service_binary_mode(tmp_path):
    """Test file service with binary mode operations."""
    config = CardFilterConfig()
    service = FileService(config)
    
    test_file = tmp_path / "test.bin"
    test_data = b"binary data"
    
    # Write binary data
    with service.open_file(str(test_file), mode='wb') as f:
        f.write(test_data)
    
    # Read binary data
    with service.open_file(str(test_file), mode='rb') as f:
        content = f.read()
    
    assert content == test_data

def test_file_service_custom_buffer(tmp_path):
    """Test file service with custom buffer size."""
    config = CardFilterConfig()
    config.buffer_size = 1024
    service = FileService(config)
    
    test_file = tmp_path / "test.txt"
    test_data = "test data" * 100  # Create some substantial content
    
    # Write with custom buffer
    with service.open_file(str(test_file), mode='w', buffering=config.buffer_size) as f:
        f.write(test_data)
    
    # Verify content
    with service.open_file(str(test_file), mode='r') as f:
        content = f.read()
    
    assert content == test_data

def test_file_service_size_validation(tmp_path):
    """Test file size validation with different limits."""
    config = CardFilterConfig()
    config.max_file_size_mb = 1
    service = FileService(config)
    
    # Create a test file that's larger than 1MB
    test_file = tmp_path / "test.txt"
    # Create 2MB of data (2 * 1024 * 1024 bytes)
    test_data = "x" * (2 * 1024 * 1024)
    test_file.write_text(test_data)
    
    # Test with default size limit (should fail as file is 2MB and limit is 1MB)
    with pytest.raises(ValueError, match="Input file too large"):
        service.validate_input_file(str(test_file))
    
    # Test with larger size limit (should pass)
    assert service.validate_input_file(str(test_file), max_size_mb=3) is True
    
    # Test with smaller size limit (should fail)
    with pytest.raises(ValueError, match="Input file too large"):
        service.validate_input_file(str(test_file), max_size_mb=1)

def test_file_service_missing_file():
    """Test file service with non-existent file."""
    config = CardFilterConfig()
    service = FileService(config)
    
    with pytest.raises(FileNotFoundError):
        service.validate_input_file("nonexistent_file.txt")

def test_container_initialization():
    """Test complete container initialization with all services."""
    container = Container()
    
    # Verify all core services are initialized
    assert container.config() is not None
    assert isinstance(container.logging_service(), LoggingService)
    assert isinstance(container.file_service(), FileService)
    assert container.card_processor() is not None
    assert container.batch_processor() is not None
    assert container.deck_parser() is not None
    assert container.deck_extractor_service() is not None

def test_container_service_sharing():
    """Test that container properly shares singleton services."""
    container = Container()
    
    # Get multiple instances of services
    logging_service1 = container.logging_service()
    logging_service2 = container.logging_service()
    
    file_service1 = container.file_service()
    file_service2 = container.file_service()
    
    # Verify they are the same instances
    assert logging_service1 is logging_service2
    assert file_service1 is file_service2
