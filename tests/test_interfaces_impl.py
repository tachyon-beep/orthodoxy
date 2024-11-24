"""Tests for concrete implementations of protocol interfaces."""

import pytest
from typing import Optional, Dict, Any, List
from src.utils.interfaces import LoggingInterface, CardProcessorInterface, FileHandlerInterface
from pathlib import Path
from io import StringIO

class ConcreteLogger(LoggingInterface):
    """Concrete implementation of LoggingInterface protocol for testing."""
    
    def __init__(self):
        self.messages = []
    
    def error(self, message: str) -> None:
        self.messages.append(("ERROR", message))
    
    def warning(self, message: str) -> None:
        self.messages.append(("WARNING", message))
    
    def info(self, message: str) -> None:
        self.messages.append(("INFO", message))
    
    def debug(self, message: str) -> None:
        self.messages.append(("DEBUG", message))

class ConcreteCardProcessor(CardProcessorInterface):
    """Concrete implementation of CardProcessorInterface protocol for testing."""
    
    def process_card(
        self,
        card_data: dict,
        filters: Optional[Dict[str, Any]] = None,
        schema: Optional[List[str]] = None,
        additional_languages: Optional[List[str]] = None,
    ) -> Optional[dict]:
        if not card_data:
            return None
            
        result = {}
        
        # Apply schema if provided
        if schema:
            for field in schema:
                if field in card_data:
                    result[field] = card_data[field]
        else:
            result = card_data.copy()
        
        # Apply filters if provided
        if filters:
            for key, value in filters.items():
                if key in result and result[key] != value:
                    return None
        
        # Add additional languages if provided
        if additional_languages and 'languages' in card_data:
            result['translations'] = {
                lang: f"Translation for {lang}"
                for lang in additional_languages
                if lang in card_data['languages']
            }
        
        return result

class ConcreteFileHandler(FileHandlerInterface):
    """Concrete implementation of FileHandlerInterface protocol for testing."""
    
    def __init__(self, max_default_size_mb: int = 10):
        self.max_default_size_mb = max_default_size_mb
    
    def validate_input_file(self, filepath: str, max_size_mb: Optional[int] = None) -> bool:
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
            
        max_size = max_size_mb if max_size_mb is not None else self.max_default_size_mb
        size_mb = path.stat().st_size / (1024 * 1024)
        
        if size_mb > max_size:
            raise ValueError(f"File too large: {size_mb:.2f}MB > {max_size}MB")
        
        return True
    
    def open_file(self, filepath: str, mode: str = 'r', encoding: str = 'utf-8', buffering: Optional[int] = None) -> StringIO:
        if not Path(filepath).exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        return StringIO()

def test_concrete_logger():
    """Test concrete implementation of LoggingInterface protocol."""
    logger = ConcreteLogger()
    
    # Test all logging methods
    logger.error("error message")
    logger.warning("warning message")
    logger.info("info message")
    logger.debug("debug message")
    
    # Verify messages were logged correctly
    assert len(logger.messages) == 4
    assert logger.messages[0] == ("ERROR", "error message")
    assert logger.messages[1] == ("WARNING", "warning message")
    assert logger.messages[2] == ("INFO", "info message")
    assert logger.messages[3] == ("DEBUG", "debug message")

def test_concrete_card_processor():
    """Test concrete implementation of CardProcessorInterface protocol."""
    processor = ConcreteCardProcessor()
    
    # Test basic card processing
    card_data = {
        "name": "Test Card",
        "cost": "2B",
        "type": "Creature",
        "languages": ["en", "jp", "de"]
    }
    
    # Test with no filters or schema
    result = processor.process_card(card_data)
    assert result == card_data
    
    # Test with schema
    schema = ["name", "type"]
    result = processor.process_card(card_data, schema=schema)
    assert result == {"name": "Test Card", "type": "Creature"}
    
    # Test with filters
    filters = {"type": "Creature"}
    result = processor.process_card(card_data, filters=filters)
    assert result == card_data
    
    filters = {"type": "Instant"}
    result = processor.process_card(card_data, filters=filters)
    assert result is None
    
    # Test with additional languages
    result = processor.process_card(
        card_data,
        additional_languages=["jp", "de"]
    )
    assert result is not None  # Fixed: Check result is not None before accessing
    assert "translations" in result
    assert len(result["translations"]) == 2
    
    # Test with empty card data
    result = processor.process_card({})
    assert result is None

def test_concrete_file_handler(tmp_path):
    """Test concrete implementation of FileHandlerInterface protocol."""
    handler = ConcreteFileHandler()
    
    # Create test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")
    
    # Test file validation
    assert handler.validate_input_file(str(test_file)) is True
    
    # Test file validation with custom size limit
    assert handler.validate_input_file(str(test_file), max_size_mb=1) is True
    
    # Test non-existent file
    with pytest.raises(FileNotFoundError):
        handler.validate_input_file("nonexistent.txt")
    
    # Test file opening
    file_obj = handler.open_file(str(test_file))
    assert isinstance(file_obj, StringIO)
    
    # Test file opening with different modes
    file_obj = handler.open_file(str(test_file), mode='r', encoding='utf-8')
    assert isinstance(file_obj, StringIO)
    
    # Test file opening non-existent file
    with pytest.raises(FileNotFoundError):
        handler.open_file("nonexistent.txt")
