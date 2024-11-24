"""Tests for the WriterStats class functionality.

This module contains tests for the WriterStats class, which tracks statistics
about card writing operations.
"""

from src.utils.models import WriterStats


def test_initial_stats():
    """Tests that WriterStats initializes with zero values."""
    stats = WriterStats()
    assert stats.cards_written == 0
    assert stats.sets_processed == 0
    assert stats.errors_encountered == 0


def test_stats_increment():
    """Tests that WriterStats correctly stores non-zero values."""
    stats = WriterStats(cards_written=1, sets_processed=2, errors_encountered=3)
    assert stats.cards_written == 1
    assert stats.sets_processed == 2
    assert stats.errors_encountered == 3
