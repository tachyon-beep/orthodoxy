"""Shared test fixtures for the card filtering application.

This module provides common fixtures used across multiple test modules.
"""

import pytest
from io import BytesIO
from typing import Union
from unittest.mock import MagicMock, create_autospec

from src.core.config import CardFilterConfig
from src.utils.container import LoggingService, FileService, Container


@pytest.fixture
def create_mock_context():
    """Creates a mock context manager for testing file operations.

    Returns:
        A function that creates a mock context manager with configured
        __enter__ and __exit__ methods.
    """
    def _create_mock_context(return_value: Union[MagicMock, BytesIO]) -> MagicMock:
        context = MagicMock()
        context.__enter__.return_value = return_value
        context.__exit__.return_value = None
        return context
    return _create_mock_context


@pytest.fixture
def config() -> CardFilterConfig:
    """Provides a CardFilterConfig instance for testing.

    Returns:
        A new instance of CardFilterConfig with default settings.
    """
    return CardFilterConfig()


@pytest.fixture
def mock_file() -> BytesIO:
    """Provides a BytesIO object for simulating file operations.

    Returns:
        A new BytesIO instance for testing file operations.
    """
    return BytesIO()


@pytest.fixture
def mock_file_service(config: CardFilterConfig) -> MagicMock:
    """Provides a mock FileService with attribute checking.

    Args:
        config: The CardFilterConfig fixture.

    Returns:
        A MagicMock instance configured to mock FileService behavior.
    """
    mock_fs = MagicMock(spec=FileService)
    
    # Create separate MagicMock objects for each method
    mock_validate = MagicMock(return_value=True)
    mock_open = MagicMock()
    
    # Assign the mocks to the service
    mock_fs.validate_input_file = mock_validate
    mock_fs.open_file = mock_open
    mock_fs.config = config
    
    return mock_fs


@pytest.fixture
def mock_logging_service(config: CardFilterConfig) -> MagicMock:
    """Provides a mock LoggingService with attribute checking.

    Args:
        config: The CardFilterConfig fixture.

    Returns:
        A MagicMock instance configured to mock LoggingService behavior.
    """
    mock_ls = MagicMock(spec=LoggingService)
    mock_ls.error = MagicMock()
    mock_ls.info = MagicMock()
    mock_ls.debug = MagicMock()
    mock_ls.config = config
    return mock_ls


@pytest.fixture
def mock_container(
    config: CardFilterConfig,
    mock_file_service: MagicMock,
    mock_logging_service: MagicMock,
) -> MagicMock:
    """Provides a mock Container with all required services.

    Args:
        config: The CardFilterConfig fixture.
        mock_file_service: The mock FileService fixture.
        mock_logging_service: The mock LoggingService fixture.

    Returns:
        A mock Container instance with configured services.
    """
    container = create_autospec(Container, instance=True)

    # Create mock providers that return the mock services
    mock_config_provider = MagicMock()
    mock_config_provider.return_value = config
    
    mock_file_service_provider = MagicMock()
    mock_file_service_provider.return_value = mock_file_service
    
    mock_logging_service_provider = MagicMock()
    mock_logging_service_provider.return_value = mock_logging_service

    # Assign the mock providers
    container.config = mock_config_provider
    container.file_service = mock_file_service_provider
    container.logging_service = mock_logging_service_provider

    return container
