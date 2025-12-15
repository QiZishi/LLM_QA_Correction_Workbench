"""
Unit tests for ExportManager.

Tests specific examples for export formats and error handling.
"""

import os
import json
import pytest
from services import ExportManager
from models import Sample


class TestExportManagerInitialization:
    """Test ExportManager initialization."""
    
    def test_init_with_valid_format(self):
        """Test initialization with valid format."""
        manager = ExportManager(format="messages")
        assert manager.format == "messages"
        assert manager.get_sample_count() == 0
    
    def test_init_with_invalid_format(self):
        """Test initialization with invalid format."""
        with pytest.raises(ValueError, match="Invalid format"):
            ExportManager(format="invalid")
    
    def test_default_format(self):
        """Test default format is messages."""
        manager = ExportManager()
        assert manager.format == "messages"


class TestSampleAddition:
    """Test adding samples to export queue."""
    
    def test_add_corrected_sample(self):
        """Test adding a corrected sample."""
        manager = ExportManager()
        sample = Sample(
            id="0",
            instruction="Q",
            output="A",
            chunk="C",
            status="corrected"
        )
        
        manager.add_sample(sample)
        assert manager.get_sample_count() == 1
    
    def test_add_non_corrected_sample(self):
        """Test adding a non-corrected sample raises error."""
        manager = ExportManager()
        sample = Sample(
            id="0",
            instruction="Q",
            output="A",
            chunk="C",
            status="unprocessed"
        )
        
        with pytest.raises(ValueError, match="Only corrected samples"):
            manager.add_sample(sample)
    
    def test_add_multiple_samples(self):
        """Test adding multiple samples."""
        manager = ExportManager()
        
        for i in range(5):
            sample = Sample(
                id=str(i),
                instruction=f"Q{i}",
                output=f"A{i}",
                chunk=f"C{i}",
                status="corrected"
            )
            manager.add_sample(sample)
        
        assert manager.get_sample_count() == 5


class TestMessagesFormat:
    """Test Messages format conversion."""
    
    def test_format_messages(self):
        """Test Messages format conversion."""
        manager = ExportManager(format="messages")
        sample = Sample(
            id="0",
            instruction="Question",
            output="Answer",
            chunk="Reference",
            status="corrected"
        )
        
        result = manager.format_messages(sample)
        
        assert result['id'] == "0"
        assert 'messages' in result
        assert len(result['messages']) == 2
        assert result['messages'][0]['role'] == 'user'
        assert result['messages'][1]['role'] == 'assistant'
        assert result['origin_chunk'] == "Reference"
        assert result['status'] == "corrected"


class TestAlpacaFormat:
    """Test Alpaca format conversion."""
    
    def test_format_alpaca(self):
        """Test Alpaca format conversion."""
        manager = ExportManager(format="alpaca")
        sample = Sample(
            id="0",
            instruction="Question",
            output="Answer",
            chunk="Reference",
            status="corrected"
        )
        
        result = manager.format_alpaca(sample)
        
        assert result['id'] == "0"
        assert result['instruction'] == "Question"
        assert result['input'] == ""
        assert result['output'] == "Answer"


class TestShareGPTFormat:
    """Test ShareGPT format conversion."""
    
    def test_format_sharegpt(self):
        """Test ShareGPT format conversion."""
        manager = ExportManager(format="sharegpt")
        sample = Sample(
            id="0",
            instruction="Question",
            output="Answer",
            chunk="Reference",
            status="corrected"
        )
        
        result = manager.format_sharegpt(sample)
        
        assert result['id'] == "0"
        assert 'conversations' in result
        assert len(result['conversations']) == 2
        assert result['conversations'][0]['from'] == 'human'
        assert result['conversations'][1]['from'] == 'gpt'


class TestQueryResponseFormat:
    """Test Query-Response format conversion."""
    
    def test_format_query_response(self):
        """Test Query-Response format conversion."""
        manager = ExportManager(format="query-response")
        sample = Sample(
            id="0",
            instruction="Question",
            output="Answer",
            chunk="Reference",
            status="corrected"
        )
        
        result = manager.format_query_response(sample)
        
        assert result['id'] == "0"
        assert result['query'] == "Question"
        assert result['response'] == "Answer"


class TestFileExport:
    """Test JSON file export."""
    
    def test_export_to_json(self):
        """Test exporting to JSON file."""
        manager = ExportManager()
        sample = Sample(
            id="0",
            instruction="Q",
            output="A",
            chunk="C",
            status="corrected"
        )
        manager.add_sample(sample)
        
        output_file = manager.export_to_json("test")
        
        try:
            assert os.path.exists(output_file)
            assert output_file.endswith('.json')
            
            with open(output_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            assert len(data) == 1
            assert data[0]['id'] == "0"
        finally:
            if os.path.exists(output_file):
                os.remove(output_file)
    
    def test_export_empty_queue(self):
        """Test exporting with no samples raises error."""
        manager = ExportManager()
        
        with pytest.raises(ValueError, match="没有已校正的样本"):
            manager.export_to_json("test")
    
    def test_export_filename_format(self):
        """Test exported filename format."""
        manager = ExportManager()
        sample = Sample(
            id="0",
            instruction="Q",
            output="A",
            chunk="C",
            status="corrected"
        )
        manager.add_sample(sample)
        
        output_file = manager.export_to_json("mydata.csv")
        
        try:
            # Should contain base name, timestamp, and count
            assert 'mydata' in output_file
            assert '_1.json' in output_file
        finally:
            if os.path.exists(output_file):
                os.remove(output_file)


class TestUtilityMethods:
    """Test utility methods."""
    
    def test_clear(self):
        """Test clearing the export queue."""
        manager = ExportManager()
        
        for i in range(3):
            sample = Sample(
                id=str(i),
                instruction=f"Q{i}",
                output=f"A{i}",
                chunk=f"C{i}",
                status="corrected"
            )
            manager.add_sample(sample)
        
        assert manager.get_sample_count() == 3
        
        manager.clear()
        assert manager.get_sample_count() == 0
    
    def test_get_sample_count(self):
        """Test getting sample count."""
        manager = ExportManager()
        assert manager.get_sample_count() == 0
        
        sample = Sample(
            id="0",
            instruction="Q",
            output="A",
            chunk="C",
            status="corrected"
        )
        manager.add_sample(sample)
        
        assert manager.get_sample_count() == 1
