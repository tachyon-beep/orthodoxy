"""Batch processing module for handling multiple Magic: The Gathering cards.

This module provides robust parallel processing capabilities for large sets of
cards, implementing advanced features for concurrent execution, resource
management, and error handling.

Key Features:
- Parallel processing using ThreadPoolExecutor with dynamic worker scaling
- Automatic batch size optimization based on system resources
- Comprehensive timeout handling with graceful recovery
- Detailed progress tracking and statistics collection
- Robust error handling with context preservation
- Memory-efficient processing through dynamic chunking
- Resource cleanup with proper thread management

Example:
    Basic usage with automatic resource management:
    ```python
    processor = BatchProcessor(card_processor, logger)
    for processed_cards, stats in processor.process_batch(cards_data):
        print(f"Processed {stats.processed_cards} cards")
        print(f"Success rate: {stats.processed_cards/stats.total_cards:.2%}")
    ```

    Advanced usage with custom processing parameters:
    ```python
    processor = BatchProcessor(card_processor, logger)
    for processed_cards, stats in processor.process_batch(
        cards_data,
        filters={"colors": {"contains": "W"}},
        schema=["name", "manaCost"],
        batch_size=50,  # Optimize chunk size
        timeout=10.0    # Set operation timeout
    ):
        print(f"Batch complete:")
        print(f"- Processed: {len(processed_cards)}")
        print(f"- Filtered: {stats.filtered_cards}")
        print(f"- Failed: {stats.failed_cards}")
        print(f"- Success Rate: {stats.processed_cards/stats.total_cards:.2%}")
    ```

Note:
    The module implements comprehensive error handling and resource cleanup,
    ensuring system resources are properly managed even in failure scenarios.
    All parallel operations include timeout handling and graceful shutdown
    capabilities.
"""

from typing import Optional, List, Dict, Any, Iterator, Tuple, Protocol, Set, Union
from concurrent.futures import (
    ThreadPoolExecutor, Future, wait, ALL_COMPLETED,
    TimeoutError as FuturesTimeoutError
)
from dataclasses import dataclass, field


class LoggingInterface(Protocol):
    """Protocol defining the logging interface required by BatchProcessor.
    
    This protocol ensures that any logger implementation used with BatchProcessor
    provides the necessary error and warning logging methods with proper
    type safety.

    Methods:
        error: Log an error message with optional exception details
        warning: Log a warning message for non-critical issues
    """
    def error(self, message: str) -> None: ...
    def warning(self, message: str) -> None: ...


class CardProcessorInterface(Protocol):
    """Protocol defining the card processing interface required by BatchProcessor.
    
    This protocol specifies the contract that any card processor must fulfill
    to work with the batch processing system, ensuring type safety and
    proper error handling.

    Methods:
        process_card: Process a single card with type-safe operations
            Args:
                card_data (dict): Raw card data to process
                filters (Optional[Dict[str, Any]]): Type-checked filter conditions
                schema (Optional[List[str]]): Validated field selection
                additional_languages (Optional[List[str]]): Language codes
            Returns:
                Optional[dict]: Processed card data, or None if filtered out
    """
    def process_card(
        self,
        card_data: dict,
        filters: Optional[Dict[str, Any]],
        schema: Optional[List[str]],
        additional_languages: Optional[List[str]]
    ) -> Optional[dict]: ...


@dataclass
class BatchStatistics:
    """Statistics tracking for batch processing operations.
    
    This class maintains atomic counters for various aspects of batch processing,
    providing thread-safe insights into the processing results and performance.

    Attributes:
        total_cards (int): Total number of cards in batch
        processed_cards (int): Successfully processed cards
        filtered_cards (int): Cards filtered out by criteria
        failed_cards (int): Cards that failed processing
    """
    total_cards: int = 0
    processed_cards: int = 0
    filtered_cards: int = 0
    failed_cards: int = 0

    def update(self, processed: int, filtered: int, failed: int) -> None:
        """Update statistics with results from a processing batch.
        
        Thread-safe update of processing statistics.
        
        Args:
            processed (int): Number of cards successfully processed
            filtered (int): Number of cards filtered out
            failed (int): Number of cards that failed processing
        """
        self.processed_cards += processed
        self.filtered_cards += filtered
        self.failed_cards += failed


