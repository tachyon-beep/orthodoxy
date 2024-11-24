"""Exceptions for card filtering operations.

This module defines custom exceptions used throughout the card filtering system
to handle various error conditions in a structured way. It provides a hierarchical
exception system that enables granular error handling and detailed error reporting.

Features:
- Hierarchical exception structure for specific error types
- Detailed error messages with context preservation
- Type-specific exceptions with validation details
- Comprehensive error handling with recovery options
- Error context preservation for debugging

Exception Hierarchy:
- CardFilterError (base)
  |- InvalidFilterError (filter validation)
  |- SchemaValidationError (data validation)
  |- CardProcessingError (card processing)
  |- BatchProcessingError (batch processing)

Example:
    Basic error handling with type checking:
    ```python
    from orthodoxy.errors import CardFilterError, InvalidFilterError
    
    def process_deck(deck_data):
        try:
            # Process deck with type-safe filters
            process_cards(deck_data, filters={
                "colors": {"contains": "R"},
                "convertedManaCost": {"lte": 3}  # Numeric comparison
            })
            
        except InvalidFilterError as e:
            print(f"Filter validation failed: {e}")
            if e.filter_data:  # Access invalid filter data
                print(f"Invalid filter: {e.filter_data}")
            
        except CardFilterError as e:
            print(f"General processing error: {e}")
            # Handle any other card filtering error
            
        except Exception as e:
            print(f"Unexpected error: {e}")
            # Handle unexpected errors
    ```

Note:
    All exceptions include detailed error messages and preserve context
    information to help identify the specific cause of the error. When
    raising these exceptions, always provide clear, descriptive messages
    and relevant error context.
"""

from typing import Optional, Dict, Any


class CardFilterError(Exception):
    """Base exception for card filtering errors.
    
    This is the parent class for all card filtering related exceptions.
    It provides a common base for catching any card filtering error and
    includes support for detailed error messages and context preservation.

    Features:
    - Common base for all filtering errors
    - Detailed error message support
    - Error context preservation
    - Type-safe error handling

    Example:
        Catching and handling specific error types:
        ```python
        try:
            # Process a batch of cards with validation
            for card in cards:
                process_card(card)
                
        except CardFilterError as e:
            logger.error(f"Card processing failed: {e}")
            # Handle the error appropriately based on type
            if isinstance(e, InvalidFilterError):
                # Handle filter-specific error with context
                logger.debug(f"Invalid filter data: {e.filter_data}")
                fix_filters()
            elif isinstance(e, SchemaValidationError):
                # Handle schema validation error with field info
                logger.debug(f"Invalid field: {e.field_name}")
                fix_schema()
            else:
                # Handle other card processing errors
                report_error()
        ```

    Attributes:
        message (str): Detailed error message explaining the cause
        
    Note:
        When creating custom exceptions, inherit from this class and
        provide specific error handling logic and context preservation
        as needed for the specific error type.
    """
    def __init__(self, message: str = "An error occurred during card filtering"):
        """Initialize the exception with a detailed message.
        
        Args:
            message (str): Detailed error message explaining the cause.
                Defaults to a generic message.
        """
        self.message = message
        super().__init__(self.message)


class InvalidFilterError(CardFilterError):
    """Raised when filter conditions are invalid or malformed.
    
    This exception is raised when filter conditions fail validation,
    providing detailed information about the specific validation failure
    and preserving the invalid filter data for debugging.
    
    Common validation failures:
    - Unknown or invalid filter operators
    - Type mismatches in filter values
    - Syntactically invalid filter conditions
    - Missing required filter fields
    - Operator and value type incompatibility
    
    Example:
        Handling specific filter validation errors:
        ```python
        try:
            # Apply type-checked filters
            filtered_cards = apply_filters(cards, {
                "colors": {"contains": "R"},
                "convertedManaCost": {"invalid_op": 3}  # Invalid operator
            })
            
        except InvalidFilterError as e:
            if "invalid operator" in str(e).lower():
                print(f"Invalid operator used: {e}")
                # Show valid operators from error context
                if e.filter_data:
                    print(f"Invalid filter was: {e.filter_data}")
                print("Valid operators are: contains, equals, gt, lt, etc.")
            else:
                print(f"Filter validation failed: {e}")
                
        # Example of type mismatch handling
        try:
            apply_filters(cards, {
                "convertedManaCost": {"gt": "not_a_number"}  # Type mismatch
            })
            
        except InvalidFilterError as e:
            print(f"Invalid value type: {e}")
            if e.filter_data:
                print(f"Problematic filter: {e.filter_data}")
            # Handle type mismatch with proper conversion
        ```

    Attributes:
        message (str): Detailed error message explaining the validation failure
        filter_data (Optional[Dict[str, Any]]): The invalid filter data that
            caused the error, preserved for debugging
        
    Note:
        When raising this exception, always provide specific details about
        what made the filter invalid to help users correct the issue.
        Include the invalid filter data when possible to aid debugging.
    """
    def __init__(self, message: str, filter_data: Optional[Dict[str, Any]] = None):
        """Initialize the exception with error details and context.
        
        Args:
            message (str): Detailed error message explaining the validation failure
            filter_data (Optional[Dict[str, Any]], optional): The invalid filter
                data that caused the error. Defaults to None.
        
        Example:
            ```python
            invalid_filter = {"colors": {"invalid_op": "R"}}
            raise InvalidFilterError(
                "Unknown operator 'invalid_op' for colors filter",
                filter_data=invalid_filter
            )
            ```
        """
        self.filter_data = filter_data
        super().__init__(message)


