"""Dependency injection container and service definitions for the card filtering application.

This module provides the dependency injection container and core services for the
Magic: The Gathering card filtering application. It implements the Inversion of Control
(IoC) pattern using dependency-injector to manage application dependencies and services.

The module includes:
- LoggingService: Handles application logging with configurable levels and formats
- FileService: Manages file operations with size validation and buffering
- Container: Main IoC container that wires all dependencies together
"""

from dependency_injector import containers, providers
import logging
from pathlib import Path
from typing import Optional
from src.core.config import CardFilterConfig, load_config
from src.processing.batch import BatchProcessor
from src.io.parsers.deck import DeckListParser
from src.utils.interfaces import CardProcessorInterface
from src.analysis.cards import CardProcessorInterface as CardProcessor
from src.analysis.decks import DeckExtractorService


class LoggingService:
    """Service for handling logging operations."""
    
    LOGGER_NAME = "src.container"
    
    def __init__(self, config: CardFilterConfig):
        # Clear any existing handlers to prevent duplicates
        self.logger = logging.getLogger(self.LOGGER_NAME)
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
            
        handler = logging.FileHandler(config.log_file)
        formatter = logging.Formatter(config.log_format)
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(config.log_level)

    def error(self, message: str) -> None:
        """Log an error message."""
        self.logger.error(message)

    def warning(self, message: str) -> None:
        """Log a warning message."""
        self.logger.warning(message)

    def info(self, message: str) -> None:
        """Log an info message."""
        self.logger.info(message)

    def debug(self, message: str) -> None:
        """Log a debug message."""
        self.logger.debug(message)


class FileService:
    """Service for handling file operations."""

    def __init__(self, config: CardFilterConfig):
        self.config = config

    def validate_input_file(self, filepath: str, max_size_mb: Optional[int] = None) -> bool:
        """Validate input file exists and is within size limits."""
        if not Path(filepath).exists():
            raise FileNotFoundError(f"Input file does not exist: {filepath}")

        max_size = max_size_mb or self.config.max_file_size_mb
        file_size = Path(filepath).stat().st_size / (1024 * 1024)
        if file_size > max_size:
            raise ValueError(f"Input file too large: {file_size:.2f}MB > {max_size}MB")
        return True

    def open_file(self, filepath: str, mode: str = 'r', encoding: Optional[str] = 'utf-8', buffering: Optional[int] = None):
        """Open a file with the specified parameters.
        
        Args:
            filepath: Path to the file to open
            mode: File open mode ('r', 'w', 'rb', 'wb', etc.)
            encoding: File encoding (only used for text mode)
            buffering: Optional buffer size
            
        Returns:
            File object
        """
        buffering = buffering or self.config.buffer_size
        # Don't use encoding for binary mode
        if 'b' in mode:
            return open(filepath, mode=mode, buffering=buffering)
        return open(filepath, mode=mode, encoding=encoding, buffering=buffering)


class Container(containers.DeclarativeContainer):
    """IoC container for dependency injection."""

    # Configuration
    config = providers.Singleton(
        load_config
    )

    # Core Services
    logging_service = providers.Singleton(
        LoggingService,
        config=config
    )

    file_service = providers.Singleton(
        FileService,
        config=config
    )

    # Card Processing
    card_processor = providers.Singleton(
        CardProcessor,
        config=config
    )

    # Batch Processing
    batch_processor = providers.Singleton(
        BatchProcessor,
        card_processor=card_processor,
        logger=logging_service
    )

    # Deck List Processing
    deck_parser = providers.Singleton(
        DeckListParser,
        logger=logging_service
    )

    # Deck Extraction
    deck_extractor_service = providers.Singleton(
        DeckExtractorService,
        card_processor=card_processor,
        logger=logging_service
    )
