"""
Validation utilities for input data.

Provides validation functions for CSV structure, tag closure, and content.
"""

import re
from typing import Tuple, List


def validate_tag_closure(text: str) -> Tuple[bool, str]:
    """
    Validate that all <false> and <true> tags are properly closed.
    
    Args:
        text: Text content to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not text:
        return True, ""
    
    # Count opening and closing tags
    false_open = len(re.findall(r'<false>', text))
    false_close = len(re.findall(r'</false>', text))
    true_open = len(re.findall(r'<true>', text))
    true_close = len(re.findall(r'</true>', text))
    
    errors = []
    
    if false_open != false_close:
        errors.append(f"<false> 标签不匹配: {false_open} 个开始标签, {false_close} 个结束标签")
    
    if true_open != true_close:
        errors.append(f"<true> 标签不匹配: {true_open} 个开始标签, {true_close} 个结束标签")
    
    if errors:
        return False, "; ".join(errors)
    
    return True, ""


def validate_csv_columns(columns: List[str]) -> Tuple[bool, str]:
    """
    Validate that CSV has required columns.
    
    Args:
        columns: List of column names from CSV
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    required_columns = ['instruction', 'output', 'chunk']
    missing_columns = [col for col in required_columns if col not in columns]
    
    if missing_columns:
        return False, f"缺少必需的列: {missing_columns}"
    
    return True, ""


def validate_content_not_empty(content: str, field_name: str = "内容") -> Tuple[bool, str]:
    """
    Validate that content is not empty or whitespace-only.
    
    Args:
        content: Content to validate
        field_name: Name of the field for error message
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not content or not content.strip():
        return False, f"{field_name}不能为空"
    
    return True, ""


def validate_export_preconditions(corrected_count: int) -> Tuple[bool, str]:
    """
    Validate preconditions for export operation.
    
    Args:
        corrected_count: Number of corrected samples
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if corrected_count == 0:
        return False, "没有已校正的样本可导出"
    
    return True, ""


def validate_batch_size(batch_size: int) -> Tuple[bool, str]:
    """
    Validate batch size parameter.
    
    Args:
        batch_size: Batch size to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if batch_size < 1:
        return False, "批量大小必须大于0"
    
    if batch_size > 1000:
        return False, "批量大小不能超过1000"
    
    return True, ""


def validate_index_bounds(index: int, total: int) -> Tuple[bool, str]:
    """
    Validate that index is within bounds.
    
    Args:
        index: Index to validate
        total: Total number of items
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if index < 0:
        return False, "索引不能为负数"
    
    if index >= total:
        return False, f"索引 {index} 超出范围 (总数: {total})"
    
    return True, ""


def auto_fix_malformed_tags(text: str) -> str:
    """
    Attempt to auto-fix malformed tags.
    
    Args:
        text: Text with potentially malformed tags
    
    Returns:
        Text with fixed tags
    """
    if not text:
        return text
    
    # Fix unclosed <false> tags
    false_open = len(re.findall(r'<false>', text))
    false_close = len(re.findall(r'</false>', text))
    
    if false_open > false_close:
        # Add missing closing tags at the end
        text += '</false>' * (false_open - false_close)
    
    # Fix unclosed <true> tags
    true_open = len(re.findall(r'<true>', text))
    true_close = len(re.findall(r'</true>', text))
    
    if true_open > true_close:
        # Add missing closing tags at the end
        text += '</true>' * (true_open - true_close)
    
    return text