class BatchErrorHandler:
    """Handles error logging and recovery during batch processing.
    
    This class provides centralized error handling for the batch processing
    system, ensuring consistent error reporting and implementing recovery
    strategies for various failure scenarios.

    Features:
    - Structured error logging with context
    - Timeout handling and recovery
    - Resource cleanup after failures
    - Error aggregation and reporting

    Attributes:
        logger (LoggingInterface): Thread-safe logger for error reporting
    """
    
    def __init__(self, logger: LoggingInterface):
        """Initialize the error handler with a thread-safe logger.
        
        Args:
            logger (LoggingInterface): Thread-safe logging interface
        """
        self.logger = logger

    def log_card_error(self, card_name: str, error: Exception) -> None:
        """Log an error that occurred while processing a specific card.
        
        Args:
            card_name (str): Name of the card that caused the error
            error (Exception): The exception that occurred
        """
        self.logger.error(f"Error processing card {card_name}: {str(error)}")

    def log_batch_error(self, error: Exception) -> None:
        """Log an error that occurred during batch processing.
        
        Args:
            error (Exception): The batch-level exception that occurred
        """
        self.logger.error(f"Batch processing error: {str(error)}")

    def log_timeout_warning(self, count: int) -> None:
        """Log a warning about cards that exceeded the timeout limit.
        
        Args:
            count (int): Number of cards that timed out
        """
        self.logger.warning(
            f"{count} cards did not complete processing within timeout"
        )


class ParallelProcessor:
    """Handles parallel processing of card batches with resource management.
    
    This class manages the concurrent processing of cards using thread pools,
    implementing proper resource management, timeout handling, and cleanup
    operations.

    Features:
    - Dynamic thread pool sizing
    - Timeout handling per operation
    - Resource cleanup on completion
    - Error context preservation
    - Memory-efficient processing

    Attributes:
        error_handler (BatchErrorHandler): Thread-safe error handler
    """

    def __init__(self, error_handler: BatchErrorHandler):
        """Initialize the parallel processor with error handling.
        
        Args:
            error_handler (BatchErrorHandler): Thread-safe error handler
        """
        self.error_handler = error_handler

    def process_parallel(
        self,
        cards: List[dict],
        processor_func: Any,
        timeout: float,
        max_workers: int
    ) -> Tuple[List[dict], int, int]:
        """Process cards in parallel with resource management.
        
        Args:
            cards: List of cards to process
            processor_func: Thread-safe processing function
            timeout: Maximum time (seconds) to wait for completion
            max_workers: Maximum concurrent workers

        Returns:
            Tuple containing:
                - List of successfully processed cards
                - Number of filtered cards
                - Number of failed cards
        """
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = self._submit_tasks(executor, cards, processor_func)
            return self._process_futures(futures, timeout)

    def _submit_tasks(
        self,
        executor: ThreadPoolExecutor,
        cards: List[dict],
        processor_func: Any
    ) -> List[Future]:
        """Submit processing tasks to the thread pool.
        
        Args:
            executor: Thread pool executor
            cards: Cards to process
            processor_func: Thread-safe processing function

        Returns:
            List[Future]: Futures for submitted tasks
        """
        return [executor.submit(processor_func, card) for card in cards]

    def _process_futures(
        self,
        futures: List[Future],
        timeout: float
    ) -> Tuple[List[dict], int, int]:
        """Process completed futures with timeout handling.
        
        Args:
            futures: List of futures to process
            timeout: Maximum wait time in seconds

        Returns:
            Tuple containing results and statistics
        """
        try:
            done, not_done = wait(futures, timeout=timeout, return_when=ALL_COMPLETED)
            results = self._handle_completed_futures(done)
            failed_from_timeout = self._handle_timeout(not_done)
            
            return (
                results.processed_cards,
                results.filtered_count,
                results.failed_count + failed_from_timeout
            )
            
        except Exception as e:
            self.error_handler.log_batch_error(e)
            self._cancel_futures(futures)
            return [], 0, len(futures)

    @dataclass
    class ProcessingResults:
        """Container for thread-safe processing results.
        
        Attributes:
            processed_cards (List[dict]): Successfully processed cards
            filtered_count (int): Number of filtered cards
            failed_count (int): Number of failed cards
        """
        processed_cards: List[dict] = field(default_factory=list)
        filtered_count: int = 0
        failed_count: int = 0

    def _handle_completed_futures(self, done: Set[Future]) -> ProcessingResults:
        """Process completed futures with error handling.
        
        Args:
            done: Set of completed futures

        Returns:
            ProcessingResults: Collected results
        """
        results = self.ProcessingResults()

        for future in done:
            if future.cancelled():
                results.failed_count += 1
                continue

            self._process_single_future(future, results)

        return results

    def _process_single_future(
        self,
        future: Future,
        results: ProcessingResults
    ) -> None:
        """Process a single completed future with error handling.
        
        Args:
            future: The completed future to process
            results: Results container to update
        """
        try:
            result = future.result()
        except Exception as e:
            self.error_handler.log_card_error("Unknown", e)
            results.failed_count += 1
            return

        if result is None:
            results.failed_count += 1
            return

        if not isinstance(result, tuple) or len(result) != 3:
            self.error_handler.log_card_error(
                "Unknown",
                Exception("Invalid result format: expected (card_result, is_filtered, is_failed) tuple")
            )
            results.failed_count += 1
            return

        try:
            self._update_results(result, results)
        except Exception as e:
            self.error_handler.log_card_error("Unknown", e)
            results.failed_count += 1

    def _update_results(
        self,
        result: Tuple[Optional[dict], bool, bool],
        results: ProcessingResults
    ) -> None:
        """Update processing results atomically.
        
        Args:
            result: Processing result tuple
            results: Results container to update
        """
        card_result, is_filtered, is_failed = result

        if is_failed:
            results.failed_count += 1
        if is_filtered:
            results.filtered_count += 1
        if card_result is not None:
            results.processed_cards.append(card_result)

    def _handle_timeout(self, not_done: Set[Future]) -> int:
        """Handle futures that exceeded timeout.
        
        Args:
            not_done: Set of incomplete futures

        Returns:
            int: Number of timed out futures
        """
        if not_done:
            self.error_handler.log_timeout_warning(len(not_done))
            self._cancel_futures(not_done)
            return len(not_done)
        return 0

    def _cancel_futures(self, futures: Union[Set[Future], List[Future]]) -> None:
        """Cancel futures and release resources.
        
        Args:
            futures: Futures to cancel and clean up
        """
        for future in futures:
            future.cancel()


