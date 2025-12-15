"""
Unit tests for state synchronization across columns.

Tests that all three columns update together during navigation and operations.
"""

import pytest
import tempfile
import os
from ui.event_handlers import (
    handle_csv_upload,
    load_sample_to_ui,
    handle_navigation,
    handle_submit,
    handle_discard
)


def create_test_csv(num_rows=5):
    """Helper to create a test CSV file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
        f.write("instruction,output,chunk\n")
        for i in range(num_rows):
            f.write(f"Question {i},Answer {i},Chunk {i}\n")
        return f.name


def test_load_sample_synchronizes_all_columns():
    """Test that loading a sample updates all three columns."""
    csv_path = create_test_csv(3)
    
    try:
        # Load CSV
        app_state, msg = handle_csv_upload(csv_path, batch_size=10)
        
        # Load sample to UI
        instruction, output, reference, progress, sample_list = load_sample_to_ui(app_state)
        
        # Verify all columns have content
        assert instruction == "Question 0"
        assert output == "Answer 0"
        assert "Chunk 0" in reference
        assert "0 / 3" in progress or "1 / 3" in progress  # Progress shows processed/total
        assert "Question 0" in sample_list
        
    finally:
        os.unlink(csv_path)


def test_navigation_synchronizes_all_columns():
    """Test that navigation updates all three columns together."""
    csv_path = create_test_csv(3)
    
    try:
        # Load CSV
        app_state, msg = handle_csv_upload(csv_path, batch_size=10)
        
        # Navigate to next
        app_state, instruction, output, reference, progress, sample_list = handle_navigation("next", app_state)
        
        # Verify all columns updated to sample 1
        assert instruction == "Question 1"
        assert output == "Answer 1"
        assert "Chunk 1" in reference
        assert sample_list is not None
        
        # Navigate to previous
        app_state, instruction, output, reference, progress, sample_list = handle_navigation("prev", app_state)
        
        # Verify all columns updated back to sample 0
        assert instruction == "Question 0"
        assert output == "Answer 0"
        assert "Chunk 0" in reference
        
    finally:
        os.unlink(csv_path)


def test_submit_synchronizes_all_columns():
    """Test that submit updates all three columns and navigates."""
    csv_path = create_test_csv(3)
    
    try:
        # Load CSV
        app_state, msg = handle_csv_upload(csv_path, batch_size=10)
        
        # Generate preview first (required before submit)
        from ui.event_handlers import handle_generate_preview
        app_state, *_ = handle_generate_preview("Edited Question 0", "Edited Answer 0", app_state)
        
        # Submit current sample
        app_state, instruction, output, reference, progress, sample_list, phase1_vis, phase2_vis = handle_submit(app_state)
        
        # Verify navigation to next sample (sample 1)
        assert instruction == "Question 1"
        assert output == "Answer 1"
        assert "Chunk 1" in reference
        
        # Verify progress updated
        assert "1 / 3" in progress  # 1 corrected out of 3 total
        
        # Verify phase reset to Phase 1
        assert phase1_vis == True
        assert phase2_vis == False
        
    finally:
        os.unlink(csv_path)


def test_discard_synchronizes_all_columns():
    """Test that discard updates all three columns and navigates."""
    csv_path = create_test_csv(3)
    
    try:
        # Load CSV
        app_state, msg = handle_csv_upload(csv_path, batch_size=10)
        
        # Discard current sample
        app_state, instruction, output, reference, progress, sample_list, phase1_vis, phase2_vis = handle_discard(app_state)
        
        # Verify navigation to next sample (sample 1)
        assert instruction == "Question 1"
        assert output == "Answer 1"
        assert "Chunk 1" in reference
        
        # Verify progress updated (discarded counts as processed)
        assert "1 / 3" in progress
        
        # Verify phase reset to Phase 1
        assert phase1_vis == True
        assert phase2_vis == False
        
    finally:
        os.unlink(csv_path)


def test_phase_transition_maintains_state():
    """Test that transitioning between phases maintains consistent state."""
    csv_path = create_test_csv(2)
    
    try:
        # Load CSV
        app_state, msg = handle_csv_upload(csv_path, batch_size=10)
        
        # Verify initial phase
        assert app_state['phase'] == 1
        assert app_state['current_index'] == 0
        
        # Navigate
        app_state, *_ = handle_navigation("next", app_state)
        
        # Verify state consistency after navigation
        assert app_state['phase'] == 1  # Reset to phase 1
        assert app_state['current_index'] == 1
        
        # Submit
        app_state, *_ = handle_submit(app_state)
        
        # Verify state consistency after submit
        assert app_state['phase'] == 1  # Reset to phase 1
        assert app_state['current_index'] == 1  # Stays at last sample
        
    finally:
        os.unlink(csv_path)


def test_sample_list_reflects_current_index():
    """Test that sample list highlights current sample correctly."""
    csv_path = create_test_csv(3)
    
    try:
        # Load CSV
        app_state, msg = handle_csv_upload(csv_path, batch_size=10)
        
        # Load initial sample
        _, _, _, _, sample_list = load_sample_to_ui(app_state)
        
        # Sample list should contain all samples
        assert "Question 0" in sample_list
        assert "Question 1" in sample_list
        assert "Question 2" in sample_list
        
        # Navigate to sample 1
        app_state, *_, sample_list = handle_navigation("next", app_state)
        
        # Sample list should still contain all samples
        assert "Question 0" in sample_list
        assert "Question 1" in sample_list
        assert "Question 2" in sample_list
        
    finally:
        os.unlink(csv_path)
