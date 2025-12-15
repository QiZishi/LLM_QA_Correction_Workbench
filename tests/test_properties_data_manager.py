"""
Property-based tests for DataManager.

Tests universal properties for CSV loading and batch management.
"""

import os
import tempfile
import pandas as pd
from hypothesis import given, strategies as st, settings
from services import DataManager


def create_test_csv(num_rows: int, filename: str) -> str:
    """Helper function to create a test CSV file."""
    data = {
        'instruction': [f'Question {i}' for i in range(num_rows)],
        'output': [f'Answer {i}' for i in range(num_rows)],
        'chunk': [f'Reference {i}' for i in range(num_rows)]
    }
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False, encoding='utf-8')
    return filename


# Feature: llm-qa-correction-workbench, Property 1: Batch loading respects configured size
@given(
    st.integers(min_value=10, max_value=100),  # num_rows
    st.integers(min_value=5, max_value=50)     # batch_size
)
@settings(max_examples=100, deadline=None)
def test_batch_loading_respects_size(num_rows, batch_size):
    """
    For any CSV file and configured batch size, loading the first batch should
    return exactly batch_size samples (or fewer if the file has fewer rows).
    
    **Validates: Requirements 1.1**
    """
    # Create temporary CSV file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        csv_path = f.name
    
    try:
        create_test_csv(num_rows, csv_path)
        
        # Create DataManager with specified batch size
        manager = DataManager(csv_path, batch_size=batch_size)
        
        # Load first batch
        loaded_samples = manager.load_next_batch()
        
        # Property: Batch size should be respected
        expected_size = min(batch_size, num_rows)
        assert len(loaded_samples) == expected_size, \
            f"Expected {expected_size} samples, got {len(loaded_samples)}"
        
        # Property: All loaded samples should have unique IDs
        sample_ids = [s.id for s in loaded_samples]
        assert len(sample_ids) == len(set(sample_ids)), "Sample IDs must be unique"
        
    finally:
        # Cleanup
        if os.path.exists(csv_path):
            os.remove(csv_path)


# Feature: llm-qa-correction-workbench, Property 5: Automatic batch loading trigger
@given(
    st.integers(min_value=50, max_value=100),  # num_rows
    st.integers(min_value=20, max_value=30)    # batch_size
)
@settings(max_examples=50, deadline=None)
def test_automatic_batch_loading_trigger(num_rows, batch_size):
    """
    For any application state where (corrected_count + discarded_count) >= (total_loaded - 10),
    the system should automatically load the next batch without user action.
    
    **Validates: Requirements 1.5**
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        csv_path = f.name
    
    try:
        create_test_csv(num_rows, csv_path)
        manager = DataManager(csv_path, batch_size=batch_size)
        
        # Load first batch
        manager.load_next_batch()
        processed_count, total_loaded = manager.get_progress()
        
        # Mark samples as processed until threshold is reached
        threshold = total_loaded - 10
        
        # Before reaching threshold, should_load_next_batch should be False
        if processed_count < threshold:
            assert not manager.should_load_next_batch(), \
                "Should not trigger batch loading before threshold"
        
        # Mark enough samples as corrected to reach threshold
        for i in range(threshold):
            if i < len(manager.samples):
                manager.update_sample_status(manager.samples[i].id, 'corrected')
        
        # After reaching threshold, should_load_next_batch should be True (if more data exists)
        has_more_data = manager.current_batch * batch_size < num_rows
        if has_more_data:
            assert manager.should_load_next_batch(), \
                "Should trigger batch loading after reaching threshold"
        
    finally:
        if os.path.exists(csv_path):
            os.remove(csv_path)


# Feature: llm-qa-correction-workbench, Property 48: Incremental batch appending
@given(
    st.integers(min_value=60, max_value=120),  # num_rows
    st.integers(min_value=20, max_value=40)    # batch_size
)
@settings(max_examples=50, deadline=None)
def test_incremental_batch_appending(num_rows, batch_size):
    """
    For any batch loading operation after the first, the new samples should be
    appended to the existing sample list without removing or reloading previous samples.
    
    **Validates: Requirements 13.3**
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        csv_path = f.name
    
    try:
        create_test_csv(num_rows, csv_path)
        manager = DataManager(csv_path, batch_size=batch_size)
        
        # Load first batch
        first_batch = manager.load_next_batch()
        first_batch_ids = [s.id for s in first_batch]
        first_total = len(manager.samples)
        
        # Load second batch (if available)
        if manager.current_batch * batch_size < num_rows:
            second_batch = manager.load_next_batch()
            second_total = len(manager.samples)
            
            # Property 1: Total should increase by second batch size
            assert second_total == first_total + len(second_batch), \
                "Second batch should be appended, not replace"
            
            # Property 2: First batch samples should still exist with same IDs
            current_ids = [s.id for s in manager.samples[:first_total]]
            assert current_ids == first_batch_ids, \
                "First batch samples should remain unchanged"
            
            # Property 3: All IDs should still be unique
            all_ids = [s.id for s in manager.samples]
            assert len(all_ids) == len(set(all_ids)), \
                "All sample IDs must remain unique after appending"
    
    finally:
        if os.path.exists(csv_path):
            os.remove(csv_path)
