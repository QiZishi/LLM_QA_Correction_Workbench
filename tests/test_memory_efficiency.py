"""
Tests for memory-efficient batch loading.

Tests that large datasets can be loaded without consuming excessive memory.
"""

import pytest
import tempfile
import os
from services import DataManager


def create_large_csv(num_rows=1000):
    """Helper to create a large test CSV file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
        f.write("instruction,output,chunk\n")
        for i in range(num_rows):
            # Create reasonably sized content
            instruction = f"Question {i}: " + "x" * 100
            output = f"Answer {i}: " + "y" * 200
            chunk = f"Chunk {i}: " + "z" * 150
            f.write(f"{instruction},{output},{chunk}\n")
        return f.name


def test_batch_loading_does_not_load_all_data():
    """Test that batch loading only loads requested batch, not entire file."""
    csv_path = create_large_csv(1000)
    
    try:
        # Create DataManager with small batch size
        dm = DataManager(csv_path, batch_size=50)
        
        # Verify total rows counted correctly
        assert dm.total_rows == 1000
        
        # Load first batch
        batch1 = dm.load_next_batch()
        
        # Verify only first batch loaded
        assert len(batch1) == 50
        assert len(dm.samples) == 50
        
        # Verify IDs are correct
        assert batch1[0].id == "0"
        assert batch1[49].id == "49"
        
    finally:
        os.unlink(csv_path)


def test_multiple_batch_loading():
    """Test loading multiple batches sequentially."""
    csv_path = create_large_csv(150)
    
    try:
        dm = DataManager(csv_path, batch_size=50)
        
        # Load first batch
        batch1 = dm.load_next_batch()
        assert len(batch1) == 50
        assert len(dm.samples) == 50
        
        # Load second batch
        batch2 = dm.load_next_batch()
        assert len(batch2) == 50
        assert len(dm.samples) == 100
        
        # Load third batch (partial)
        batch3 = dm.load_next_batch()
        assert len(batch3) == 50
        assert len(dm.samples) == 150
        
        # Try to load fourth batch (should be empty)
        batch4 = dm.load_next_batch()
        assert len(batch4) == 0
        assert len(dm.samples) == 150
        
    finally:
        os.unlink(csv_path)


def test_lazy_batch_loading_generator():
    """Test lazy batch loading using generator."""
    csv_path = create_large_csv(200)
    
    try:
        dm = DataManager(csv_path, batch_size=50)
        
        # Use generator to load batches
        batches = list(dm.load_all_batches_lazy())
        
        # Verify correct number of batches
        assert len(batches) == 4
        
        # Verify batch sizes
        assert len(batches[0]) == 50
        assert len(batches[1]) == 50
        assert len(batches[2]) == 50
        assert len(batches[3]) == 50
        
        # Verify IDs are sequential
        assert batches[0][0].id == "0"
        assert batches[1][0].id == "50"
        assert batches[2][0].id == "100"
        assert batches[3][0].id == "150"
        
    finally:
        os.unlink(csv_path)


def test_memory_usage_estimate():
    """Test memory usage estimation."""
    csv_path = create_large_csv(100)
    
    try:
        dm = DataManager(csv_path, batch_size=50)
        
        # Load first batch
        dm.load_next_batch()
        
        # Get memory usage estimate
        usage = dm.get_memory_usage_estimate()
        
        # Verify usage statistics
        assert 'total_bytes' in usage
        assert 'total_mb' in usage
        assert 'samples_loaded' in usage
        assert 'avg_bytes_per_sample' in usage
        
        assert usage['samples_loaded'] == 50
        assert usage['total_bytes'] > 0
        assert usage['total_mb'] > 0
        assert usage['avg_bytes_per_sample'] > 0
        
        # Load second batch
        dm.load_next_batch()
        
        # Get updated memory usage
        usage2 = dm.get_memory_usage_estimate()
        
        # Verify memory usage increased
        assert usage2['samples_loaded'] == 100
        assert usage2['total_bytes'] > usage['total_bytes']
        
    finally:
        os.unlink(csv_path)


def test_efficient_row_counting():
    """Test that row counting doesn't load entire file into memory."""
    csv_path = create_large_csv(500)
    
    try:
        # Create DataManager (this counts rows)
        dm = DataManager(csv_path, batch_size=50)
        
        # Verify row count is correct
        assert dm.total_rows == 500
        
        # Verify no samples loaded yet
        assert len(dm.samples) == 0
        
    finally:
        os.unlink(csv_path)


def test_batch_loading_with_very_large_file():
    """Test batch loading with a very large file (simulated)."""
    csv_path = create_large_csv(2000)
    
    try:
        dm = DataManager(csv_path, batch_size=100)
        
        # Verify total rows
        assert dm.total_rows == 2000
        
        # Load first batch
        batch1 = dm.load_next_batch()
        assert len(batch1) == 100
        
        # Skip to last batch
        dm.current_batch = 19  # Jump to batch 19 (rows 1900-1999)
        batch_last = dm.load_next_batch()
        assert len(batch_last) == 100
        
        # Verify IDs
        assert batch_last[0].id == "1900"
        assert batch_last[99].id == "1999"
        
    finally:
        os.unlink(csv_path)


def test_memory_efficiency_with_edits():
    """Test memory usage when samples are edited."""
    csv_path = create_large_csv(50)
    
    try:
        dm = DataManager(csv_path, batch_size=50)
        dm.load_next_batch()
        
        # Get initial memory usage
        usage_before = dm.get_memory_usage_estimate()
        
        # Edit some samples
        for i in range(10):
            sample = dm.samples[i]
            sample.edited_instruction = "Edited: " + sample.instruction
            sample.edited_output = "Edited: " + sample.output
            sample.diff_result = "<false>old</false><true>new</true>"
        
        # Get memory usage after edits
        usage_after = dm.get_memory_usage_estimate()
        
        # Verify memory usage increased due to edits
        assert usage_after['total_bytes'] > usage_before['total_bytes']
        
    finally:
        os.unlink(csv_path)


def test_partial_last_batch():
    """Test loading when last batch is partial."""
    csv_path = create_large_csv(125)
    
    try:
        dm = DataManager(csv_path, batch_size=50)
        
        # Load batches
        batch1 = dm.load_next_batch()
        assert len(batch1) == 50
        
        batch2 = dm.load_next_batch()
        assert len(batch2) == 50
        
        batch3 = dm.load_next_batch()
        assert len(batch3) == 25  # Partial batch
        
        # Verify total
        assert len(dm.samples) == 125
        
    finally:
        os.unlink(csv_path)
