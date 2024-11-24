"""Tests for batch processing functionality.

This module contains comprehensive tests for batch processing, including core functionality,
extended coverage cases, and parallel processing scenarios.
"""

import pytest
from typing import List, Dict, Any
from unittest.mock import Mock, MagicMock, patch
from concurrent.futures import TimeoutError, Future, ThreadPoolExecutor, wait, ALL_COMPLETED
from src.analysis.cards import CardProcessorInterface
from src.core.config import CardFilterConfig
from src.core.errors import CardFilterError, CardProcessingError, BatchProcessingError
from src.processing.batch import (
    BatchProcessor,
    BatchStatistics,
    BatchErrorHandler,
    ParallelProcessor,
    LoggingInterface
)

# Fixtures and Mock Classes

@pytest.fixture
def config():
    """Create a test configuration."""
    return CardFilterConfig()

@pytest.fixture
def mock_logger():
    """Create a mock logger."""
    logger = Mock()
    logger.error = Mock()
    logger.warning = Mock()
    return logger

class MockLogger(LoggingInterface):
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

@pytest.fixture
def sample_cards():
    """Create a list of sample cards for testing."""
    return [
        {
            "name": "Card 1",
            "type": "Creature",
            "colors": ["W"],
            "convertedManaCost": 2,
            "availability": ["paper", "arena"],
            "foreignData": [
                {"language": "German", "name": "Karte 1"},
                {"language": "French", "name": "Carte 1"}
            ]
        },
        {
            "name": "Card 2",
            "type": "Instant",
            "colors": ["U"],
            "convertedManaCost": 1,
            "availability": ["paper", "mtgo"],
            "foreignData": [
                {"language": "German", "name": "Karte 2"}
            ]
        },
        {
            "name": "Card 3",
            "type": "Creature",
            "colors": ["B"],
            "convertedManaCost": 3,
            "availability": ["paper"]
        }
    ]

@pytest.fixture
def processor(config, mock_logger):
    """Create a BatchProcessor instance."""
    card_processor = CardProcessorInterface(config)
    return BatchProcessor(card_processor=card_processor, logger=mock_logger)

class MockCardProcessor(CardProcessorInterface):
    def __init__(self, behavior='normal'):
        self.behavior = behavior
    
    def process_card(self, card_data, filters=None, schema=None, additional_languages=None):
        if self.behavior == 'timeout':
            import time
            time.sleep(2)  # Sleep longer than timeout
            return card_data
        elif self.behavior == 'error':
            raise CardProcessingError("Processing error")
        elif self.behavior == 'mixed':
            if card_data.get('name', '').startswith('Error'):
                raise CardProcessingError("Processing error")
            elif card_data.get('name', '').startswith('Timeout'):
                import time
                time.sleep(2)
                return card_data
            return card_data
        return card_data

# Core Functionality Tests

class TestBatchProcessor:
    def test_initialization(self, processor, mock_logger):
        """Test batch processor initialization."""
        assert isinstance(processor.card_processor, CardProcessorInterface)
        assert processor.logger == mock_logger

    def test_process_single_card(self, processor, sample_cards):
        """Test processing of a single card."""
        card = sample_cards[0]
        result, is_filtered, is_failed = processor.process_single_card(
            card,
            filters=None,
            schema=["name", "type"],
            additional_languages=None
        )
        
        assert result is not None
        assert not is_filtered
        assert not is_failed
        assert set(result.keys()) == {"name", "type"}

    def test_process_single_card_filtered(self, processor, sample_cards):
        """Test processing of a single card that gets filtered."""
        card = sample_cards[0]
        result, is_filtered, is_failed = processor.process_single_card(
            card,
            filters={"type": {"eq": "Instant"}},
            schema=None,
            additional_languages=None
        )
        
        assert result is None
        assert is_filtered
        assert not is_failed

    def test_process_single_card_failure(self, processor):
        """Test processing of an invalid card."""
        invalid_card = {"invalid": "data"}
        result, is_filtered, is_failed = processor.process_single_card(
            invalid_card,
            filters=None,
            schema=None,
            additional_languages=None
        )
        
        assert result is None
        assert not is_filtered
        assert is_failed

    def test_process_batch_chunk_small_batch(self, processor, sample_cards):
        """Test processing of a small batch (≤5 cards) sequentially."""
        small_batch = sample_cards[:2]
        processed_cards, _, failed_count = processor.process_batch_chunk(
            small_batch,
            filters=None,
            schema=["name", "type"],
            additional_languages=None
        )

        assert len(processed_cards) == 2
        assert failed_count == 0
        assert all(set(card.keys()) == {"name", "type"} for card in processed_cards)

    def test_process_batch_chunk_large_batch(self, processor, sample_cards):
        """Test processing of a larger batch in parallel."""
        large_batch = sample_cards * 4  # 12 cards
        processed_cards, filtered_count, failed_count = processor.process_batch_chunk(
            large_batch,
            filters=None,
            schema=["name", "type"],
            additional_languages=None
        )

        assert len(processed_cards) == 12
        assert filtered_count == 0
        assert failed_count == 0
        assert all(set(card.keys()) == {"name", "type"} for card in processed_cards)

    def test_process_batch_empty_input(self, processor):
        """Test processing an empty batch."""
        results = list(processor.process_batch([]))
        assert len(results) == 0

    def test_process_batch_with_timeout(self, processor):
        """Test handling of timeout during batch processing."""
        cards = [{"name": "Test", "type": "Creature", "availability": ["paper"]}] * 10

        def slow_process(*args, **kwargs):
            import time
            time.sleep(6)  # Longer than the 5 second timeout
            return None, False, False

        with patch.object(processor, 'process_single_card', side_effect=slow_process):
            processed_cards, _, failed_count = processor.process_batch_chunk(
                cards,
                filters=None,
                schema=None,
                additional_languages=None
            )
            
            assert len(processed_cards) == 0
            assert failed_count == 10

    def test_process_batch_with_filters(self, processor, sample_cards):
        """Test batch processing with filters."""
        results = list(processor.process_batch(
            sample_cards,
            filters={"type": {"eq": "Creature"}},
            batch_size=2
        ))

        assert len(results) == 2
        total_processed = sum(len(chunk) for chunk, _ in results)
        assert total_processed == 2
        final_stats = results[-1][1]
        assert final_stats.filtered_cards == 1
        assert final_stats.failed_cards == 0

