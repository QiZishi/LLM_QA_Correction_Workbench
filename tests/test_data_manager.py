"""
Unit tests for DataManager.

Tests specific examples, edge cases, and error conditions.
"""

import os
import tempfile
import pytest
import pandas as pd
from services import DataManager


def create_test_csv(num_rows: int, filename: str, encoding='utf-8') -> str:
    """Helper function to create a test CSV file."""
    data = {
        'instruction': [f'Question {i}' for i in range(num_rows)],
        'output': [f'Answer {i}' for i in range(num_rows)],
        'chunk': [f'Reference {i}' for i in range(num_rows)]
    }
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False, encoding=encoding)
    return filename


class TestDataManagerInitialization:
    """Test DataManager initialization and validation."""
    
    def test_init_with_valid_csv(self):
        """Test initialization with valid CSV file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            csv_path = f.name
        
        try:
            create_test_csv(10, csv_path)
            manager = DataManager(csv_path, batch_size=5)
            
            assert manager.csv_path == csv_path
            assert manager.batch_size == 5
            assert manager.total_rows == 10
            assert len(manager.samples) == 0
            assert manager.current_batch == 0
        finally:
            if os.path.exists(csv_path):
                os.remove(csv_path)
    
    def test_init_with_missing_file(self):
        """Test initialization with non-existent file."""
        with pytest.raises(FileNotFoundError):
            DataManager('/nonexistent/file.csv')
    
    def test_init_with_missing_columns(self):
        """Test initialization with CSV missing required columns."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            csv_path = f.name
        
        try:
            # Create CSV with wrong columns
            df = pd.DataFrame({
                'question': ['Q1', 'Q2'],
                'answer': ['A1', 'A2']
            })
            df.to_csv(csv_path, index=False)
            
            with pytest.raises(ValueError, match="缺少必需的列"):
                DataManager(csv_path)
        finally:
            if os.path.exists(csv_path):
                os.remove(csv_path)
    
    def test_init_with_gbk_encoding(self):
        """Test initialization with GBK encoded CSV."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            csv_path = f.name
        
        try:
            # Create GBK encoded CSV
            data = {
                'instruction': ['问题1', '问题2'],
                'output': ['答案1', '答案2'],
                'chunk': ['参考1', '参考2']
            }
            df = pd.DataFrame(data)
            df.to_csv(csv_path, index=False, encoding='gbk')
            
            manager = DataManager(csv_path)
            assert manager.total_rows == 2
        finally:
            if os.path.exists(csv_path):
                os.remove(csv_path)


class TestBatchLoading:
    """Test batch loading functionality."""
    
    def test_load_first_batch(self):
        """Test loading the first batch."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            csv_path = f.name
        
        try:
            create_test_csv(20, csv_path)
            manager = DataManager(csv_path, batch_size=10)
            
            samples = manager.load_next_batch()
            
            assert len(samples) == 10
            assert manager.current_batch == 1
            assert len(manager.samples) == 10
            assert samples[0].id == '0'
            assert samples[9].id == '9'
        finally:
            if os.path.exists(csv_path):
                os.remove(csv_path)
    
    def test_load_multiple_batches(self):
        """Test loading multiple batches."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            csv_path = f.name
        
        try:
            create_test_csv(25, csv_path)
            manager = DataManager(csv_path, batch_size=10)
            
            # Load first batch
            batch1 = manager.load_next_batch()
            assert len(batch1) == 10
            
            # Load second batch
            batch2 = manager.load_next_batch()
            assert len(batch2) == 10
            
            # Load third batch (partial)
            batch3 = manager.load_next_batch()
            assert len(batch3) == 5
            
            # Total samples
            assert len(manager.samples) == 25
        finally:
            if os.path.exists(csv_path):
                os.remove(csv_path)
    
    def test_load_when_no_more_data(self):
        """Test loading when all data is already loaded."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            csv_path = f.name
        
        try:
            create_test_csv(10, csv_path)
            manager = DataManager(csv_path, batch_size=10)
            
            # Load all data
            manager.load_next_batch()
            
            # Try to load more
            batch2 = manager.load_next_batch()
            assert len(batch2) == 0
        finally:
            if os.path.exists(csv_path):
                os.remove(csv_path)


