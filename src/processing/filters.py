"""Operator functions for card filtering with type safety.

This module provides a comprehensive set of type-safe operator functions used
for filtering Magic: The Gathering cards based on various criteria. It implements
robust type checking and conversion for numeric comparisons, string operations,
and collection membership tests.

Features:
- Type-safe numeric comparisons with automatic conversion
- Safe string operations with null handling
- Collection membership testing with type validation
- Error-safe operation with graceful fallbacks
- Extensible operator mapping system
- Comprehensive type checking and validation

Example:
    Basic usage with type safety:
    ```python
    from orthodoxy.operators import get_operator_function
    
    # Get type-safe operator functions
    gt_op = get_operator_function("gt")
    contains_op = get_operator_function("contains")
    
    # Numeric comparison with type conversion
    is_greater = gt_op("5", 3)  # True (automatic conversion)
    is_greater = gt_op("not_a_number", 3)  # False (safe handling)
    
    # String/list containment with type checking
    has_color = contains_op(["R", "G"], "R")  # True
    has_color = contains_op(None, "R")  # False (null safety)
    ```

Note:
    All operators implement comprehensive type checking and safe conversion,
    returning False instead of raising exceptions when types are incompatible
    or values are invalid. This ensures robust operation in production
    environments.
"""

from typing import Any, Callable, Optional, Union, List


def _safe_numeric_comparison(a: Any, b: Any, op: Callable[[float, float], bool]) -> bool:
    """Safely perform numeric comparison with type conversion.
    
    Attempts to convert both values to floats before comparison,
    handling various numeric formats and type mismatches safely.
    
    Args:
        a: First value to compare (will be converted to float)
        b: Second value to compare (will be converted to float)
        op: Comparison function to use
        
    Returns:
        bool: Result of comparison, or False for invalid types
        
    Example:
        ```python
        # Valid numeric comparisons with type conversion
        result = _safe_numeric_comparison("3.14", 3, lambda x, y: x > y)  # True
        result = _safe_numeric_comparison("3", "2.5", lambda x, y: x > y)  # True
        
        # Invalid type handling
        result = _safe_numeric_comparison("not_a_number", 3, lambda x, y: x > y)  # False
        result = _safe_numeric_comparison(None, 3, lambda x, y: x > y)  # False
        ```
    """
    try:
        a_num = float(a)
        b_num = float(b)
        return op(a_num, b_num)
    except (TypeError, ValueError):
        return False


def _eq(a: Any, b: Any) -> bool:
    """Equal to operator with type safety.
    
    Performs a safe equality comparison between two values,
    handling null values and type mismatches gracefully.
    
    Args:
        a: First value to compare
        b: Second value to compare
        
    Returns:
        bool: True if values are equal, False otherwise
        
    Example:
        ```python
        result = _eq("Serra Angel", "Serra Angel")  # True
        result = _eq(3, "3")  # False (no type coercion)
        result = _eq(None, "value")  # False (null safety)
        ```
    """
    try:
        return a == b
    except Exception:
        return False


def _gt(a: Any, b: Any) -> bool:
    """Greater than operator with type conversion.
    
    Performs a safe numeric greater-than comparison with
    automatic type conversion for numeric strings.
    
    Args:
        a: First value to compare (will be converted to numeric)
        b: Second value to compare (will be converted to numeric)
        
    Returns:
        bool: True if a > b, False otherwise
        
    Example:
        ```python
        result = _gt(4, 3)  # True
        result = _gt("4", "3")  # True (converted to numeric)
        result = _gt("4.5", 3)  # True (decimal conversion)
        result = _gt("a", "b")  # False (invalid numeric)
        ```
    """
    return _safe_numeric_comparison(a, b, lambda x, y: x > y)


def _lt(a: Any, b: Any) -> bool:
    """Less than operator with type conversion.
    
    Performs a safe numeric less-than comparison with
    automatic type conversion for numeric strings.
    
    Args:
        a: First value to compare (will be converted to numeric)
        b: Second value to compare (will be converted to numeric)
        
    Returns:
        bool: True if a < b, False otherwise
        
    Example:
        ```python
        result = _lt(2, 3)  # True
        result = _lt("2.5", 3)  # True (converted to numeric)
        result = _lt("2", "3.5")  # True (decimal conversion)
        result = _lt("abc", 3)  # False (invalid numeric)
        ```
    """
    return _safe_numeric_comparison(a, b, lambda x, y: x < y)