# Extended Coverage Tests

def test_batch_processor_error_handling():
    """Test batch processor error handling scenarios."""
    logger = MockLogger()
    card_processor = MagicMock()
    processor = BatchProcessor(card_processor=card_processor, logger=logger)
    
    card_processor.process_card.side_effect = CardProcessingError("Test error")
    
    cards = [{"name": "Card 1"}, {"name": "Card 2"}]
    results = list(processor.process_batch(cards))
    
    _, stats = results[-1]
    assert stats.failed_cards > 0
    assert any("Test error" in msg[1] for msg in logger.messages)
    assert any("ERROR" in msg[0] for msg in logger.messages)

def test_batch_processor_empty_input():
    """Test batch processor with empty input."""
    logger = MockLogger()
    card_processor = MagicMock()
    processor = BatchProcessor(card_processor=card_processor, logger=logger)
    
    results = list(processor.process_batch([]))
    assert len(results) == 0

def test_batch_processor_partial_failure():
    """Test batch processor with some cards failing."""
    logger = MockLogger()
    card_processor = MagicMock()
    processor = BatchProcessor(card_processor=card_processor, logger=logger)
    
    def mock_process(card_data, *args, **kwargs):
        if card_data["name"] == "Card 2":
            raise CardProcessingError("Failed to process Card 2")
        return card_data
    
    card_processor.process_card.side_effect = mock_process
    
    cards = [
        {"name": "Card 1"},
        {"name": "Card 2"},
        {"name": "Card 3"}
    ]
    
    results = []
    for chunk in processor.process_batch(cards, batch_size=1):
        results.append(chunk)
    
    _, stats = results[-1]
    assert stats.processed_cards == 2
    assert stats.failed_cards == 1
    assert any("Failed to process Card 2" in msg[1] for msg in logger.messages)

def test_batch_processor_with_filters():
    """Test batch processor with various filter combinations."""
    logger = MockLogger()
    card_processor = MagicMock()
    processor = BatchProcessor(card_processor=card_processor, logger=logger)
    
    filters = {"type": "Creature"}
    schema = ["name", "type"]
    additional_languages = ["jp", "de"]
    
    cards = [{"name": "Card 1", "type": "Creature"}]
    list(processor.process_batch(
        cards,
        filters=filters,
        schema=schema,
        additional_languages=additional_languages
    ))
    
    card_processor.process_card.assert_called_with(
        card_data=cards[0],
        filters=filters,
        schema=schema,
        additional_languages=additional_languages
    )

def test_batch_processor_large_batch():
    """Test batch processor with a large number of cards."""
    logger = MockLogger()
    card_processor = MagicMock()
    processor = BatchProcessor(card_processor=card_processor, logger=logger)
    
    cards = [{"name": f"Card {i}"} for i in range(100)]
    card_processor.process_card.return_value = {"processed": True}
    
    results = list(processor.process_batch(cards, batch_size=10))
    
    _, stats = results[-1]
    assert stats.total_cards == 100
    assert stats.processed_cards == 100
    assert stats.failed_cards == 0

