"""Additional tests for interfaces to improve coverage."""

import pytest
from typing import Optional, Dict, Any, List, Union, IO
from src.utils.interfaces import LoggingInterface, CardProcessorInterface, FileHandlerInterface
from pathlib import Path
from io import StringIO, BytesIO

class FullLogger(LoggingInterface):
    """Complete implementation of LoggingInterface protocol for testing."""
    
    def __init__(self):
        self.messages = []
        self.levels = []
    
    def error(self, message: str) -> None:
        """Log an error message."""
        self.messages.append(message)
        self.levels.append("ERROR")
    
    def warning(self, message: str) -> None:
        """Log a warning message."""
        self.messages.append(message)
        self.levels.append("WARNING")
    
    def info(self, message: str) -> None:
        """Log an informational message."""
        self.messages.append(message)
        self.levels.append("INFO")
    
    def debug(self, message: str) -> None:
        """Log a debug message."""
        self.messages.append(message)
        self.levels.append("DEBUG")

class FullCardProcessor(CardProcessorInterface):
    """Complete implementation of CardProcessorInterface protocol for testing."""
    
    def process_card(
        self,
        card_data: dict,
        filters: Optional[Dict[str, Any]] = None,
        schema: Optional[List[str]] = None,
        additional_languages: Optional[List[str]] = None,
    ) -> Optional[dict]:
        """Process a single card according to specified criteria."""
        if not card_data:
            return None
        
        result = card_data.copy()
        
        # Apply schema
        if schema:
            result = {k: v for k, v in result.items() if k in schema}
        
        # Apply filters
        if filters:
            for key, value in filters.items():
                if key not in result or result[key] != value:
                    return None
        
        # Apply additional languages
        if additional_languages and 'languages' in card_data:
            result['translations'] = {
                lang: card_data.get(f'translation_{lang}', f'Default {lang} translation')
                for lang in additional_languages
                if lang in card_data['languages']
            }
        
        return result

class FullFileHandler(FileHandlerInterface):
    """Complete implementation of FileHandlerInterface protocol for testing."""
    
    def __init__(self):
        self.files: Dict[str, bytes] = {}
    
    def validate_input_file(self, filepath: str, max_size_mb: Optional[int] = None) -> bool:
        """Validate an input file exists and meets size constraints."""
        if filepath not in self.files:
            raise FileNotFoundError(f"File not found: {filepath}")
        
        if max_size_mb is not None:
            size_mb = len(self.files[filepath]) / (1024 * 1024)
            if size_mb > max_size_mb:
                raise ValueError(f"File too large: {size_mb:.2f}MB > {max_size_mb}MB")
        
        return True
    
    def open_file(self, filepath: str, mode: str = 'r', encoding: str = 'utf-8', buffering: Optional[int] = None) -> IO[Any]:
        """Open a file with specified parameters."""
        if 'w' in mode:
            # Create new file or truncate existing file
            if 'b' in mode:
                bio = BytesIO()
                def close_hook():
                    self.files[filepath] = bio.getvalue()
                bio.close = close_hook
                return bio
            else:
                sio = StringIO()
                def close_hook():
                    self.files[filepath] = sio.getvalue().encode(encoding)
                sio.close = close_hook
                return sio
        
        if filepath not in self.files:
            raise FileNotFoundError(f"File not found: {filepath}")
        
        if 'b' in mode:
            return BytesIO(self.files[filepath])
        else:
            return StringIO(self.files[filepath].decode(encoding))

def test_logger_protocol():
    """Test full implementation of LoggingInterface protocol."""
    logger = FullLogger()
    
    # Test all logging methods with docstrings
    logger.error("Error message")  # Test error method
    logger.warning("Warning message")  # Test warning method
    logger.info("Info message")  # Test info method
    logger.debug("Debug message")  # Test debug method
    
    # Verify all messages were logged
    assert len(logger.messages) == 4
    assert len(logger.levels) == 4
    assert logger.levels == ["ERROR", "WARNING", "INFO", "DEBUG"]
    assert "Error message" in logger.messages[0]
    assert "Warning message" in logger.messages[1]
    assert "Info message" in logger.messages[2]
    assert "Debug message" in logger.messages[3]

def test_card_processor_protocol():
    """Test full implementation of CardProcessorInterface protocol."""
    processor = FullCardProcessor()
    
    # Test with all optional parameters
    card_data = {
        "name": "Test Card",
        "type": "Creature",
        "languages": ["en", "jp", "de"],
        "translation_jp": "テストカード",
        "translation_de": "Testkarte"
    }
    
    result = processor.process_card(
        card_data=card_data,
        filters={"type": "Creature"},
        schema=["name", "type"],
        additional_languages=["jp", "de"]
    )
    
    assert result is not None
    assert result["name"] == "Test Card"
    assert result["type"] == "Creature"
    assert "translations" in result
    
    # Test with no optional parameters
    result = processor.process_card(card_data)
    assert result == card_data
    
    # Test with empty card data
    assert processor.process_card({}) is None

def test_file_handler_protocol():
    """Test full implementation of FileHandlerInterface protocol."""
    handler = FullFileHandler()
    
    # Test file validation
    with pytest.raises(FileNotFoundError):
        handler.validate_input_file("nonexistent.txt")
    
    # Test file operations with different modes and encodings
    text_file = handler.open_file("test.txt", mode='w', encoding='utf-8')
    text_file.write("Hello, World!")
    text_file.close()
    
    # Test validation with size limits
    assert handler.validate_input_file("test.txt") is True
    assert handler.validate_input_file("test.txt", max_size_mb=1) is True
    
    with pytest.raises(ValueError):
        handler.validate_input_file("test.txt", max_size_mb=0)
    
    # Test reading with different modes
    text_file = handler.open_file("test.txt", mode='r', encoding='utf-8')
    assert text_file.read() == "Hello, World!"
    
    binary_file = handler.open_file("test.txt", mode='rb')
    assert binary_file.read() == b"Hello, World!"
    
    # Test with buffering parameter
    buffered_file = handler.open_file("test.txt", mode='r', buffering=4096)
    assert buffered_file.read() == "Hello, World!"