def _gte(a: Any, b: Any) -> bool:
    """Greater than or equal to operator with type conversion.
    
    Performs a safe numeric greater-than-or-equal comparison with
    automatic type conversion for numeric strings.
    
    Args:
        a: First value to compare (will be converted to numeric)
        b: Second value to compare (will be converted to numeric)
        
    Returns:
        bool: True if a >= b, False otherwise
        
    Example:
        ```python
        result = _gte(3, 3)  # True
        result = _gte(4, 3)  # True
        result = _gte("4.0", "3")  # True (converted to numeric)
        result = _gte("4.5", 3)  # True (decimal conversion)
        ```
    """
    return _safe_numeric_comparison(a, b, lambda x, y: x >= y)


def _lte(a: Any, b: Any) -> bool:
    """Less than or equal to operator with type conversion.
    
    Performs a safe numeric less-than-or-equal comparison with
    automatic type conversion for numeric strings.
    
    Args:
        a: First value to compare (will be converted to numeric)
        b: Second value to compare (will be converted to numeric)
        
    Returns:
        bool: True if a <= b, False otherwise
        
    Example:
        ```python
        result = _lte(3, 3)  # True
        result = _lte(2, 3)  # True
        result = _lte("2.5", "3")  # True (converted to numeric)
        result = _lte("2.5", 3)  # True (decimal conversion)
        ```
    """
    return _safe_numeric_comparison(a, b, lambda x, y: x <= y)


def _contains(a: Any, b: Any) -> bool:
    """Contains operator with type checking.
    
    Checks if a value is contained within a container (string, list, etc.),
    with comprehensive type checking and null safety.
    
    Args:
        a: Container to check (must be iterable)
        b: Value to look for
        
    Returns:
        bool: True if b is in a, False otherwise
        
    Note:
        Returns False for non-iterable containers or null values
        instead of raising TypeError
        
    Example:
        ```python
        # List containment with type safety
        result = _contains(["R", "G", "B"], "R")  # True
        result = _contains(["1", "2"], 1)  # False (type mismatch)
        
        # String containment with null safety
        result = _contains("Lightning Bolt", "Bolt")  # True
        result = _contains(None, "value")  # False (null safety)
        ```
    """
    try:
        return b in a
    except (TypeError, ValueError):
        return False


def _in(a: Any, b: Any) -> bool:
    """In operator with type checking.
    
    Checks if a value is a member of a container (string, list, etc.),
    with comprehensive type checking and null safety. This is the
    reverse of the contains operator.
    
    Args:
        a: Value to look for
        b: Container to check (must be iterable)
        
    Returns:
        bool: True if a is in b, False otherwise
        
    Note:
        Returns False for non-iterable containers or null values
        instead of raising TypeError
        
    Example:
        ```python
        # List membership with type safety
        result = _in("R", ["R", "G", "B"])  # True
        result = _in(1, ["1", "2"])  # False (type mismatch)
        
        # String membership with null safety
        result = _in("Bolt", "Lightning Bolt")  # True
        result = _in("value", None)  # False (null safety)
        ```
    """
    try:
        return a in b
    except (TypeError, ValueError):
        return False


# Map of operator strings to type-safe functions
OPERATORS = {
    "eq": _eq,
    "gt": _gt,
    "lt": _lt,
    "gte": _gte,
    "lte": _lte,
    "contains": _contains,
    "in": _in,
}


def get_operator_function(op: str) -> Optional[Callable[[Any, Any], bool]]:
    """Get the type-safe function for a given operator string.
    
    This function provides access to the operator functions through
    their string identifiers, ensuring type safety and proper error
    handling for all operations.
    
    Args:
        op (str): Operator string identifier
        
    Returns:
        Optional[Callable[[Any, Any], bool]]: Type-safe function implementing
            the operator, or None if the operator is not found
            
    Example:
        ```python
        # Get type-safe operator function
        gt_op = get_operator_function("gt")
        if gt_op:
            # Use operator with automatic type conversion
            result = gt_op("5", 3)  # True
            result = gt_op("not_a_number", 3)  # False (safe handling)
            
        # Handle unknown operator
        unknown_op = get_operator_function("invalid")
        if unknown_op is None:
            print("Unknown operator")
            
        # Common filtering pattern with type safety
        def apply_filter(value: Any, filter_op: str, filter_value: Any) -> bool:
            op_func = get_operator_function(filter_op)
            if op_func is None:
                raise ValueError(f"Unknown operator: {filter_op}")
            return op_func(value, filter_value)
            
        # Example usage with type conversion
        is_valid = apply_filter("3.14", "gt", "3")  # True
        is_valid = apply_filter(["R", "G"], "contains", "R")  # True
        ```
    """
    return OPERATORS.get(op)
