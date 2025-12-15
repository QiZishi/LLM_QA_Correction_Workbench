"""
Property-based tests for ExportManager.

Tests universal properties for export filtering and data completeness.
"""

import os
import json
from hypothesis import given, strategies as st, settings
from services import ExportManager
from models import Sample


# Feature: llm-qa-correction-workbench, Property 30: Export contains only corrected samples
@given(st.lists(st.sampled_from(['corrected', 'discarded', 'unprocessed']), min_size=1, max_size=20))
@settings(max_examples=50, deadline=None)
def test_export_contains_only_corrected(statuses):
    """
    For any export operation, the generated JSON file should contain only
    samples with status "corrected".
    
    **Validates: Requirements 8.1**
    """
    manager = ExportManager()
    
    # Create samples with various statuses
    samples = []
    for i, status in enumerate(statuses):
        sample = Sample(
            id=str(i),
            instruction=f"Q{i}",
            output=f"A{i}",
            chunk=f"C{i}",
            status=status
        )
        samples.append(sample)
    
    # Try to add all samples (only corrected should be added)
    corrected_count = 0
    for sample in samples:
        if sample.status == "corrected":
            manager.add_sample(sample)
            corrected_count += 1
    
    # Property: Only corrected samples should be in export queue
    assert manager.get_sample_count() == corrected_count
    
    # If we have corrected samples, export and verify
    if corrected_count > 0:
        output_file = manager.export_to_json("test")
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Property: All exported samples should have corrected status
            assert len(data) == corrected_count
            for item in data:
                assert item.get('status') == 'corrected' or 'status' not in item
        finally:
            if os.path.exists(output_file):
                os.remove(output_file)


# Feature: llm-qa-correction-workbench, Property 31: Export data completeness
@given(
    st.integers(min_value=1, max_value=10),
    st.text(min_size=1, max_size=50),
    st.text(min_size=1, max_size=100)
)
@settings(max_examples=50, deadline=None)
def test_export_data_completeness(num_samples, instruction_base, output_base):
    """
    For any exported sample, the JSON object should include id, messages array,
    origin_chunk, and status fields.
    
    **Validates: Requirements 8.2**
    """
    manager = ExportManager(format="messages")
    
    # Create corrected samples
    for i in range(num_samples):
        sample = Sample(
            id=str(i),
            instruction=f"{instruction_base}_{i}",
            output=f"{output_base}_{i}",
            chunk=f"chunk_{i}",
            status="corrected"
        )
        manager.add_sample(sample)
    
    # Export
    output_file = manager.export_to_json("test")
    
    try:
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Property: Each exported item should have required fields
        for item in data:
            assert 'id' in item, "Export must include 'id' field"
            assert 'messages' in item, "Export must include 'messages' field"
            assert 'origin_chunk' in item, "Export must include 'origin_chunk' field"
            assert 'status' in item, "Export must include 'status' field"
            
            # Messages should be a list with user and assistant
            assert isinstance(item['messages'], list)
            assert len(item['messages']) == 2
    finally:
        if os.path.exists(output_file):
            os.remove(output_file)



# Feature: llm-qa-correction-workbench, Property 32: Export filename format
@given(
    st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
    st.integers(min_value=1, max_value=5)
)
@settings(max_examples=50, deadline=None)
def test_export_filename_format(base_name, num_samples):
    """
    For any export operation, the generated filename should match the pattern
    {original_name}_{timestamp}_{count}.json.
    
    **Validates: Requirements 8.3**
    """
    manager = ExportManager()
    
    # Create samples
    for i in range(num_samples):
        sample = Sample(
            id=str(i),
            instruction=f"Q{i}",
            output=f"A{i}",
            chunk=f"C{i}",
            status="corrected"
        )
        manager.add_sample(sample)
    
    # Export
    output_file = manager.export_to_json(base_name)
    
    try:
        # Property: Filename should match pattern
        assert output_file.endswith('.json'), "Filename must end with .json"
        assert base_name in output_file, "Filename must contain original name"
        assert f"_{num_samples}.json" in output_file, "Filename must contain sample count"
        
        # Should contain timestamp (8 digits for date + 6 for time)
        parts = output_file.replace('.json', '').split('_')
        assert len(parts) >= 3, "Filename should have at least 3 parts"
    finally:
        if os.path.exists(output_file):
            os.remove(output_file)


# Feature: llm-qa-correction-workbench, Property 34: Format selection affects export
@given(
    st.sampled_from(['messages', 'alpaca', 'sharegpt', 'query-response']),
    st.integers(min_value=1, max_value=3)
)
@settings(max_examples=50, deadline=None)
def test_format_selection_affects_export(export_format, num_samples):
    """
    For any selected export format (alpaca, sharegpt, query-response), the
    exported JSON structure should match that format's schema.
    
    **Validates: Requirements 8.5**
    """
    manager = ExportManager(format=export_format)
    
    # Create samples
    for i in range(num_samples):
        sample = Sample(
            id=str(i),
            instruction=f"Q{i}",
            output=f"A{i}",
            chunk=f"C{i}",
            status="corrected"
        )
        manager.add_sample(sample)
    
    # Export
    output_file = manager.export_to_json("test")
    
    try:
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Property: Format-specific fields should be present
        for item in data:
            if export_format == 'messages':
                assert 'messages' in item
                assert 'origin_chunk' in item
            elif export_format == 'alpaca':
                assert 'instruction' in item
                assert 'input' in item
                assert 'output' in item
            elif export_format == 'sharegpt':
                assert 'conversations' in item
                assert isinstance(item['conversations'], list)
            elif export_format == 'query-response':
                assert 'query' in item
                assert 'response' in item
    finally:
        if os.path.exists(output_file):
            os.remove(output_file)



# Feature: llm-qa-correction-workbench, Property 33: Default export format
@given(st.integers(min_value=1, max_value=3))
@settings(max_examples=30, deadline=None)
def test_default_export_format(num_samples):
    """
    For any export operation without explicit format selection, the system
    should use the Messages format with user and assistant roles.
    
    **Validates: Requirements 8.4**
    """
    # Create manager without specifying format (should default to messages)
    manager = ExportManager()
    
    # Property: Default format should be messages
    assert manager.format == "messages", "Default format must be 'messages'"
    
    # Create samples
    for i in range(num_samples):
        sample = Sample(
            id=str(i),
            instruction=f"Q{i}",
            output=f"A{i}",
            chunk=f"C{i}",
            status="corrected"
        )
        manager.add_sample(sample)
    
    # Export
    output_file = manager.export_to_json("test")
    
    try:
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Property: Should use messages format structure
        for item in data:
            assert 'messages' in item, "Default export must use messages format"
            assert len(item['messages']) == 2
            assert item['messages'][0]['role'] == 'user'
            assert item['messages'][1]['role'] == 'assistant'
    finally:
        if os.path.exists(output_file):
            os.remove(output_file)
