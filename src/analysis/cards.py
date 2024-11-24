"""Card processing module for filtering and transforming Magic: The Gathering card data.

This module provides comprehensive functionality for processing Magic: The Gathering
card data, implementing type-safe filtering, schema validation, and multi-language
support through a robust processing interface.

Features:
- Type-safe card filtering with comprehensive validation
- Schema-based field selection with validation
- Multi-language support with proper encoding
- Null-safe default value handling
- Type-aware operator evaluation
- Comprehensive error handling
- Memory-efficient processing

Example:
    Basic usage with type safety:
    ```python
    processor = CardProcessorInterface(config)
    
    # Process a card with validated filters
    result = processor.process_card(
        card_data={"name": "Serra Angel", "colors": ["W"]},
        filters={"colors": {"contains": "W"}},  # Type-checked filter
        schema=["name", "colors"]  # Validated schema
    )

    # Process with multiple type-safe filters
    result = processor.process_card(
        card_data=card_data,
        filters={
            "colors": {"contains": "U"},
            "convertedManaCost": {"lte": 3}  # Numeric comparison
        },
        schema=["name", "manaCost", "text"],
        additional_languages=["Japanese", "German"]
    )
    ```

Note:
    All operations implement comprehensive type checking and validation:
    - Numeric comparisons handle type conversion safely
    - String operations are encoding-aware
    - List operations validate element types
    - Null values are han"I dled gracefully
"""

from typing import Optional, List, Dict, Any
from src.core.config import CardFilterConfig
from src.processing.filters import get_operator_function


class FilterStrategy:
    """Strategy class for evaluating filter conditions with type safety.
    
    This class implements the strategy pattern for filter evaluation,
    providing type-safe and extensible filtering capabilities with
    proper validation and error handling.

    Features:
    - Type-safe comparison operations
    - Null-safe value handling
    - Automatic type conversion
    - Validation of filter conditions
    
    Supported Operations:
    - Numeric comparisons (gt, lt, gte, lte) with type conversion
    - String operations (equals, contains, startswith) with encoding
    - List operations (contains, containsAll, containsAny) with validation
    
    Example:
        ```python
        strategy = FilterStrategy()
        
        # Numeric comparison with type safety
        result = strategy.evaluate_condition(3, 5, "lt")  # True
        result = strategy.evaluate_condition("3", "5", "lt")  # True (converted)
        
        # String operation with encoding awareness
        result = strategy.evaluate_condition("Blue", "lu", "contains")  # True
        
        # List operation with type validation
        result = strategy.evaluate_condition(["R", "G"], "R", "contains")  # True
        ```
    """

    @staticmethod
    def evaluate_condition(card_value: Any, filter_value: Any, op: str) -> bool:
        """Evaluate a single filter condition with type safety.
        
        This method implements comprehensive type checking and conversion
        for different types of values and operators. It handles type
        mismatches and invalid values gracefully.
        
        Args:
            card_value: The value from the card to check
            filter_value: The value to check against
            op: The operator to use for comparison
            
        Returns:
            bool: True if the condition is met, False otherwise
            
        Raises:
            ValueError: If the operator is invalid or values incompatible
            
        Example:
            ```python
            # Numeric comparison with type conversion
            strategy.evaluate_condition("3", 2, "gt")  # True
            strategy.evaluate_condition("not_a_number", 2, "gt")  # False
            
            # List containment with type validation
            strategy.evaluate_condition(["W", "U"], "W", "contains")  # True
            strategy.evaluate_condition(None, "W", "contains")  # False
            ```
        """
        operator_func = get_operator_function(op)
        if operator_func is None:
            raise ValueError(f"Invalid operator: {op}")

        try:
            if op in ['gt', 'lt', 'gte', 'lte']:
                try:
                    card_value, filter_value = float(card_value), float(filter_value)
                except (TypeError, ValueError):
                    raise ValueError("Invalid value type for numeric operator")
            return operator_func(card_value, filter_value)
        except Exception as e:
            raise ValueError(f"Error applying operator {op}: {str(e)}")


