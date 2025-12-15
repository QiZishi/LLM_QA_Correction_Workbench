"""
Unit tests for validation utilities.

Tests validation functions for tags, content, and preconditions.
"""

import pytest
from utils.validation import (
    validate_tag_closure,
    validate_csv_columns,
    validate_content_not_empty,
    validate_export_preconditions,
    validate_batch_size,
    validate_index_bounds,
    auto_fix_malformed_tags
)


def test_validate_tag_closure_valid():
    """Test validation of properly closed tags."""
    text = "This is <false>wrong</false> and <true>correct</true>"
    is_valid, error_msg = validate_tag_closure(text)
    assert is_valid == True
    assert error_msg == ""


def test_validate_tag_closure_unclosed_false():
    """Test validation of unclosed <false> tag."""
    text = "This is <false>wrong and <true>correct</true>"
    is_valid, error_msg = validate_tag_closure(text)
    assert is_valid == False
    assert "<false>" in error_msg


def test_validate_tag_closure_unclosed_true():
    """Test validation of unclosed <true> tag."""
    text = "This is <false>wrong</false> and <true>correct"
    is_valid, error_msg = validate_tag_closure(text)
    assert is_valid == False
    assert "<true>" in error_msg


def test_validate_tag_closure_multiple_unclosed():
    """Test validation of multiple unclosed tags."""
    text = "<false>wrong <true>correct"
    is_valid, error_msg = validate_tag_closure(text)
    assert is_valid == False
    assert "<false>" in error_msg
    assert "<true>" in error_msg


def test_validate_tag_closure_empty_text():
    """Test validation of empty text."""
    is_valid, error_msg = validate_tag_closure("")
    assert is_valid == True
    assert error_msg == ""


def test_validate_csv_columns_valid():
    """Test validation of valid CSV columns."""
    columns = ['instruction', 'output', 'chunk', 'extra']
    is_valid, error_msg = validate_csv_columns(columns)
    assert is_valid == True
    assert error_msg == ""


def test_validate_csv_columns_missing():
    """Test validation of CSV with missing columns."""
    columns = ['instruction', 'output']
    is_valid, error_msg = validate_csv_columns(columns)
    assert is_valid == False
    assert "chunk" in error_msg


def test_validate_content_not_empty_valid():
    """Test validation of non-empty content."""
    is_valid, error_msg = validate_content_not_empty("Some content", "Field")
    assert is_valid == True
    assert error_msg == ""


def test_validate_content_not_empty_empty():
    """Test validation of empty content."""
    is_valid, error_msg = validate_content_not_empty("", "Field")
    assert is_valid == False
    assert "Field" in error_msg


def test_validate_content_not_empty_whitespace():
    """Test validation of whitespace-only content."""
    is_valid, error_msg = validate_content_not_empty("   \n\t  ", "Field")
    assert is_valid == False
    assert "Field" in error_msg


def test_validate_export_preconditions_valid():
    """Test validation of export with corrected samples."""
    is_valid, error_msg = validate_export_preconditions(5)
    assert is_valid == True
    assert error_msg == ""


def test_validate_export_preconditions_no_samples():
    """Test validation of export with no corrected samples."""
    is_valid, error_msg = validate_export_preconditions(0)
    assert is_valid == False
    assert "没有已校正的样本" in error_msg


def test_validate_batch_size_valid():
    """Test validation of valid batch sizes."""
    assert validate_batch_size(50)[0] == True
    assert validate_batch_size(1)[0] == True
    assert validate_batch_size(1000)[0] == True


def test_validate_batch_size_invalid():
    """Test validation of invalid batch sizes."""
    is_valid, error_msg = validate_batch_size(0)
    assert is_valid == False
    
    is_valid, error_msg = validate_batch_size(-10)
    assert is_valid == False
    
    is_valid, error_msg = validate_batch_size(1001)
    assert is_valid == False


def test_validate_index_bounds_valid():
    """Test validation of valid indices."""
    is_valid, error_msg = validate_index_bounds(0, 10)
    assert is_valid == True
    
    is_valid, error_msg = validate_index_bounds(5, 10)
    assert is_valid == True
    
    is_valid, error_msg = validate_index_bounds(9, 10)
    assert is_valid == True


def test_validate_index_bounds_invalid():
    """Test validation of invalid indices."""
    is_valid, error_msg = validate_index_bounds(-1, 10)
    assert is_valid == False
    
    is_valid, error_msg = validate_index_bounds(10, 10)
    assert is_valid == False
    
    is_valid, error_msg = validate_index_bounds(100, 10)
    assert is_valid == False


def test_auto_fix_malformed_tags_unclosed_false():
    """Test auto-fixing of unclosed <false> tags."""
    text = "This is <false>wrong"
    fixed = auto_fix_malformed_tags(text)
    assert fixed == "This is <false>wrong</false>"
    
    # Verify it's now valid
    is_valid, _ = validate_tag_closure(fixed)
    assert is_valid == True


def test_auto_fix_malformed_tags_unclosed_true():
    """Test auto-fixing of unclosed <true> tags."""
    text = "This is <true>correct"
    fixed = auto_fix_malformed_tags(text)
    assert fixed == "This is <true>correct</true>"
    
    # Verify it's now valid
    is_valid, _ = validate_tag_closure(fixed)
    assert is_valid == True


def test_auto_fix_malformed_tags_multiple():
    """Test auto-fixing of multiple unclosed tags."""
    text = "<false>wrong <true>correct"
    fixed = auto_fix_malformed_tags(text)
    assert "</false>" in fixed
    assert "</true>" in fixed
    
    # Verify it's now valid
    is_valid, _ = validate_tag_closure(fixed)
    assert is_valid == True


def test_auto_fix_malformed_tags_already_valid():
    """Test auto-fixing doesn't change valid tags."""
    text = "This is <false>wrong</false> and <true>correct</true>"
    fixed = auto_fix_malformed_tags(text)
    assert fixed == text


def test_auto_fix_malformed_tags_empty():
    """Test auto-fixing of empty text."""
    fixed = auto_fix_malformed_tags("")
    assert fixed == ""
