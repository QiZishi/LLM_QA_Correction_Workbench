"""
Tests for performance monitoring utilities.

Tests performance tracking, statistics, and monitoring decorators.
"""

import pytest
import time
import tempfile
import os
from utils.performance import (
    PerformanceMonitor,
    get_monitor,
    monitor_performance,
    measure_time,
    check_responsiveness
)
from services import DataManager, DiffEngine


def test_performance_monitor_record():
    """Test recording performance metrics."""
    monitor = PerformanceMonitor()
    
    monitor.record("test_op", 0.5)
    monitor.record("test_op", 0.3)
    monitor.record("test_op", 0.7)
    
    stats = monitor.get_stats("test_op")
    
    assert stats['count'] == 3
    assert stats['min'] == 0.3
    assert stats['max'] == 0.7
    assert stats['avg'] == pytest.approx(0.5, rel=0.01)
    assert stats['total'] == pytest.approx(1.5, rel=0.01)


def test_performance_monitor_multiple_operations():
    """Test monitoring multiple operations."""
    monitor = PerformanceMonitor()
    
    monitor.record("op1", 0.1)
    monitor.record("op1", 0.2)
    monitor.record("op2", 0.5)
    monitor.record("op2", 0.6)
    
    all_stats = monitor.get_all_stats()
    
    assert len(all_stats) == 2
    assert all_stats['op1']['count'] == 2
    assert all_stats['op2']['count'] == 2


def test_performance_monitor_clear():
    """Test clearing performance metrics."""
    monitor = PerformanceMonitor()
    
    monitor.record("test_op", 0.5)
    assert monitor.get_stats("test_op")['count'] == 1
    
    monitor.clear()
    assert monitor.get_stats("test_op")['count'] == 0


def test_monitor_performance_decorator():
    """Test performance monitoring decorator."""
    monitor = get_monitor()
    monitor.clear()
    
    @monitor_performance("test_function")
    def slow_function():
        time.sleep(0.1)
        return "done"
    
    result = slow_function()
    
    assert result == "done"
    
    stats = monitor.get_stats("test_function")
    assert stats['count'] == 1
    assert stats['avg'] >= 0.1


def test_measure_time_context_manager():
    """Test time measurement context manager."""
    monitor = get_monitor()
    monitor.clear()
    
    with measure_time("test_context"):
        time.sleep(0.1)
    
    stats = monitor.get_stats("test_context")
    assert stats['count'] == 1
    assert stats['avg'] >= 0.1


def test_check_responsiveness_decorator():
    """Test responsiveness checking decorator."""
    @check_responsiveness(max_duration=0.5)
    def fast_function():
        time.sleep(0.1)
        return "done"
    
    @check_responsiveness(max_duration=0.05)
    def slow_function():
        time.sleep(0.1)
        return "done"
    
    # Fast function should complete without warning
    result1 = fast_function()
    assert result1 == "done"
    
    # Slow function should log warning but still complete
    result2 = slow_function()
    assert result2 == "done"


def test_data_manager_performance_monitoring():
    """Test that DataManager operations are monitored."""
    monitor = get_monitor()
    monitor.clear()
    
    # Create test CSV
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
        f.write("instruction,output,chunk\n")
        for i in range(100):
            f.write(f"Question {i},Answer {i},Chunk {i}\n")
        csv_path = f.name
    
    try:
        # Create DataManager and load batch
        dm = DataManager(csv_path, batch_size=50)
        dm.load_next_batch()
        
        # Check that load_next_batch was monitored
        stats = monitor.get_stats("load_next_batch")
        assert stats['count'] >= 1
        assert stats['avg'] > 0
        
    finally:
        os.unlink(csv_path)


def test_diff_engine_performance_monitoring():
    """Test that DiffEngine operations are monitored."""
    monitor = get_monitor()
    monitor.clear()
    
    engine = DiffEngine()
    
    original = "This is the original text with some content"
    modified = "This is the modified text with different content"
    
    result = engine.compute_diff(original, modified)
    
    # Check that compute_diff was monitored
    stats = monitor.get_stats("compute_diff")
    assert stats['count'] >= 1
    assert stats['avg'] > 0


def test_performance_stats_for_multiple_calls():
    """Test statistics after multiple function calls."""
    monitor = get_monitor()
    monitor.clear()
    
    @monitor_performance("repeated_op")
    def test_function(duration):
        time.sleep(duration)
    
    # Call function multiple times with different durations
    test_function(0.05)
    test_function(0.1)
    test_function(0.15)
    
    stats = monitor.get_stats("repeated_op")
    
    assert stats['count'] == 3
    assert stats['min'] >= 0.05
    assert stats['max'] >= 0.15
    assert 0.05 <= stats['avg'] <= 0.15


def test_performance_monitor_empty_operation():
    """Test getting stats for non-existent operation."""
    monitor = PerformanceMonitor()
    
    stats = monitor.get_stats("nonexistent")
    
    assert stats['count'] == 0
    assert stats['min'] == 0
    assert stats['max'] == 0
    assert stats['avg'] == 0
    assert stats['total'] == 0


def test_global_monitor_instance():
    """Test that get_monitor returns same instance."""
    monitor1 = get_monitor()
    monitor2 = get_monitor()
    
    assert monitor1 is monitor2


def test_performance_monitoring_with_exceptions():
    """Test that performance is recorded even when function raises exception."""
    monitor = get_monitor()
    monitor.clear()
    
    @monitor_performance("failing_op")
    def failing_function():
        time.sleep(0.1)
        raise ValueError("Test error")
    
    with pytest.raises(ValueError):
        failing_function()
    
    # Performance should still be recorded
    stats = monitor.get_stats("failing_op")
    assert stats['count'] == 1
    assert stats['avg'] >= 0.1


def test_performance_log_stats(caplog):
    """Test logging of performance statistics."""
    import logging
    caplog.set_level(logging.INFO)
    
    monitor = PerformanceMonitor()
    monitor.record("test_op", 0.5)
    monitor.record("test_op", 0.3)
    
    monitor.log_stats("test_op")
    
    # Check that log contains expected information
    assert "test_op" in caplog.text
    assert "Count: 2" in caplog.text


def test_measure_time_with_exception():
    """Test that time is measured even when exception occurs."""
    monitor = get_monitor()
    monitor.clear()
    
    with pytest.raises(ValueError):
        with measure_time("error_context"):
            time.sleep(0.1)
            raise ValueError("Test error")
    
    # Time should still be recorded
    stats = monitor.get_stats("error_context")
    assert stats['count'] == 1
    assert stats['avg'] >= 0.1
