"""
Property-based tests for large dataset handling.

**Feature: llm-qa-correction-workbench, Property 46: Large dataset batch loading**
"""

import pytest
import tempfile
import os
from hypothesis import given, strategies as st, settings
from services import DataManager


def create_csv_with_rows(num_rows: int) -> str:
    """Helper to create a CSV file with specified number of rows."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
        f.write("instruction,output,chunk\n")
        for i in range(num_rows):
            f.write(f"Question {i},Answer {i},Chunk {i}\n")
        return f.name


@given(
    total_rows=st.integers(min_value=1001, max_value=5000),
    batch_size=st.integers(min_value=50, max_value=500)
)
@settings(max_examples=20, deadline=10000)
def test_property_46_large_dataset_batch_loading(total_rows, batch_size):
    """
    **Feature: llm-qa-correction-workbench, Property 46: Large dataset batch loading**
    **Validates: Requirements 13.1**
    
    Property: For any CSV file with more than 1000 rows, the system should use
    batch loading rather than loading all samples at once.
    
    This test verifies that:
    1. DataManager doesn't load all rows at initialization
    2. Only the first batch is loaded initially
    3. Subsequent batches can be loaded on demand
    4. Total memory usage is bounded by batch size
    """
    csv_path = create_csv_with_rows(total_rows)
    
    try:
        # Create DataManager
        dm = DataManager(csv_path, batch_size=batch_size)
        
        # Property 1: Total rows should be counted without loading all data
        assert dm.total_rows == total_rows
        
        # Property 2: No samples loaded at initialization
        assert len(dm.samples) == 0
        
        # Load first batch
        first_batch = dm.load_next_batch()
        
        # Property 3: Only first batch loaded, not all rows
        assert len(first_batch) == min(batch_size, total_rows)
        assert len(dm.samples) == min(batch_size, total_rows)
        assert len(dm.samples) < total_rows  # Not all loaded
        
        # Property 4: Can load subsequent batches
        if total_rows > batch_size:
            second_batch = dm.load_next_batch()
            expected_second_batch_size = min(batch_size, total_rows - batch_size)
            assert len(second_batch) == expected_second_batch_size
            assert len(dm.samples) == min(batch_size * 2, total_rows)
        
        # Property 5: Memory usage is bounded by loaded samples, not total rows
        memory_usage = dm.get_memory_usage_estimate()
        assert memory_usage['samples_loaded'] == len(dm.samples)
        assert memory_usage['samples_loaded'] <= batch_size * 2  # At most 2 batches loaded
        
    finally:
        os.unlink(csv_path)


@given(
    total_rows=st.integers(min_value=100, max_value=2000),
    batch_size=st.integers(min_value=10, max_value=200)
)
@settings(max_examples=30, deadline=10000)
def test_property_batch_loading_completeness(total_rows, batch_size):
    """
    Property: For any CSV file and batch size, loading all batches should
    eventually load all rows exactly once.
    
    This verifies that batch loading doesn't skip or duplicate rows.
    """
    csv_path = create_csv_with_rows(total_rows)
    
    try:
        dm = DataManager(csv_path, batch_size=batch_size)
        
        # Load all batches
        all_samples = []
        while True:
            batch = dm.load_next_batch()
            if not batch:
                break
            all_samples.extend(batch)
        
        # Property 1: All rows loaded exactly once
        assert len(all_samples) == total_rows
        
        # Property 2: No duplicate IDs
        ids = [sample.id for sample in all_samples]
        assert len(ids) == len(set(ids))
        
        # Property 3: IDs are sequential from 0 to total_rows-1
        expected_ids = set(str(i) for i in range(total_rows))
        assert set(ids) == expected_ids
        
    finally:
        os.unlink(csv_path)


@given(
    total_rows=st.integers(min_value=500, max_value=3000),
    batch_size=st.integers(min_value=50, max_value=300)
)
@settings(max_examples=20, deadline=10000)
def test_property_lazy_loading_generator(total_rows, batch_size):
    """
    Property: For any CSV file, the lazy loading generator should yield
    batches without loading all data into memory at once.
    
    This verifies the generator-based lazy loading approach.
    """
    csv_path = create_csv_with_rows(total_rows)
    
    try:
        dm = DataManager(csv_path, batch_size=batch_size)
        
        # Use generator to load batches
        batches = list(dm.load_all_batches_lazy())
        
        # Property 1: Correct number of batches
        expected_num_batches = (total_rows + batch_size - 1) // batch_size
        assert len(batches) == expected_num_batches
        
        # Property 2: Each batch (except possibly last) has correct size
        for i, batch in enumerate(batches[:-1]):
            assert len(batch) == batch_size
        
        # Property 3: Last batch has remaining rows
        last_batch_expected_size = total_rows - (batch_size * (expected_num_batches - 1))
        assert len(batches[-1]) == last_batch_expected_size
        
        # Property 4: Total samples equals total rows
        total_samples = sum(len(batch) for batch in batches)
        assert total_samples == total_rows
        
    finally:
        os.unlink(csv_path)


@given(
    total_rows=st.integers(min_value=200, max_value=1000),
    batch_size=st.integers(min_value=20, max_value=100),
    jump_to_batch=st.integers(min_value=0, max_value=5)
)
@settings(max_examples=20, deadline=10000)
def test_property_random_batch_access(total_rows, batch_size, jump_to_batch):
    """
    Property: For any CSV file, jumping to any batch number should load
    the correct samples without loading all previous batches.
    
    This verifies efficient random access to batches.
    """
    csv_path = create_csv_with_rows(total_rows)
    
    try:
        dm = DataManager(csv_path, batch_size=batch_size)
        
        # Calculate max valid batch number
        max_batch = (total_rows + batch_size - 1) // batch_size - 1
        target_batch = min(jump_to_batch, max_batch)
        
        # Jump to target batch
        dm.current_batch = target_batch
        batch = dm.load_next_batch()
        
        if target_batch * batch_size < total_rows:
            # Property 1: Batch loaded successfully
            assert len(batch) > 0
            
            # Property 2: Correct samples loaded
            expected_start_id = target_batch * batch_size
            assert batch[0].id == str(expected_start_id)
            
            # Property 3: Only target batch loaded, not all previous batches
            # (samples list should only contain the target batch)
            expected_samples_count = min(batch_size, total_rows - expected_start_id)
            assert len(dm.samples) == expected_samples_count
        
    finally:
        os.unlink(csv_path)


@given(
    total_rows=st.integers(min_value=100, max_value=1000),
    batch_size=st.integers(min_value=10, max_value=100)
)
@settings(max_examples=20, deadline=10000)
def test_property_memory_bounded_by_batch_size(total_rows, batch_size):
    """
    Property: For any CSV file and batch size, memory usage should be
    bounded by the batch size, not the total file size.
    
    This verifies that memory usage doesn't grow unboundedly with file size.
    """
    csv_path = create_csv_with_rows(total_rows)
    
    try:
        dm = DataManager(csv_path, batch_size=batch_size)
        
        # Load first batch
        dm.load_next_batch()
        usage1 = dm.get_memory_usage_estimate()
        
        # Load second batch (if available)
        if total_rows > batch_size:
            dm.load_next_batch()
            usage2 = dm.get_memory_usage_estimate()
            
            # Property: Memory usage should be roughly proportional to loaded samples
            # not to total rows
            assert usage2['samples_loaded'] <= batch_size * 2
            # Only check if there are more rows than we've loaded
            if total_rows > batch_size * 2:
                assert usage2['samples_loaded'] < total_rows  # Not all loaded
            
            # Property: Average bytes per sample should be consistent
            if usage1['samples_loaded'] > 0 and usage2['samples_loaded'] > 0:
                avg1 = usage1['avg_bytes_per_sample']
                avg2 = usage2['avg_bytes_per_sample']
                # Should be within 50% of each other (accounting for variation)
                assert 0.5 * avg1 <= avg2 <= 2.0 * avg1
        
    finally:
        os.unlink(csv_path)


@given(
    total_rows=st.integers(min_value=1001, max_value=3000)
)
@settings(max_examples=15, deadline=10000)
def test_property_46_explicit_large_file(total_rows):
    """
    **Feature: llm-qa-correction-workbench, Property 46: Large dataset batch loading**
    **Validates: Requirements 13.1**
    
    Explicit test for Property 46: Files with > 1000 rows must use batch loading.
    """
    csv_path = create_csv_with_rows(total_rows)
    
    try:
        # Use default batch size
        dm = DataManager(csv_path, batch_size=50)
        
        # Property: For files > 1000 rows, batch loading is used
        assert dm.total_rows > 1000
        
        # Load first batch
        first_batch = dm.load_next_batch()
        
        # Property: Not all samples loaded at once
        assert len(dm.samples) < dm.total_rows
        assert len(dm.samples) == 50  # Only first batch
        
        # Property: Can load more batches
        second_batch = dm.load_next_batch()
        assert len(second_batch) == 50
        assert len(dm.samples) == 100  # Two batches
        assert len(dm.samples) < dm.total_rows  # Still not all loaded
        
    finally:
        os.unlink(csv_path)
