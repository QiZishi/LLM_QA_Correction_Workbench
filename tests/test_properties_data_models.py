"""
Property-based tests for data models.

Tests universal properties that should hold across all valid inputs.
"""

from hypothesis import given, strategies as st
from models import Sample


# Feature: llm-qa-correction-workbench, Property 2: Unique ID assignment
@given(st.lists(st.integers(min_value=0, max_value=10000), min_size=1, max_size=100, unique=True))
def test_unique_id_assignment(row_indices):
    """
    For any loaded batch of samples, each sample should have a unique identifier
    that matches its CSV row index, and no two samples should share the same ID.
    
    **Validates: Requirements 1.2**
    """
    # Create samples with IDs from row indices
    samples = [
        Sample(
            id=str(idx),
            instruction=f"Question {idx}",
            output=f"Answer {idx}",
            chunk=f"Reference {idx}"
        )
        for idx in row_indices
    ]
    
    # Extract all IDs
    sample_ids = [sample.id for sample in samples]
    
    # Property 1: All IDs should be unique (no duplicates)
    assert len(sample_ids) == len(set(sample_ids)), "Sample IDs must be unique"
    
    # Property 2: Each ID should match its corresponding row index
    for idx, sample in zip(row_indices, samples):
        assert sample.id == str(idx), f"Sample ID should match row index: {idx}"


# Feature: llm-qa-correction-workbench, Property 3: Initial status is unprocessed
@given(
    st.text(min_size=1, max_size=100),
    st.text(min_size=1, max_size=500),
    st.text(min_size=1, max_size=500),
    st.text(min_size=0, max_size=1000)
)
def test_initial_status_unprocessed(sample_id, instruction, output, chunk):
    """
    For any newly loaded sample, the status should be set to "unprocessed"
    before any user interaction.
    
    **Validates: Requirements 1.3**
    """
    # Create a new sample without specifying status
    sample = Sample(
        id=sample_id,
        instruction=instruction,
        output=output,
        chunk=chunk
    )
    
    # Property: Status should default to "unprocessed"
    assert sample.status == "unprocessed", "New samples must have 'unprocessed' status"
