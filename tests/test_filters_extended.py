"""Extended tests for operators module to improve coverage."""

import pytest
from src.processing.filters import (
    _eq, _gt, _lt, _gte, _lte,
    _contains, _in,
    get_operator_function,
    OPERATORS
)

def test_contains_operator_with_invalid_types():
    """Test contains operator with invalid container types."""
    # Test with non-iterable container
    assert not _contains(123, 3)  # Number is not iterable
    
    # Test with None container
    assert not _contains(None, "test")
    
    # Test with invalid value types that might raise TypeError
    assert not _contains([1, 2, 3], object())
    
    # Test with values that might raise ValueError
    complex_list = [complex(1, 2), complex(3, 4)]
    assert not _contains(complex_list, "invalid")

def test_in_operator_with_invalid_types():
    """Test in operator with invalid container types."""
    # Test with non-iterable container
    assert not _in(3, 123)  # Number is not iterable
    
    # Test with None container
    assert not _in("test", None)
    
    # Test with invalid value types that might raise TypeError
    assert not _in(object(), [1, 2, 3])
    
    # Test with values that might raise ValueError
    assert not _in("invalid", [complex(1, 2), complex(3, 4)])

def test_contains_operator_valid_cases():
    """Test contains operator with valid cases."""
    # Test with list
    assert _contains([1, 2, 3], 2)
    assert not _contains([1, 2, 3], 4)
    
    # Test with string
    assert _contains("hello", "el")
    assert not _contains("hello", "xy")
    
    # Test with set
    assert _contains({1, 2, 3}, 2)
    assert not _contains({1, 2, 3}, 4)
    
    # Test with dict keys
    assert _contains({"a": 1, "b": 2}, "a")
    assert not _contains({"a": 1, "b": 2}, "c")

def test_in_operator_valid_cases():
    """Test in operator with valid cases."""
    # Test with list
    assert _in(2, [1, 2, 3])
    assert not _in(4, [1, 2, 3])
    
    # Test with string
    assert _in("el", "hello")
    assert not _in("xy", "hello")
    
    # Test with set
    assert _in(2, {1, 2, 3})
    assert not _in(4, {1, 2, 3})
    
    # Test with dict keys
    assert _in("a", {"a": 1, "b": 2})
    assert not _in("c", {"a": 1, "b": 2})

def test_operator_function_mapping():
    """Test that all operators are properly mapped."""
    # Test all operators are in the mapping
    assert "eq" in OPERATORS
    assert "gt" in OPERATORS
    assert "lt" in OPERATORS
    assert "gte" in OPERATORS
    assert "lte" in OPERATORS
    assert "contains" in OPERATORS
    assert "in" in OPERATORS
    
    # Test get_operator_function returns correct functions
    assert get_operator_function("eq") == _eq
    assert get_operator_function("gt") == _gt
    assert get_operator_function("lt") == _lt
    assert get_operator_function("gte") == _gte
    assert get_operator_function("lte") == _lte
    assert get_operator_function("contains") == _contains
    assert get_operator_function("in") == _in
    
    # Test invalid operator returns None
    assert get_operator_function("invalid") is None

def test_numeric_comparison_edge_cases():
    """Test numeric comparison operators with edge cases."""
    # Test with invalid numeric strings
    assert not _gt("abc", "123")
    assert not _lt("abc", "123")
    assert not _gte("abc", "123")
    assert not _lte("abc", "123")
    
    # Test with None values
    assert not _gt(None, 123)
    assert not _lt(None, 123)
    assert not _gte(None, 123)
    assert not _lte(None, 123)
    
    # Test with mixed types
    assert not _gt("123", 123.0)  # Should work as both can be converted to float
    assert not _lt(123, "123.0")  # Should work as both can be converted to float
    assert _gte(123.0, "123")    # Should work as both can be converted to float
    assert _lte("123", 123.0)    # Should work as both can be converted to float
