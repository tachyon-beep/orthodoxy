"""Tests for the services module functionality."""

from src.services.analysis import CardFilterService


def test_service_availability():
    """Test that the CardFilterService is available from services.analysis."""
    assert CardFilterService is not None, (
        "CardFilterService should be available from services.analysis"
    )
