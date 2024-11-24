"""Common interfaces and protocols used across the application.

This module provides shared protocol definitions and interfaces that are used
by multiple components throughout the application. These protocols define
standard interfaces that ensure consistency and interoperability between
different parts of the system.

Features:
- LoggingInterface protocol for consistent logging interface
- Card processing protocols for handling MTG card data
- File handling protocols for consistent I/O operations
- Type hints and documentation for all interfaces

Example:
    Basic logger implementation:
    ```python
    class ConsoleLogger:
        def error(self, message: str) -> None:
            print(f"ERROR: {message}")
            
        def warning(self, message: str) -> None:
            print(f"WARNING: {message}")
            
        def info(self, message: str) -> None:
            print(f"INFO: {message}")
            
        def debug(self, message: str) -> None:
            print(f"DEBUG: {message}")
    ```

    Using protocols in type hints:
    ```python
    def process_cards(processor: CardProcessorInterface, logger: LoggingInterface) -> None:
        try:
            result = processor.process_card(card_data, filters=None)
            logger.info(f"Processed card: {result}")
        except Exception as e:
            logger.error(f"Processing failed: {e}")
    ```
"""

from typing import Protocol, Any, Optional, Dict, List, IO, Union


class LoggingInterface(Protocol):
    """Protocol defining the standard logging interface used across the application.
    
    This protocol ensures consistent logging behavior throughout the application
    by defining a standard interface that all logging implementations must follow.
    It supports different log levels (error, warning, info, debug) for appropriate
    message categorization.

    Example:
        ```python
        class FileLogger(LoggingInterface):
            def __init__(self, log_file: str):
                self.log_file = log_file
                
            def error(self, message: str) -> None:
                with open(self.log_file, 'a') as f:
                    f.write(f"ERROR: {message}\\n")
                    
            def warning(self, message: str) -> None:
                with open(self.log_file, 'a') as f:
                    f.write(f"WARNING: {message}\\n")
                    
            def info(self, message: str) -> None:
                with open(self.log_file, 'a') as f:
                    f.write(f"INFO: {message}\\n")
                    
            def debug(self, message: str) -> None:
                with open(self.log_file, 'a') as f:
                    f.write(f"DEBUG: {message}\\n")
        
        # Usage
        logger = FileLogger("app.log")
        logger.error("Failed to process card")
        ```
    """
    def error(self, message: str) -> None:
        """Log an error message.
        
        Args:
            message (str): The error message to log. Should be descriptive
                and include relevant error details.
        """
        ...

    def warning(self, message: str) -> None:
        """Log a warning message.
        
        Args:
            message (str): The warning message to log. Should describe potential
                issues that don't prevent operation but require attention.
        """
        ...

    def info(self, message: str) -> None:
        """Log an informational message.
        
        Args:
            message (str): The info message to log. Should provide useful
                information about normal operation progress.
        """
        ...

    def debug(self, message: str) -> None:
        """Log a debug message.
        
        Args:
            message (str): The debug message to log. Can include detailed
                technical information useful for debugging.
        """
        ...