# Parallel Processing Tests

def test_parallel_processor_exception_handling():
    """Test exception handling in parallel processing."""
    logger = MockLogger()
    error_handler = BatchErrorHandler(logger)
    processor = ParallelProcessor(error_handler)
    
    cards = [
        {"name": "Error Card 1"},
        {"name": "Error Card 2"},
        {"name": "Error Card 3"}
    ]
    
    def process_func(card):
        raise CardProcessingError(f"Error processing {card['name']}")
    
    results, _, failed = processor.process_parallel(
        cards=cards,
        processor_func=process_func,
        timeout=1.0,
        max_workers=2
    )
    
    assert len(results) == 0
    assert failed == len(cards)
    assert any("Error processing Error Card" in msg[1] for msg in logger.messages)

def test_parallel_processor_timeout_handling():
    """Test timeout handling in parallel processing."""
    logger = MockLogger()
    error_handler = BatchErrorHandler(logger)
    processor = ParallelProcessor(error_handler)
    
    cards = [
        {"name": "Timeout Card 1"},
        {"name": "Timeout Card 2"},
        {"name": "Timeout Card 3"}
    ]
    
    def slow_process(card):
        import time
        time.sleep(2)
        return card, False, False
    
    results, _, failed = processor.process_parallel(
        cards=cards,
        processor_func=slow_process,
        timeout=0.1,
        max_workers=2
    )
    
    assert len(results) == 0
    assert failed == len(cards)
    assert any("did not complete processing within timeout" in msg[1] for msg in logger.messages)

def test_batch_processor_mixed_failures():
    """Test batch processing with mixed success, errors, and timeouts."""
    logger = MockLogger()
    card_processor = MockCardProcessor(behavior='mixed')
    processor = BatchProcessor(card_processor=card_processor, logger=logger)
    
    cards = [
        {"name": "Normal Card 1"},
        {"name": "Error Card 1"},
        {"name": "Timeout Card 1"},
        {"name": "Normal Card 2"},
        {"name": "Error Card 2"},
        {"name": "Timeout Card 2"}
    ]
    
    results = list(processor.process_batch(
        cards_data=cards,
        batch_size=6,
        timeout=0.1
    ))
    
    _, stats = results[-1]
    assert stats.total_cards == len(cards)
    assert stats.failed_cards > 0
    assert stats.processed_cards < len(cards)
    
    error_messages = [msg for msg in logger.messages if msg[0] == "ERROR"]
    timeout_warnings = [msg for msg in logger.messages if msg[0] == "WARNING"]
    assert len(error_messages) > 0
    assert len(timeout_warnings) > 0

def test_batch_processor_chunk_exception():
    """Test exception handling in batch chunk processing."""
    logger = MockLogger()
    card_processor = MagicMock()
    processor = BatchProcessor(card_processor=card_processor, logger=logger)
    
    def raise_error(*args, **kwargs):
        raise BatchProcessingError("Chunk processing error")
    
    processor.process_batch_chunk = raise_error
    
    cards = [{"name": f"Card {i}"} for i in range(5)]
    results = list(processor.process_batch(cards_data=cards, batch_size=2))
    
    _, stats = results[-1]
    assert stats.failed_cards == len(cards)
    assert stats.processed_cards == 0
    assert any("Chunk processing error" in msg[1] for msg in logger.messages)

def test_parallel_processor_future_exception():
    """Test handling of exceptions from futures."""
    logger = MockLogger()
    error_handler = BatchErrorHandler(logger)
    processor = ParallelProcessor(error_handler)
    
    mock_future = MagicMock(spec=Future)
    mock_future.result.side_effect = CardProcessingError("Future error")
    mock_future.done.return_value = True
    mock_future.cancelled.return_value = False
    
    mock_executor = MagicMock(spec=ThreadPoolExecutor)
    mock_executor.__enter__.return_value.submit.return_value = mock_future
    
    def mock_wait(futures, timeout, return_when):
        assert return_when == ALL_COMPLETED
        return {mock_future}, set()
    
    def process_func(card):
        return card, False, False
    
    with patch('src.processing.batch.ThreadPoolExecutor', return_value=mock_executor), \
         patch('src.processing.batch.wait', side_effect=mock_wait):
        
        cards = [{"name": "Test Card"}]
        results, _, failed = processor.process_parallel(
            cards=cards,
            processor_func=process_func,
            timeout=1.0,
            max_workers=1
        )
        
        assert failed == 1
        assert len(results) == 0
        error_messages = [msg for msg in logger.messages if msg[0] == "ERROR"]
        assert len(error_messages) == 1
        assert "Future error" in error_messages[0][1]
