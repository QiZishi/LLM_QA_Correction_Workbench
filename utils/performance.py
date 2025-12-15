"""
Performance monitoring utilities.

Provides decorators and functions for tracking operation performance.
"""

import time
import functools
from typing import Callable, Any, Dict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """
    Performance monitoring class for tracking operation times.
    """
    
    def __init__(self):
        """Initialize performance monitor."""
        self.metrics: Dict[str, list] = {}
    
    def record(self, operation: str, duration: float):
        """
        Record an operation duration.
        
        Args:
            operation: Name of the operation
            duration: Duration in seconds
        """
        if operation not in self.metrics:
            self.metrics[operation] = []
        
        self.metrics[operation].append(duration)
    
    def get_stats(self, operation: str) -> Dict[str, float]:
        """
        Get statistics for an operation.
        
        Args:
            operation: Name of the operation
        
        Returns:
            Dictionary with min, max, avg, total, count
        """
        if operation not in self.metrics or not self.metrics[operation]:
            return {
                'min': 0,
                'max': 0,
                'avg': 0,
                'total': 0,
                'count': 0
            }
        
        durations = self.metrics[operation]
        return {
            'min': min(durations),
            'max': max(durations),
            'avg': sum(durations) / len(durations),
            'total': sum(durations),
            'count': len(durations)
        }
    
    def get_all_stats(self) -> Dict[str, Dict[str, float]]:
        """
        Get statistics for all operations.
        
        Returns:
            Dictionary mapping operation names to their statistics
        """
        return {
            operation: self.get_stats(operation)
            for operation in self.metrics.keys()
        }
    
    def clear(self):
        """Clear all recorded metrics."""
        self.metrics.clear()
    
    def log_stats(self, operation: str = None):
        """
        Log statistics to console.
        
        Args:
            operation: Specific operation to log, or None for all
        """
        if operation:
            stats = self.get_stats(operation)
            logger.info(f"Performance stats for '{operation}':")
            logger.info(f"  Count: {stats['count']}")
            logger.info(f"  Avg: {stats['avg']:.4f}s")
            logger.info(f"  Min: {stats['min']:.4f}s")
            logger.info(f"  Max: {stats['max']:.4f}s")
            logger.info(f"  Total: {stats['total']:.4f}s")
        else:
            all_stats = self.get_all_stats()
            logger.info("Performance stats for all operations:")
            for op, stats in all_stats.items():
                logger.info(f"  {op}:")
                logger.info(f"    Count: {stats['count']}")
                logger.info(f"    Avg: {stats['avg']:.4f}s")
                logger.info(f"    Total: {stats['total']:.4f}s")


# Global performance monitor instance
_global_monitor = PerformanceMonitor()


def get_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance."""
    return _global_monitor


def monitor_performance(operation_name: str = None):
    """
    Decorator to monitor function performance.
    
    Args:
        operation_name: Name for the operation (defaults to function name)
    
    Example:
        @monitor_performance("csv_loading")
        def load_csv(path):
            ...
    """
    def decorator(func: Callable) -> Callable:
        op_name = operation_name or func.__name__
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                _global_monitor.record(op_name, duration)
                
                # Log if operation took longer than 1 second
                if duration > 1.0:
                    logger.warning(
                        f"Operation '{op_name}' took {duration:.2f}s "
                        f"(threshold: 1.0s)"
                    )
        
        return wrapper
    return decorator


def measure_time(operation_name: str):
    """
    Context manager for measuring operation time.
    
    Example:
        with measure_time("data_processing"):
            process_data()
    """
    class TimeMeasurement:
        def __init__(self, name: str):
            self.name = name
            self.start_time = None
        
        def __enter__(self):
            self.start_time = time.time()
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            duration = time.time() - self.start_time
            _global_monitor.record(self.name, duration)
            
            if duration > 1.0:
                logger.warning(
                    f"Operation '{self.name}' took {duration:.2f}s "
                    f"(threshold: 1.0s)"
                )
    
    return TimeMeasurement(operation_name)


def check_responsiveness(max_duration: float = 0.5):
    """
    Decorator to check if operation completes within time limit.
    
    Args:
        max_duration: Maximum allowed duration in seconds
    
    Raises:
        TimeoutError: If operation exceeds max_duration
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            
            if duration > max_duration:
                logger.warning(
                    f"Operation '{func.__name__}' took {duration:.2f}s, "
                    f"exceeding limit of {max_duration}s"
                )
            
            return result
        
        return wrapper
    return decorator
