"""
Unit tests for CSV loading error handling.

Tests various error conditions when loading CSV files.
"""

import pytest
import tempfile
import os
from ui.event_handlers import handle_csv_upload


def test_handle_csv_upload_no_file():
    """Test handling when no file is provided."""
    app_state, message = handle_csv_upload(None)
    
    assert app_state['data_manager'] is None
    assert app_state['samples'] == []
    assert "请先上传CSV文件" in message


def test_handle_csv_upload_file_not_found():
    """Test handling when file doesn't exist."""
    app_state, message = handle_csv_upload("/nonexistent/file.csv")
    
    assert app_state['data_manager'] is None
    assert "文件未找到" in message or "CSV格式错误" in message


def test_handle_csv_upload_missing_columns():
    """Test handling when CSV is missing required columns."""
    # Create temp CSV with wrong columns
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
        f.write("wrong_col1,wrong_col2\n")
        f.write("value1,value2\n")
        temp_path = f.name
    
    try:
        app_state, message = handle_csv_upload(temp_path)
        
        assert app_state['data_manager'] is None
        assert "CSV格式错误" in message
        assert "缺少必需的列" in message
    finally:
        os.unlink(temp_path)


def test_handle_csv_upload_empty_file():
    """Test handling when CSV file is empty."""
    # Create temp empty CSV with headers only
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
        f.write("instruction,output,chunk\n")
        temp_path = f.name
    
    try:
        app_state, message = handle_csv_upload(temp_path)
        
        assert app_state['data_manager'] is None
        assert "CSV文件为空" in message
    finally:
        os.unlink(temp_path)


def test_handle_csv_upload_valid_file():
    """Test successful CSV loading."""
    # Create temp valid CSV
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
        f.write("instruction,output,chunk\n")
        f.write("What is AI?,AI is artificial intelligence,Context about AI\n")
        f.write("What is ML?,ML is machine learning,Context about ML\n")
        temp_path = f.name
    
    try:
        app_state, message = handle_csv_upload(temp_path, batch_size=10)
        
        assert app_state['data_manager'] is not None
        assert len(app_state['samples']) == 2
        assert "成功加载" in message
        assert app_state['batch_size'] == 10
        assert app_state['export_format'] == "messages"
    finally:
        os.unlink(temp_path)


def test_handle_csv_upload_encoding_utf8():
    """Test CSV loading with UTF-8 encoding."""
    # Create temp CSV with UTF-8 Chinese characters
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
        f.write("instruction,output,chunk\n")
        f.write("什么是人工智能？,人工智能是...,关于AI的上下文\n")
        temp_path = f.name
    
    try:
        app_state, message = handle_csv_upload(temp_path)
        
        assert app_state['data_manager'] is not None
        assert len(app_state['samples']) == 1
        assert "成功加载" in message
    finally:
        os.unlink(temp_path)


def test_handle_csv_upload_large_batch():
    """Test CSV loading with custom batch size."""
    # Create temp CSV with multiple rows
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
        f.write("instruction,output,chunk\n")
        for i in range(100):
            f.write(f"Question {i},Answer {i},Chunk {i}\n")
        temp_path = f.name
    
    try:
        app_state, message = handle_csv_upload(temp_path, batch_size=30)
        
        assert app_state['data_manager'] is not None
        assert len(app_state['samples']) == 30  # Only first batch loaded
        assert app_state['data_manager'].total_rows == 100
        assert "成功加载" in message
    finally:
        os.unlink(temp_path)
