"""Tests for filter functions.

This module contains tests for the filter functions used in card filtering.
"""

from src.processing.filters import get_operator_function


def test_get_operator_function():
    """Tests the get_operator_function utility with various filter operations."""
    # Test equality filter
    eq_op = get_operator_function("eq")
    assert eq_op is not None
    assert eq_op(5, 5) is True
    assert eq_op(5, 6) is False

    # Test contains filter
    contains_op = get_operator_function("contains")
    assert contains_op is not None
    assert contains_op(["A", "B"], "A") is True
    assert contains_op(["A", "B"], "C") is False
    assert contains_op("ABC", "B") is True
    assert contains_op(5, "B") is False  # Invalid type

    # Test greater than filter
    gt_op = get_operator_function("gt")
    assert gt_op is not None
    assert gt_op(5, 3) is True
    assert gt_op(3, 5) is False
    assert gt_op("abc", 5) is False  # Invalid type

    # Test less than filter
    lt_op = get_operator_function("lt")
    assert lt_op is not None
    assert lt_op(3, 5) is True
    assert lt_op(5, 3) is False
    assert lt_op("abc", 5) is False  # Invalid type

    # Test invalid filter operation
    assert get_operator_function("invalid") is None
