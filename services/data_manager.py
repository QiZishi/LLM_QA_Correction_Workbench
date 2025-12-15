"""
DataManager for CSV loading and batch management.

Handles CSV file loading, sample status tracking, and batch loading strategy.
"""

import pandas as pd
from typing import List, Optional, Tuple
from models import Sample
from utils.performance import monitor_performance


class DataManager:
    """
    Manages CSV data loading, sample status tracking, and batch strategy.
    
    Attributes:
        csv_path: Path to the CSV file
        batch_size: Number of samples to load per batch
        samples: List of all loaded samples
        current_batch: Current batch number (0-indexed)
        total_rows: Total number of rows in CSV file
    """
    
    def __init__(self, csv_path: str, batch_size: int = 50):
        """
        Initialize DataManager.
        
        Args:
            csv_path: Path to CSV file containing question-answer data
            batch_size: Number of samples to load per batch (default: 50)
        
        Raises:
            FileNotFoundError: If CSV file doesn't exist
            ValueError: If CSV is missing required columns
        """
        self.csv_path = csv_path
        self.batch_size = batch_size
        self.samples: List[Sample] = []
        self.current_batch = 0
        self.total_rows = 0
        
        # Validate CSV file exists and has required columns
        self._validate_csv()
    
    def _validate_csv(self):
        """
        Validate CSV file exists and has required columns.
        
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If required columns are missing
            UnicodeDecodeError: If encoding is invalid
        """
        try:
            # Try UTF-8 first
            df = pd.read_csv(self.csv_path, encoding='utf-8', nrows=1)
        except UnicodeDecodeError:
            # Fallback to GBK encoding
            try:
                df = pd.read_csv(self.csv_path, encoding='gbk', nrows=1)
            except Exception as e:
                raise ValueError(f"无法读取CSV文件，编码错误: {str(e)}")
        except FileNotFoundError:
            raise FileNotFoundError(f"CSV文件未找到: {self.csv_path}")
        except Exception as e:
            raise ValueError(f"CSV文件读取失败: {str(e)}")
        
        # Check required columns
        required_columns = ['instruction', 'output', 'chunk']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise ValueError(
                f"CSV文件缺少必需的列: {missing_columns}. "
                f"需要的列: {required_columns}"
            )
        
        # Get total row count efficiently (without loading all data into memory)
        try:
            # Use iterator to count rows without loading all data
            with open(self.csv_path, 'r', encoding='utf-8') as f:
                self.total_rows = sum(1 for line in f) - 1  # Subtract header row
        except UnicodeDecodeError:
            with open(self.csv_path, 'r', encoding='gbk') as f:
                self.total_rows = sum(1 for line in f) - 1  # Subtract header row
    
    @monitor_performance("load_next_batch")
    def load_next_batch(self) -> List[Sample]:
        """
        Load the next batch of samples from CSV.
        
        Returns:
            List of Sample objects loaded in this batch
        
        Raises:
            ValueError: If no more batches to load
        """
        start_idx = self.current_batch * self.batch_size
        
        if start_idx >= self.total_rows:
            return []  # No more data to load
        
        end_idx = min(start_idx + self.batch_size, self.total_rows)
        
        # Load batch from CSV
        try:
            df = pd.read_csv(
                self.csv_path,
                encoding='utf-8',
                skiprows=range(1, start_idx + 1) if start_idx > 0 else None,
                nrows=end_idx - start_idx
            )
        except UnicodeDecodeError:
            df = pd.read_csv(
                self.csv_path,
                encoding='gbk',
                skiprows=range(1, start_idx + 1) if start_idx > 0 else None,
                nrows=end_idx - start_idx
            )
        
        # Convert to Sample objects
        new_samples = []
        for idx, row in df.iterrows():
            sample = Sample(
                id=str(start_idx + len(new_samples)),
                instruction=str(row['instruction']),
                output=str(row['output']),
                chunk=str(row['chunk'])
            )
            new_samples.append(sample)
        
        # Add to samples list
        self.samples.extend(new_samples)
        self.current_batch += 1
        
        return new_samples
    
    def get_sample(self, index: int) -> Optional[Sample]:
        """
        Get sample by index.
        
        Args:
            index: Index of sample in loaded samples list
        
        Returns:
            Sample object or None if index out of bounds
        """
        if 0 <= index < len(self.samples):
            return self.samples[index]
        return None
    
    def update_sample_status(self, sample_id: str, status: str):
        """
        Update sample status.
        
        Args:
            sample_id: Unique identifier of the sample
            status: New status (unprocessed/corrected/discarded)
        
        Raises:
            ValueError: If sample_id not found or status invalid
        """
        valid_statuses = ['unprocessed', 'corrected', 'discarded']
        if status not in valid_statuses:
            raise ValueError(
                f"Invalid status: {status}. Must be one of {valid_statuses}"
            )
        
        # Find and update sample
        for sample in self.samples:
            if sample.id == sample_id:
                sample.status = status
                return
        
        raise ValueError(f"Sample with id {sample_id} not found")
    
    def get_progress(self) -> Tuple[int, int]:
        """
        Get progress information.
        
        Returns:
            Tuple of (processed_count, total_loaded_count)
        """
        processed_count = sum(
            1 for sample in self.samples
            if sample.status in ['corrected', 'discarded']
        )
        total_loaded = len(self.samples)
        
        return processed_count, total_loaded
    
    def should_load_next_batch(self) -> bool:
        """
        Determine if next batch should be loaded.
        
        Uses threshold: load when processed_count >= (total_loaded - 10)
        
        Returns:
            True if next batch should be loaded, False otherwise
        """
        if self.current_batch * self.batch_size >= self.total_rows:
            return False  # No more data available
        
        processed_count, total_loaded = self.get_progress()
        threshold = total_loaded - 10
        
        return processed_count >= threshold
    
    def load_all_batches_lazy(self):
        """
        Generator that yields batches lazily for very large files.
        
        This is useful for processing extremely large CSV files without
        loading everything into memory at once.
        
        Yields:
            List of Sample objects for each batch
        """
        for batch_num in range((self.total_rows + self.batch_size - 1) // self.batch_size):
            start_idx = batch_num * self.batch_size
            end_idx = min(start_idx + self.batch_size, self.total_rows)
            
            # Load batch from CSV
            try:
                df = pd.read_csv(
                    self.csv_path,
                    encoding='utf-8',
                    skiprows=range(1, start_idx + 1) if start_idx > 0 else None,
                    nrows=end_idx - start_idx
                )
            except UnicodeDecodeError:
                df = pd.read_csv(
                    self.csv_path,
                    encoding='gbk',
                    skiprows=range(1, start_idx + 1) if start_idx > 0 else None,
                    nrows=end_idx - start_idx
                )
            
            # Convert to Sample objects
            batch_samples = []
            for idx, row in df.iterrows():
                sample = Sample(
                    id=str(start_idx + len(batch_samples)),
                    instruction=str(row['instruction']),
                    output=str(row['output']),
                    chunk=str(row['chunk'])
                )
                batch_samples.append(sample)
            
            yield batch_samples
    
    def get_memory_usage_estimate(self) -> dict:
        """
        Estimate memory usage for current loaded samples.
        
        Returns:
            Dictionary with memory usage statistics
        """
        import sys
        
        total_size = 0
        for sample in self.samples:
            total_size += sys.getsizeof(sample.instruction)
            total_size += sys.getsizeof(sample.output)
            total_size += sys.getsizeof(sample.chunk)
            if hasattr(sample, 'edited_instruction') and sample.edited_instruction:
                total_size += sys.getsizeof(sample.edited_instruction)
            if hasattr(sample, 'edited_output') and sample.edited_output:
                total_size += sys.getsizeof(sample.edited_output)
            if hasattr(sample, 'diff_result') and sample.diff_result:
                total_size += sys.getsizeof(sample.diff_result)
        
        return {
            'total_bytes': total_size,
            'total_mb': total_size / (1024 * 1024),
            'samples_loaded': len(self.samples),
            'avg_bytes_per_sample': total_size / len(self.samples) if self.samples else 0
        }