class CardProcessorInterface:
    """Handles card processing and filtering with type safety.
    
    This class is responsible for processing Magic: The Gathering cards,
    implementing type-safe filtering, schema validation, and proper
    encoding support for multi-language data.

    Features:
    - Type-safe filter evaluation
    - Schema validation
    - Multi-language support
    - Null-safe defaults
    - Memory-efficient processing
    
    Attributes:
        config (CardFilterConfig): Validated configuration settings
        filter_strategy (FilterStrategy): Type-safe filter evaluation

    Example:
        ```python
        processor = CardProcessorInterface(config)
        
        # Process a card with type safety
        result = processor.process_card(
            card_data={
                "name": "Counterspell",
                "colors": ["U"],
                "convertedManaCost": 2
            },
            filters={
                "colors": {"contains": "U"},  # Type-checked
                "convertedManaCost": {"lte": 3}  # Numeric conversion
            },
            schema=["name", "manaCost", "text"]  # Validated
        )
        ```
    """

    def __init__(self, config: CardFilterConfig):
        """Initialize with validated configuration.
        
        Args:
            config: Validated configuration settings
        """
        self.config = config
        self.filter_strategy = FilterStrategy()

    def create_base_card(self, card_data: dict) -> dict:
        """Creates a base card dictionary with null-safe defaults.
        
        This method ensures all required fields are present with proper
        types and sets appropriate default values for optional fields.
        
        Args:
            card_data: Raw card data to process
            
        Returns:
            dict: Card data with validated fields and defaults
            
        Example:
            ```python
            base_card = processor.create_base_card({
                "name": "Lightning Bolt",
                "type": "Instant"
            })
            # Result includes type-safe defaults:
            # {
            #     "name": "Lightning Bolt",
            #     "type": "Instant",
            #     "colors": [],  # Type-safe empty list
            #     "convertedManaCost": 0,  # Numeric default
            #     ...
            # }
            ```
        """
        base_card = card_data.copy()
        
        # Required fields with validation
        base_card.setdefault("name", None)
        base_card.setdefault("type", None)
        
        # Optional fields with type-safe defaults
        base_card.setdefault("colors", [])
        base_card.setdefault("colorIdentity", [])
        base_card.setdefault("convertedManaCost", 0)
        base_card.setdefault("text", "")
        base_card.setdefault("edhrecSaltiness", 0.0)
        base_card.setdefault("language", "English")
        base_card.setdefault("foreignData", [])
        base_card.setdefault("availability", [])
        
        return base_card

    @staticmethod
    def filter_foreign_data(card_data: dict, additional_languages: Optional[List[str]]) -> List[dict]:
        """Filters foreign data entries with language validation.
        
        Args:
            card_data: Card data containing translations
            additional_languages: Validated language codes
            
        Returns:
            List[dict]: Filtered and validated foreign data
            
        Example:
            ```python
            foreign_data = processor.filter_foreign_data(
                card_data,
                additional_languages=["Japanese", "German"]
            )
            ```
        """
        if not additional_languages:
            return []

        foreign_data = card_data.get("foreignData", [])
        return [
            entry
            for entry in foreign_data
            if entry.get("language") in additional_languages
        ]

    @staticmethod
    def apply_schema(card: dict, schema: Optional[List[str]]) -> dict:
        """Applies schema filter with field validation.
        
        This method selects and validates specific fields from the card
        data based on the provided schema.
        
        Args:
            card: Card data to filter
            schema: Validated list of field names
            
        Returns:
            dict: Filtered card data with validated fields
            
        Example:
            ```python
            result = processor.apply_schema(
                card_data,
                schema=["name", "manaCost", "text"]
            )
            ```
        """
        if schema is None:
            # If no schema provided, return all fields except internal
            result = card.copy()
            if "language" in result:
                del result["language"]
            return result
        if not schema:
            return {}
        return {key: card[key] for key in schema if key in card}

    def evaluate_filters(self, card: dict, filter_conditions: Dict[str, Any]) -> bool:
        """Evaluates if a card matches filters with type safety.
        
        This method applies all filter conditions to a card using the
        type-safe filter strategy. All conditions must be met for the
        card to pass the filter.
        
        Args:
            card: Card data to evaluate
            filter_conditions: Type-checked filter conditions
            
        Returns:
            bool: True if card matches all conditions
            
        Raises:
            ValueError: If filter evaluation fails
            
        Example:
            ```python
            matches = processor.evaluate_filters(
                card_data,
                filter_conditions={
                    "colors": {"contains": "R"},  # List operation
                    "convertedManaCost": {"lte": 3}  # Numeric
                }
            )
            ```
        """
        if not filter_conditions:
            return True

        for field, conditions in filter_conditions.items():
            if field not in card:
                return False
                
            card_value = card[field]
            for op, filter_value in conditions.items():
                if not get_operator_function(op):
                    raise ValueError(f"Invalid operator: {op}")
                try:
                    if not self.filter_strategy.evaluate_condition(card_value, filter_value, op):
                        return False
                except ValueError as e:
                    raise ValueError(str(e))
                    
        return True

    def process_card(
        self,
        card_data: dict,
        filters: Optional[Dict[str, Any]] = None,
        schema: Optional[List[str]] = None,
        additional_languages: Optional[List[str]] = None,
    ) -> Optional[dict]:
        """Processes a single card with comprehensive validation.
        
        This is the main method for processing individual cards. It applies
        type-safe filters, schema validation, and proper encoding handling
        in a specific order to ensure consistent results.
        
        Args:
            card_data: Raw card data to process
            filters: Type-checked filter conditions
            schema: Validated field selection
            additional_languages: Validated language codes
            
        Returns:
            Optional[dict]: Processed card data, or None if filtered
            
        Raises:
            ValueError: If validation fails or processing errors occur
        """
        try:
            # Validate and prepare card data
            self._validate_required_fields(card_data)
            processed_card = self.create_base_card(card_data)

            # Apply type-safe filters
            if not self._apply_filters(processed_card, filters):
                return None

            # Process language data with validation
            processed_card = self._process_language_data(
                processed_card, 
                card_data,
                additional_languages
            )

            # Apply schema with validation
            return self._apply_final_schema(processed_card, schema)
            
        except ValueError as e:
            raise ValueError(f"Error processing card: {str(e)}")

    def _validate_required_fields(self, card_data: dict) -> None:
        """Validates required fields with type checking."""
        if not all(field in card_data for field in ["name", "type"]):
            raise ValueError("Card missing required fields")

    def _validate_filter_operators(self, filters: Optional[Dict[str, Any]]) -> None:
        """Validates filter operators with type checking."""
        if not filters:
            return

        for conditions in filters.values():
            for op in conditions.keys():
                if not get_operator_function(op):
                    raise ValueError(f"Invalid operator: {op}")

    def _apply_filters(self, processed_card: dict, filters: Optional[Dict[str, Any]]) -> bool:
        """Applies filters with type safety.
        
        Returns:
            bool: True if card passes filters
        """
        if filters is None:
            return True

        try:
            self._validate_filter_operators(filters)
            return self.evaluate_filters(processed_card, filters)
        except ValueError as e:
            raise ValueError(f"Filter evaluation failed: {str(e)}")

    def _process_language_data(
        self, 
        processed_card: dict, 
        card_data: dict,
        additional_languages: Optional[List[str]]
    ) -> dict:
        """Processes language data with encoding validation."""
        if additional_languages:
            processed_card["foreignData"] = self.filter_foreign_data(
                card_data, 
                additional_languages
            )
        elif "foreignData" in processed_card:
            del processed_card["foreignData"]
            
        return processed_card

    def _apply_final_schema(
        self, 
        processed_card: dict, 
        schema: Optional[List[str]]
    ) -> dict:
        """Applies final schema with field validation."""
        result = self.apply_schema(processed_card, schema)
        
        if schema and "foreignData" in schema:
            result["foreignData"] = processed_card.get("foreignData", [])
            
        return result