class SchemaValidationError(CardFilterError):
    """Raised when card data fails schema validation.
    
    This exception is raised when card data doesn't conform to the
    expected schema, providing detailed information about the validation
    failure including field names, expected types, and actual values.
    
    Common validation failures:
    - Missing required fields
    - Invalid field types
    - Field value constraint violations
    - Schema format errors
    - Type conversion failures
    
    Example:
        Handling schema validation with type checking:
        ```python
        try:
            # Validate card against typed schema
            validate_card_schema(card_data, schema={
                "name": {"type": "string", "required": True},
                "convertedManaCost": {"type": "number", "min": 0}
            })
            
        except SchemaValidationError as e:
            if "required field" in str(e).lower():
                print(f"Missing required field: {e}")
                if e.field_name:
                    print(f"Field '{e.field_name}' is required")
                print("Required fields are: name, type")
            elif e.expected_type:
                print(f"Type mismatch: expected {e.expected_type}")
                if e.actual_value is not None:
                    print(f"Got value: {e.actual_value}")
            else:
                print(f"Schema validation failed: {e}")
                
        # Example of type validation with context
        try:
            validate_card_schema(card_data, schema={
                "power": {"type": "number"}
            })
            
        except SchemaValidationError as e:
            print(f"Invalid field type: {e}")
            if e.field_name and e.expected_type:
                print(f"Field '{e.field_name}' must be {e.expected_type}")
            # Handle type validation error with context
        ```

    Attributes:
        message (str): Detailed error message explaining the validation failure
        field_name (Optional[str]): The name of the field that failed validation
        expected_type (Optional[str]): The expected type of the field
        actual_value (Optional[Any]): The actual value that failed validation
    """
    def __init__(
        self,
        message: str,
        field_name: Optional[str] = None,
        expected_type: Optional[str] = None,
        actual_value: Optional[Any] = None
    ):
        """Initialize the exception with validation details and context.
        
        Args:
            message (str): Detailed error message explaining the validation failure
            field_name (Optional[str], optional): The name of the field that
                failed validation. Defaults to None.
            expected_type (Optional[str], optional): The expected type of the
                field. Defaults to None.
            actual_value (Optional[Any], optional): The actual value that
                failed validation. Defaults to None.
            
        Example:
            ```python
            raise SchemaValidationError(
                "Invalid type for 'power' field",
                field_name="power",
                expected_type="number",
                actual_value="N/A"
            )
            ```
        """
        self.field_name = field_name
        self.expected_type = expected_type
        self.actual_value = actual_value
        super().__init__(message)


class CardProcessingError(CardFilterError):
    """Raised when an error occurs during individual card processing.
    
    This exception is raised when processing a single card fails, providing
    detailed information about the specific processing failure. It helps
    distinguish card-level processing errors from other types of errors
    in the system.
    
    Common processing failures:
    - Invalid card data format
    - Missing required card fields
    - Data transformation errors
    - Field validation failures
    - Processing timeout issues
    
    Example:
        Handling card processing errors:
        ```python
        try:
            # Process a single card
            processed_card = process_card(card_data)
            
        except CardProcessingError as e:
            logger.error(f"Failed to process card: {e}")
            # Handle the card processing error
            if "timeout" in str(e).lower():
                retry_with_longer_timeout()
            else:
                skip_card_and_continue()
        ```
    
    Attributes:
        message (str): Detailed error message explaining the processing failure
    """
    def __init__(self, message: str = "An error occurred during card processing"):
        """Initialize the exception with error details.
        
        Args:
            message (str): Detailed error message explaining the processing failure.
                Defaults to a generic message.
            
        Example:
            ```python
            raise CardProcessingError(
                "Failed to process card 'Black Lotus': invalid mana cost format"
            )
            ```
        """
        super().__init__(message)


class BatchProcessingError(CardFilterError):
    """Raised when an error occurs during batch processing operations.
    
    This exception is raised when processing a batch of cards fails at the
    batch level, rather than individual card level. It helps distinguish
    batch-wide issues from card-specific problems.
    
    Common batch processing failures:
    - Resource allocation errors
    - Parallel processing failures
    - Batch size validation issues
    - Memory management problems
    - Timeout on batch operations
    
    Example:
        Handling batch processing errors:
        ```python
        try:
            # Process a batch of cards
            processed_batch = process_card_batch(cards)
            
        except BatchProcessingError as e:
            logger.error(f"Batch processing failed: {e}")
            # Handle the batch processing error
            if "memory" in str(e).lower():
                reduce_batch_size_and_retry()
            else:
                handle_batch_failure()
        ```
    
    Attributes:
        message (str): Detailed error message explaining the batch processing failure
    """
    def __init__(self, message: str = "An error occurred during batch processing"):
        """Initialize the exception with error details.
        
        Args:
            message (str): Detailed error message explaining the batch processing
                failure. Defaults to a generic message.
            
        Example:
            ```python
            raise BatchProcessingError(
                "Failed to process batch: insufficient memory for parallel processing"
            )
            ```
        """
        super().__init__(message)
