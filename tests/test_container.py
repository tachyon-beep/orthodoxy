"""Tests for dependency injection container."""

import logging
import pytest
from unittest.mock import patch
from src.utils.container import Container, LoggingService
from src.core.config import CardFilterConfig, ConfigVersion


@pytest.fixture
def config():
    """Create a test configuration."""
    return CardFilterConfig(
        version=ConfigVersion(major=1, minor=0, patch=0),
        max_file_size_mb=10,
        buffer_size=8192,
        default_schema=["name", "type"],
        valid_operators={"eq", "contains", "gt", "lt"},
        log_file="test.log",
        log_format="%(levelname)s: %(message)s",
        log_level="DEBUG"
    )


class TestLoggingService:
    def test_logging_initialization(self, config):
        """Test logging service initialization."""
        # Clear any existing handlers
        logger = logging.getLogger("src.container")
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
            
        with patch("builtins.open"):
            service = LoggingService(config)
            assert service.logger.level == logging.DEBUG
            assert len(service.logger.handlers) == 1
            handler = service.logger.handlers[0]
            assert isinstance(handler, logging.FileHandler)
            assert isinstance(handler.formatter, logging.Formatter)
            assert handler.formatter._fmt == "%(levelname)s: %(message)s"

    def test_logging_methods(self, config):
        """Test logging methods."""
        with patch("builtins.open"):
            service = LoggingService(config)
            with patch.object(service.logger, "error") as mock_error, \
                 patch.object(service.logger, "info") as mock_info, \
                 patch.object(service.logger, "debug") as mock_debug:
                
                service.error("test error")
                service.info("test info")
                service.debug("test debug")
                
                mock_error.assert_called_once_with("test error")
                mock_info.assert_called_once_with("test info")
                mock_debug.assert_called_once_with("test debug")


class TestContainer:
    def test_container_initialization(self):
        """Test container initialization."""
        container = Container()
        container.init_resources()
        
        assert container.config() is not None
        assert container.logging_service() is not None
        assert container.file_service() is not None
        assert container.card_processor() is not None

    def test_container_singleton_services(self):
        """Test that services are singletons."""
        container = Container()
        container.init_resources()
        
        config1 = container.config()
        config2 = container.config()
        assert config1 is config2
        
        logging1 = container.logging_service()
        logging2 = container.logging_service()
        assert logging1 is logging2
        
        file_service1 = container.file_service()
        file_service2 = container.file_service()
        assert file_service1 is file_service2
        
        processor1 = container.card_processor()
        processor2 = container.card_processor()
        assert processor1 is processor2

    def test_container_dependencies(self):
        """Test that dependencies are properly injected."""
        container = Container()
        container.init_resources()
        
        # Verify services can be created
        processor = container.card_processor()
        assert processor is not None
        
        file_service = container.file_service()
        assert file_service is not None