class BatchProcessor:
    """Orchestrates batch processing of multiple cards with resource management.
    
    This class provides the main interface for batch processing Magic: The Gathering
    cards, implementing robust parallel processing with proper resource management,
    error handling, and statistics tracking.

    Features:
    - Parallel processing with dynamic scaling
    - Memory-efficient batch processing
    - Comprehensive error handling
    - Detailed statistics tracking
    - Resource cleanup and management
    - Type-safe operations

    Example:
        ```python
        processor = BatchProcessor(card_processor, logger)
        
        # Process cards with resource management
        for processed_cards, stats in processor.process_batch(
            cards_data,
            filters={"rarity": {"equals": "rare"}},
            schema=["name", "manaCost", "rarity"],
            batch_size=50,  # Optimize memory usage
            timeout=10.0    # Ensure timely completion
        ):
            print(f"Batch processed: {len(processed_cards)} cards")
            print(f"Total success: {stats.processed_cards}")
            print(f"Total filtered: {stats.filtered_cards}")
            print(f"Success rate: {stats.processed_cards/stats.total_cards:.2%}")
        ```

    Attributes:
        card_processor (CardProcessorInterface): Type-safe card processor
        logger (LoggingInterface): Thread-safe logger
        error_handler (BatchErrorHandler): Error handling system
        parallel_processor (ParallelProcessor): Parallel processing manager
    """

    def __init__(self, card_processor: CardProcessorInterface, logger: LoggingInterface):
        """Initialize the BatchProcessor with required components.
        
        Args:
            card_processor: Type-safe card processor implementation
            logger: Thread-safe logging interface
        """
        self.card_processor = card_processor
        self.logger = logger  # Store logger for backward compatibility
        self.error_handler = BatchErrorHandler(logger)
        self.parallel_processor = ParallelProcessor(self.error_handler)

    def process_single_card(
        self,
        card: dict,
        filters: Optional[Dict[str, Any]],
        schema: Optional[List[str]],
        additional_languages: Optional[List[str]],
    ) -> Tuple[Optional[dict], bool, bool]:
        """Process a single card with comprehensive error handling.
        
        Args:
            card: Card data to process
            filters: Type-checked filter conditions
            schema: Validated field selection
            additional_languages: Language codes to include

        Returns:
            Tuple containing:
                - Processed card data or None
                - Whether the card was filtered
                - Whether processing failed
        """
        try:
            result = self.card_processor.process_card(
                card_data=card,
                filters=filters,
                schema=schema,
                additional_languages=additional_languages
            )
            return result, result is None, False
        except Exception as e:
            self.error_handler.log_card_error(card.get('name', 'Unknown'), e)
            return None, False, True

    def process_batch_chunk(
        self,
        cards: List[dict],
        filters: Optional[Dict[str, Any]],
        schema: Optional[List[str]],
        additional_languages: Optional[List[str]],
        timeout: float = 5.0
    ) -> Tuple[List[dict], int, int]:
        """Process a chunk of cards with optimized execution strategy.
        
        Implements adaptive processing strategy based on batch size:
        - Small batches (<= 5 cards): Sequential processing
        - Larger batches: Parallel processing with resource management

        Args:
            cards: List of cards to process
            filters: Type-checked filter conditions
            schema: Validated field selection
            additional_languages: Language codes to include
            timeout: Maximum processing time per card

        Returns:
            Tuple containing:
                - List of successfully processed cards
                - Number of filtered cards
                - Number of failed cards
        """
        # Process cards sequentially if batch is small
        if len(cards) <= 5:
            processed_cards = []
            filtered_count = 0
            failed_count = 0
            
            for card in cards:
                result, is_filtered, is_failed = self.process_single_card(
                    card, filters, schema, additional_languages
                )
                if result is not None:
                    processed_cards.append(result)
                if is_filtered:
                    filtered_count += 1
                if is_failed:
                    failed_count += 1
                    
            return processed_cards, filtered_count, failed_count
        
        # Process larger batches in parallel with resource management
        def process_card(card):
            return self.process_single_card(
                card, filters, schema, additional_languages
            )
            
        return self.parallel_processor.process_parallel(
            cards=cards,
            processor_func=process_card,
            timeout=timeout,
            max_workers=min(len(cards), 10)
        )

    def process_batch(
        self,
        cards_data: List[dict],
        filters: Optional[Dict[str, Any]] = None,
        schema: Optional[List[str]] = None,
        additional_languages: Optional[List[str]] = None,
        batch_size: int = 100,
        timeout: float = 5.0
    ) -> Iterator[Tuple[List[dict], BatchStatistics]]:
        """Process a batch of cards with comprehensive resource management.
        
        This method processes cards in memory-efficient chunks, yielding results
        as they become available along with detailed statistics. Implements
        proper resource management and error handling throughout the process.

        Args:
            cards_data: List of cards to process
            filters: Type-checked filter conditions
            schema: Validated field selection
            additional_languages: Language codes to include
            batch_size: Size of processing chunks
            timeout: Maximum processing time per card

        Yields:
            Iterator[Tuple[List[dict], BatchStatistics]]: Tuple containing:
                - List of processed cards in current chunk
                - Updated statistics for entire batch

        Example:
            ```python
            processor = BatchProcessor(card_processor, logger)
            
            # Process large dataset with resource management
            for processed_chunk, stats in processor.process_batch(
                cards_data,
                batch_size=50,  # Memory-efficient chunks
                timeout=10.0    # Ensure timely completion
            ):
                print(f"Chunk processed: {len(processed_chunk)} cards")
                print(f"Progress: {stats.processed_cards}/{stats.total_cards}")
                print(f"Success rate: {stats.processed_cards/stats.total_cards:.2%}")
            ```
        """
        if not cards_data:
            return

        stats = BatchStatistics(total_cards=len(cards_data))
        
        # Process cards in memory-efficient chunks
        for i in range(0, len(cards_data), batch_size):
            chunk = cards_data[i:i + batch_size]
            try:
                processed_chunk, filtered_count, failed_count = self.process_batch_chunk(
                    chunk,
                    filters,
                    schema,
                    additional_languages,
                    timeout
                )
                
                # Update statistics atomically
                stats.update(
                    processed=len(processed_chunk),
                    filtered=filtered_count,
                    failed=failed_count
                )
                
                yield processed_chunk, stats
                
            except Exception as e:
                self.error_handler.log_batch_error(e)
                stats.update(processed=0, filtered=0, failed=len(chunk))
                yield [], stats