class TestSampleRetrieval:
    """Test sample retrieval functionality."""
    
    def test_get_sample_valid_index(self):
        """Test getting sample with valid index."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            csv_path = f.name
        
        try:
            create_test_csv(10, csv_path)
            manager = DataManager(csv_path, batch_size=10)
            manager.load_next_batch()
            
            sample = manager.get_sample(5)
            assert sample is not None
            assert sample.id == '5'
            assert sample.instruction == 'Question 5'
        finally:
            if os.path.exists(csv_path):
                os.remove(csv_path)
    
    def test_get_sample_invalid_index(self):
        """Test getting sample with invalid index."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            csv_path = f.name
        
        try:
            create_test_csv(10, csv_path)
            manager = DataManager(csv_path, batch_size=10)
            manager.load_next_batch()
            
            assert manager.get_sample(-1) is None
            assert manager.get_sample(100) is None
        finally:
            if os.path.exists(csv_path):
                os.remove(csv_path)


class TestStatusTracking:
    """Test sample status tracking."""
    
    def test_update_sample_status(self):
        """Test updating sample status."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            csv_path = f.name
        
        try:
            create_test_csv(5, csv_path)
            manager = DataManager(csv_path, batch_size=5)
            manager.load_next_batch()
            
            # Update status
            manager.update_sample_status('0', 'corrected')
            assert manager.samples[0].status == 'corrected'
            
            manager.update_sample_status('1', 'discarded')
            assert manager.samples[1].status == 'discarded'
        finally:
            if os.path.exists(csv_path):
                os.remove(csv_path)
    
    def test_update_invalid_status(self):
        """Test updating with invalid status."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            csv_path = f.name
        
        try:
            create_test_csv(5, csv_path)
            manager = DataManager(csv_path, batch_size=5)
            manager.load_next_batch()
            
            with pytest.raises(ValueError, match="Invalid status"):
                manager.update_sample_status('0', 'invalid_status')
        finally:
            if os.path.exists(csv_path):
                os.remove(csv_path)
    
    def test_update_nonexistent_sample(self):
        """Test updating status of non-existent sample."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            csv_path = f.name
        
        try:
            create_test_csv(5, csv_path)
            manager = DataManager(csv_path, batch_size=5)
            manager.load_next_batch()
            
            with pytest.raises(ValueError, match="not found"):
                manager.update_sample_status('999', 'corrected')
        finally:
            if os.path.exists(csv_path):
                os.remove(csv_path)


class TestProgressTracking:
    """Test progress tracking functionality."""
    
    def test_get_progress(self):
        """Test getting progress information."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            csv_path = f.name
        
        try:
            create_test_csv(10, csv_path)
            manager = DataManager(csv_path, batch_size=10)
            manager.load_next_batch()
            
            # Initially no processed samples
            processed, total = manager.get_progress()
            assert processed == 0
            assert total == 10
            
            # Mark some as corrected
            manager.update_sample_status('0', 'corrected')
            manager.update_sample_status('1', 'corrected')
            manager.update_sample_status('2', 'discarded')
            
            processed, total = manager.get_progress()
            assert processed == 3
            assert total == 10
        finally:
            if os.path.exists(csv_path):
                os.remove(csv_path)
    
    def test_should_load_next_batch(self):
        """Test batch loading threshold logic."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            csv_path = f.name
        
        try:
            create_test_csv(50, csv_path)
            manager = DataManager(csv_path, batch_size=20)
            manager.load_next_batch()
            
            # Initially should not load (0 processed, threshold is 10)
            assert not manager.should_load_next_batch()
            
            # Mark 10 samples as corrected (reaches threshold)
            for i in range(10):
                manager.update_sample_status(str(i), 'corrected')
            
            # Should trigger loading
            assert manager.should_load_next_batch()
        finally:
            if os.path.exists(csv_path):
                os.remove(csv_path)
