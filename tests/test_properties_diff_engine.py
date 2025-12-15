"""
Property-based tests for DiffEngine.

Tests universal properties for text comparison and diff generation.
"""

from hypothesis import given, strategies as st, settings, assume
from services import DiffEngine


# Feature: llm-qa-correction-workbench, Property 13: Deletion tagging
@given(
    st.text(min_size=1, max_size=500),
    st.text(min_size=1, max_size=100)
)
@settings(max_examples=100, deadline=None)
def test_deletion_tagging(original_base, deleted_portion):
    """
    For any text comparison where content exists in the original but not in
    the modified version, the diff algorithm should wrap the deleted content
    with <false>...</false> tags.
    
    **Validates: Requirements 4.2**
    """
    # Ensure deleted_portion is actually in the combined text
    full_original = original_base + deleted_portion
    modified = original_base
    
    diff_engine = DiffEngine()
    result = diff_engine.compute_diff(full_original, modified)
    
    # Property: Deleted content should be wrapped in false tags
    # The result should contain false tags if content was deleted
    if deleted_portion.strip():  # Only check if there's meaningful content
        assert '<false>' in result, "Deleted content should have <false> tags"
        assert '</false>' in result, "Deleted content should have </false> tags"


# Feature: llm-qa-correction-workbench, Property 14: Addition tagging
@given(
    st.text(min_size=1, max_size=500),
    st.text(min_size=1, max_size=100)
)
@settings(max_examples=100, deadline=None)
def test_addition_tagging(original_base, added_portion):
    """
    For any text comparison where content exists in the modified version but
    not in the original, the diff algorithm should wrap the added content
    with <true>...</true> tags.
    
    **Validates: Requirements 4.3**
    """
    original = original_base
    full_modified = original_base + added_portion
    
    diff_engine = DiffEngine()
    result = diff_engine.compute_diff(original, full_modified)
    
    # Property: Added content should be wrapped in true tags
    if added_portion.strip():  # Only check if there's meaningful content
        assert '<true>' in result, "Added content should have <true> tags"
        assert '</true>' in result, "Added content should have </true> tags"


# Feature: llm-qa-correction-workbench, Property 15: Unchanged content preservation
@given(st.text(min_size=1, max_size=1000))
@settings(max_examples=100, deadline=None)
def test_unchanged_content_preservation(text):
    """
    For any text comparison where content is identical in both original and
    modified versions, the diff algorithm should preserve the content without
    adding any tags.
    
    **Validates: Requirements 4.4**
    """
    diff_engine = DiffEngine()
    result = diff_engine.compute_diff(text, text)
    
    # Property: Identical text should have no tags
    assert '<false>' not in result, "Unchanged content should not have <false> tags"
    assert '<true>' not in result, "Unchanged content should not have <true> tags"
    assert result == text, "Unchanged content should be preserved exactly"


# Additional property: Tag validation
@given(
    st.text(min_size=0, max_size=500),
    st.text(min_size=0, max_size=500)
)
@settings(max_examples=100, deadline=None)
def test_tags_are_always_balanced(original, modified):
    """
    For any diff result, all tags should be properly balanced (opened and closed).
    """
    # Skip if texts are too similar or empty
    assume(len(original) > 0 or len(modified) > 0)
    
    diff_engine = DiffEngine()
    result = diff_engine.compute_diff(original, modified)
    
    # Property: Tags should be balanced
    assert diff_engine.validate_tags(result), "All tags must be properly balanced"


# Additional property: Strip tags returns clean text
@given(
    st.text(min_size=1, max_size=500),
    st.text(min_size=1, max_size=500)
)
@settings(max_examples=100, deadline=None)
def test_strip_tags_removes_all_tags(original, modified):
    """
    For any diff result, stripping tags should remove all <false> and <true> tags.
    """
    diff_engine = DiffEngine()
    result = diff_engine.compute_diff(original, modified)
    stripped = diff_engine.strip_tags(result)
    
    # Property: Stripped text should have no tags
    assert '<false>' not in stripped
    assert '</false>' not in stripped
    assert '<true>' not in stripped
    assert '</true>' not in stripped