class CardProcessorInterface(Protocol):
    """Protocol defining the interface for card processing components.
    
    This protocol establishes a standard interface for components that process
    Magic: The Gathering card data. It supports filtering, field selection,
    and multi-language capabilities.

    Example:
        ```python
        class StandardCardProcessor:
            def process_card(
                self,
                card_data: dict,
                filters: Optional[Dict[str, Any]] = None,
                schema: Optional[List[str]] = None,
                additional_languages: Optional[List[str]] = None,
            ) -> Optional[dict]:
                # Apply filters
                if filters and not self._matches_filters(card_data, filters):
                    return None
                    
                # Apply schema
                if schema:
                    result = {k: card_data[k] for k in schema if k in card_data}
                else:
                    result = card_data.copy()
                    
                # Add languages if requested
                if additional_languages:
                    result['foreignData'] = self._get_foreign_data(
                        card_data,
                        additional_languages
                    )
                    
                return result
        
        # Usage
        processor = StandardCardProcessor()
        result = processor.process_card(
            card_data={"name": "Lightning Bolt", "colors": ["R"]},
            filters={"colors": {"contains": "R"}},
            schema=["name", "colors"]
        )
        ```
    """
    def process_card(
        self,
        card_data: dict,
        filters: Optional[Dict[str, Any]],
        schema: Optional[List[str]],
        additional_languages: Optional[List[str]],
    ) -> Optional[dict]:
        """Process a single card according to specified criteria.
        
        Args:
            card_data (dict): Raw card data to process. Should contain all
                standard MTG card fields.
            filters (Optional[Dict[str, Any]]): Filter conditions to apply.
                Format: {"field": {"operator": value}}
            schema (Optional[List[str]]): List of fields to include in output.
                If None, includes all fields.
            additional_languages (Optional[List[str]]): List of language codes
                to include in foreign data.
            
        Returns:
            Optional[dict]: Processed card data if it matches filters,
                None if filtered out.
            
        Example:
            ```python
            result = processor.process_card(
                card_data={
                    "name": "Counterspell",
                    "colors": ["U"],
                    "convertedManaCost": 2
                },
                filters={"colors": {"contains": "U"}},
                schema=["name", "convertedManaCost"],
                additional_languages=["Japanese", "German"]
            )
            ```
        """
        ...


class FileHandlerInterface(Protocol):
    """Protocol defining the interface for file handling components.
    
    This protocol establishes a standard interface for components that handle
    file operations, ensuring consistent file handling across the application.
    It includes validation and safe file operations.

    Example:
        ```python
        class SafeFileHandler:
            def validate_input_file(
                self,
                filepath: str,
                max_size_mb: Optional[int] = None
            ) -> bool:
                if not os.path.exists(filepath):
                    return False
                    
                if max_size_mb:
                    size_mb = os.path.getsize(filepath) / (1024 * 1024)
                    if size_mb > max_size_mb:
                        return False
                        
                return True
                
            def open_file(
                self,
                filepath: str,
                mode: str = 'r',
                encoding: str = 'utf-8',
                buffering: Optional[int] = None
            ) -> IO[Any]:
                return open(
                    filepath,
                    mode=mode,
                    encoding=encoding,
                    buffering=buffering
                )
        
        # Usage
        handler = SafeFileHandler()
        if handler.validate_input_file("cards.json", max_size_mb=100):
            with handler.open_file("cards.json", "r") as f:
                data = json.load(f)
        ```
    """
    def validate_input_file(self, filepath: str, max_size_mb: Optional[int] = None) -> bool:
        """Validate an input file exists and meets size constraints.
        
        Args:
            filepath (str): Path to the file to validate
            max_size_mb (Optional[int]): Optional maximum file size in megabytes.
                If None, no size limit is enforced.
            
        Returns:
            bool: True if file is valid and meets all criteria,
                False otherwise.
            
        Example:
            ```python
            handler = FileHandlerInterface()
            if handler.validate_input_file("large_file.json", max_size_mb=100):
                print("File is valid and within size limits")
            else:
                print("File is invalid or too large")
            ```
        """
        ...

    def open_file(self, filepath: str, mode: str = 'r', encoding: str = 'utf-8', buffering: Optional[int] = None) -> IO[Any]:
        """Open a file with specified parameters.
        
        Args:
            filepath (str): Path to the file to open
            mode (str): File open mode ('r', 'w', etc.)
            encoding (str): File encoding (default: 'utf-8')
            buffering (Optional[int]): Optional buffer size
            
        Returns:
            IO[Any]: Opened file object
            
        Raises:
            IOError: If file cannot be opened
            
        Example:
            ```python
            handler = FileHandlerInterface()
            try:
                with handler.open_file("data.txt", "r") as f:
                    content = f.read()
            except IOError as e:
                print(f"Failed to open file: {e}")
            ```
        """
        ...
