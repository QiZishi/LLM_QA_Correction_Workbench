"""
End-to-end integration tests for complete workflow.

Tests the full workflow: Load CSV → Edit → Generate preview → Submit → Export
"""

import pytest
import tempfile
import os
import json
from ui.event_handlers import (
    handle_csv_upload,
    load_sample_to_ui,
    handle_generate_preview,
    handle_submit,
    handle_discard,
    handle_export,
    handle_navigation
)


def create_test_csv(num_rows=5):
    """Helper to create a test CSV file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
        f.write("instruction,output,chunk\n")
        for i in range(num_rows):
            f.write(f"Question {i}?,Answer {i} here,Context for question {i}\n")
        return f.name


def test_complete_workflow_single_sample():
    """
    Test complete workflow for a single sample:
    Load CSV → Edit → Generate preview → Submit → Export
    """
    csv_path = create_test_csv(3)
    
    try:
        # Step 1: Load CSV
        app_state, msg = handle_csv_upload(csv_path, batch_size=10)
        assert "成功加载" in msg
        assert len(app_state['samples']) == 3
        assert app_state['current_index'] == 0
        assert app_state['phase'] == 1
        
        # Step 2: Load sample to UI
        instruction, output, reference, progress, sample_list = load_sample_to_ui(app_state)
        assert instruction == "Question 0?"
        assert output == "Answer 0 here"
        assert "Context for question 0" in reference
        
        # Step 3: Edit content
        edited_instruction = "What is Question 0?"
        edited_output = "Answer 0 is here with more details"
        
        # Step 4: Generate preview (transition to Phase 2)
        app_state, original_display, diff_html, phase1_vis, phase2_vis = handle_generate_preview(
            edited_instruction,
            edited_output,
            app_state
        )
        assert app_state['phase'] == 2
        assert phase1_vis == False
        assert phase2_vis == True
        assert diff_html is not None
        
        # Step 5: Submit sample
        app_state, instruction, output, reference, progress, sample_list, phase1_vis, phase2_vis = handle_submit(app_state)
        
        # Verify submission
        assert app_state['phase'] == 1  # Reset to Phase 1
        assert app_state['current_index'] == 1  # Moved to next sample
        assert phase1_vis == True
        assert phase2_vis == False
        
        # Verify sample status
        assert app_state['samples'][0].status == 'corrected'
        
        # Verify progress
        assert "1 / 3" in progress
        
        # Step 6: Export
        file_path, export_msg = handle_export(app_state)
        assert file_path is not None
        assert "成功导出" in export_msg
        
        # Verify export file exists and contains data
        assert os.path.exists(file_path)
        with open(file_path, 'r', encoding='utf-8') as f:
            export_data = json.load(f)
            assert len(export_data) == 1
            # Messages format has messages array
            assert export_data[0]['messages'][0]['content'] == edited_instruction
        
        # Cleanup export file
        os.unlink(file_path)
        
    finally:
        os.unlink(csv_path)


def test_complete_workflow_multiple_samples():
    """
    Test workflow with multiple samples:
    Load → Edit sample 1 → Submit → Edit sample 2 → Submit → Export
    """
    csv_path = create_test_csv(5)
    
    try:
        # Load CSV
        app_state, msg = handle_csv_upload(csv_path, batch_size=10)
        assert len(app_state['samples']) == 5
        
        # Process first sample
        edited_instruction_1 = "Edited Question 0"
        edited_output_1 = "Edited Answer 0"
        
        app_state, *_ = handle_generate_preview(edited_instruction_1, edited_output_1, app_state)
        app_state, *_ = handle_submit(app_state)
        
        assert app_state['samples'][0].status == 'corrected'
        assert app_state['current_index'] == 1
        
        # Process second sample
        edited_instruction_2 = "Edited Question 1"
        edited_output_2 = "Edited Answer 1"
        
        app_state, *_ = handle_generate_preview(edited_instruction_2, edited_output_2, app_state)
        app_state, *_ = handle_submit(app_state)
        
        assert app_state['samples'][1].status == 'corrected'
        assert app_state['current_index'] == 2
        
        # Export
        file_path, export_msg = handle_export(app_state)
        assert file_path is not None
        
        # Verify export contains both samples
        with open(file_path, 'r', encoding='utf-8') as f:
            export_data = json.load(f)
            assert len(export_data) == 2
            assert export_data[0]['messages'][0]['content'] == edited_instruction_1
            assert export_data[1]['messages'][0]['content'] == edited_instruction_2
        
        os.unlink(file_path)
        
    finally:
        os.unlink(csv_path)


def test_workflow_with_discard():
    """
    Test workflow with discarded samples:
    Load → Discard sample 1 → Edit sample 2 → Submit → Export (only sample 2)
    """
    csv_path = create_test_csv(3)
    
    try:
        # Load CSV
        app_state, msg = handle_csv_upload(csv_path, batch_size=10)
        
        # Discard first sample
        app_state, *_ = handle_discard(app_state)
        
        assert app_state['samples'][0].status == 'discarded'
        assert app_state['current_index'] == 1
        
        # Process second sample
        edited_instruction = "Edited Question 1"
        edited_output = "Edited Answer 1"
        
        app_state, *_ = handle_generate_preview(edited_instruction, edited_output, app_state)
        app_state, *_ = handle_submit(app_state)
        
        assert app_state['samples'][1].status == 'corrected'
        
        # Export
        file_path, export_msg = handle_export(app_state)
        assert file_path is not None
        
        # Verify export only contains corrected sample (not discarded)
        with open(file_path, 'r', encoding='utf-8') as f:
            export_data = json.load(f)
            assert len(export_data) == 1
            assert export_data[0]['messages'][0]['content'] == edited_instruction
        
        os.unlink(file_path)
        
    finally:
        os.unlink(csv_path)


def test_batch_loading_workflow():
    """
    Test workflow with automatic batch loading:
    Load small batch → Process samples → Trigger automatic batch load
    """
    csv_path = create_test_csv(25)  # Create 25 samples
    
    try:
        # Load CSV with small batch size
        app_state, msg = handle_csv_upload(csv_path, batch_size=10)
        
        assert len(app_state['samples']) == 10  # Only first batch loaded
        assert app_state['data_manager'].total_rows == 25
        
        # Process samples by generating preview and submitting
        # Threshold is total_loaded - 10, so we need to process all 10 to trigger next batch
        for i in range(10):
            current_sample = app_state['samples'][app_state['current_index']]
            # Generate preview first
            app_state, *_ = handle_generate_preview(
                f"Edited {current_sample.instruction}",
                f"Edited {current_sample.output}",
                app_state
            )
            # Then submit
            app_state, *_ = handle_submit(app_state)
        
        # After processing all 10 samples, next batch should be loaded automatically
        # because processed_count (10) >= threshold (10 - 10 = 0)
        assert len(app_state['samples']) > 10
        
    finally:
        os.unlink(csv_path)


def test_navigation_workflow():
    """
    Test workflow with navigation:
    Load → Navigate forward → Navigate backward → Edit → Submit
    """
    csv_path = create_test_csv(5)
    
    try:
        # Load CSV
        app_state, msg = handle_csv_upload(csv_path, batch_size=10)
        
        # Navigate forward
        app_state, instruction, *_ = handle_navigation("next", app_state)
        assert app_state['current_index'] == 1
        assert instruction == "Question 1?"
        
        # Navigate forward again
        app_state, instruction, *_ = handle_navigation("next", app_state)
        assert app_state['current_index'] == 2
        assert instruction == "Question 2?"
        
        # Navigate backward
        app_state, instruction, *_ = handle_navigation("prev", app_state)
        assert app_state['current_index'] == 1
        assert instruction == "Question 1?"
        
        # Edit and submit
        edited_instruction = "Edited Question 1"
        edited_output = "Edited Answer 1"
        
        app_state, *_ = handle_generate_preview(edited_instruction, edited_output, app_state)
        app_state, *_ = handle_submit(app_state)
        
        # Verify submission
        assert app_state['samples'][1].status == 'corrected'
        assert app_state['current_index'] == 2
        
    finally:
        os.unlink(csv_path)


def test_export_without_corrected_samples():
    """
    Test export when no samples have been corrected.
    """
    csv_path = create_test_csv(3)
    
    try:
        # Load CSV
        app_state, msg = handle_csv_upload(csv_path, batch_size=10)
        
        # Try to export without correcting any samples
        file_path, export_msg = handle_export(app_state)
        
        # Should return None and warning message
        assert file_path is None
        assert "没有已校正的样本" in export_msg
        
    finally:
        os.unlink(csv_path)


def test_phase_transitions():
    """
    Test phase transitions throughout workflow:
    Phase 1 → Generate preview → Phase 2 → Submit → Phase 1
    """
    csv_path = create_test_csv(2)
    
    try:
        # Load CSV (starts in Phase 1)
        app_state, msg = handle_csv_upload(csv_path, batch_size=10)
        assert app_state['phase'] == 1
        
        # Generate preview (transition to Phase 2)
        app_state, *_, phase1_vis, phase2_vis = handle_generate_preview(
            "Edited Question",
            "Edited Answer",
            app_state
        )
        assert app_state['phase'] == 2
        assert phase1_vis == False
        assert phase2_vis == True
        
        # Submit (transition back to Phase 1)
        app_state, *_, phase1_vis, phase2_vis = handle_submit(app_state)
        assert app_state['phase'] == 1
        assert phase1_vis == True
        assert phase2_vis == False
        
        # Navigate (should stay in Phase 1)
        app_state, *_ = handle_navigation("prev", app_state)
        assert app_state['phase'] == 1
        
    finally:
        os.unlink(csv_path)


def test_markdown_and_latex_preservation():
    """
    Test that Markdown and LaTeX are preserved through the workflow.
    """
    # Create CSV with Markdown and LaTeX
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
        f.write("instruction,output,chunk\n")
        f.write("What is $E=mc^2$?,**Einstein's** equation: $E=mc^2$,Context with $\\alpha$\n")
        csv_path = f.name
    
    try:
        # Load CSV
        app_state, msg = handle_csv_upload(csv_path, batch_size=10)
        
        # Load sample
        instruction, output, reference, *_ = load_sample_to_ui(app_state)
        
        # Verify LaTeX is preserved in raw data
        assert "$E=mc^2$" in instruction
        assert "$E=mc^2$" in output
        # Reference is rendered HTML, so LaTeX may be converted to placeholder
        assert "Context" in reference  # Just check context is there
        
        # Edit with more Markdown
        edited_output = "**Einstein's** equation: $E=mc^2$ and *more* details"
        
        # Generate preview
        app_state, *_ = handle_generate_preview(instruction, edited_output, app_state)
        
        # Submit
        app_state, *_ = handle_submit(app_state)
        
        # Export
        file_path, export_msg = handle_export(app_state)
        
        # Verify Markdown/LaTeX preserved in export
        with open(file_path, 'r', encoding='utf-8') as f:
            export_data = json.load(f)
            assert "$E=mc^2$" in export_data[0]['messages'][0]['content']
        
        os.unlink(file_path)
        
    finally:
        os.unlink(csv_path)
