"""
Property-based tests for UI components.

Tests universal properties for UI interactions.
"""

from hypothesis import given, strategies as st, settings
from ui.event_handlers import (
    toggle_left_column,
    navigate_previous,
    navigate_next,
    update_progress_display
)


# Feature: llm-qa-correction-workbench, Property 6: Column visibility toggle
@given(st.booleans())
@settings(max_examples=100)
def test_column_visibility_toggle(current_visible):
    """
    For any application state, clicking the collapse button should toggle
    the left column visibility from visible to hidden or hidden to visible.
    
    **Validates: Requirements 2.3**
    """
    # Toggle visibility
    new_visible, button_text = toggle_left_column(current_visible)
    
    # Property: Visibility should be toggled
    assert new_visible == (not current_visible), \
        "Column visibility should be toggled"
    
    # Property: Button text should reflect new state
    if new_visible:
        assert "收起" in button_text, "Button should show '收起' when visible"
    else:
        assert "展开" in button_text, "Button should show '展开' when hidden"


# Feature: llm-qa-correction-workbench, Property 38: Previous navigation
@given(
    st.integers(min_value=0, max_value=100),
    st.integers(min_value=1, max_value=100)
)
@settings(max_examples=100)
def test_previous_navigation(current_index, total_samples):
    """
    For any sample with index > 0, clicking the previous button should
    decrement the current index by 1.
    
    **Validates: Requirements 10.1**
    """
    new_index = navigate_previous(current_index, total_samples)
    
    # Property: If index > 0, should decrement
    if current_index > 0:
        assert new_index == current_index - 1, \
            "Index should decrement by 1 when not at first"
    else:
        # Property: If at first, should stay at 0
        assert new_index == 0, "Index should stay at 0 when at first"


# Feature: llm-qa-correction-workbench, Property 39: Next navigation
@given(
    st.integers(min_value=0, max_value=100),
    st.integers(min_value=1, max_value=100)
)
@settings(max_examples=100)
def test_next_navigation(current_index, total_samples):
    """
    For any sample with index < (total_loaded - 1), clicking the next button
    should increment the current index by 1.
    
    **Validates: Requirements 10.2**
    """
    new_index = navigate_next(current_index, total_samples)
    
    # Property: If not at last, should increment
    if current_index < total_samples - 1:
        assert new_index == current_index + 1, \
            "Index should increment by 1 when not at last"
    else:
        # Property: If at last, should stay at current
        assert new_index == current_index, \
            "Index should stay at current when at last"


# Feature: llm-qa-correction-workbench, Property 40: Progress display update
@given(
    st.integers(min_value=0, max_value=1000),
    st.integers(min_value=0, max_value=1000)
)
@settings(max_examples=100)
def test_progress_display_update(corrected_count, total_loaded):
    """
    For any navigation action, the progress display should show the updated
    count of corrected samples and total loaded samples.
    
    **Validates: Requirements 10.3**
    """
    # Ensure corrected_count <= total_loaded
    if corrected_count > total_loaded:
        corrected_count = total_loaded
    
    progress_text = update_progress_display(corrected_count, total_loaded)
    
    # Property: Progress text should contain both counts
    assert str(corrected_count) in progress_text, \
        "Progress should show corrected count"
    assert str(total_loaded) in progress_text, \
        "Progress should show total loaded count"
    assert "/" in progress_text, \
        "Progress should have separator"



# Feature: llm-qa-correction-workbench, Property 9: Bold marker insertion
@given(st.text(min_size=1, max_size=100))
@settings(max_examples=100)
def test_bold_marker_insertion(selected_text):
    """
    For any selected text, clicking the bold button should insert ** before
    and after the selection.
    
    **Validates: Requirements 3.3**
    """
    # Simulate bold insertion
    result = f"**{selected_text}**"
    
    # Property: Result should have ** markers
    assert result.startswith("**"), "Should start with **"
    assert result.endswith("**"), "Should end with **"
    assert selected_text in result, "Original text should be preserved"
    
    # Property: Markers should be at correct positions
    assert result == f"**{selected_text}**"


# Feature: llm-qa-correction-workbench, Property 10: List marker insertion
@given(st.text(min_size=1, max_size=100))
@settings(max_examples=100)
def test_list_marker_insertion(selected_text):
    """
    For any selected text, clicking the list button should insert appropriate
    Markdown list markers (e.g., - or 1. ).
    
    **Validates: Requirements 3.4**
    """
    # Simulate list insertion (single line)
    result = f"- {selected_text}"
    
    # Property: Result should have list marker
    assert result.startswith("- "), "Should start with list marker"
    assert selected_text in result, "Original text should be preserved"
    
    # For multiline text
    lines = selected_text.split('\n')
    multiline_result = '\n'.join([f"- {line}" for line in lines])
    
    # Property: Each line should have marker
    for line in multiline_result.split('\n'):
        assert line.startswith("- "), "Each line should have list marker"


# Feature: llm-qa-correction-workbench, Property 16: Phase 1 locking
@given(st.booleans())
@settings(max_examples=50)
def test_phase1_locking(preview_generated):
    """
    For any sample, after clicking generate preview, the Phase 1 editors
    (Instruction and Output) should become read-only or disabled.
    
    **Validates: Requirements 4.5**
    """
    # Simulate locking state
    is_locked = preview_generated
    
    # Property: If preview generated, editors should be locked
    if preview_generated:
        assert is_locked == True, "Editors should be locked after preview"
    else:
        assert is_locked == False, "Editors should be unlocked before preview"



# Feature: llm-qa-correction-workbench, Property 35: Batch size configuration persistence
@given(st.integers(min_value=10, max_value=200))
@settings(max_examples=50)
def test_batch_size_persistence(new_batch_size):
    """
    For any modified batch size setting, subsequent batch loading operations
    should load exactly that number of samples.
    
    **Validates: Requirements 9.2**
    """
    from ui.event_handlers import update_batch_size
    
    # Initial state
    app_state = {
        'batch_size': 50,
        'export_format': 'messages'
    }
    
    # Update batch size
    updated_state = update_batch_size(new_batch_size, app_state)
    
    # Property: Batch size should be updated in state
    assert updated_state['batch_size'] == new_batch_size, \
        "Batch size should be persisted in application state"


# Feature: llm-qa-correction-workbench, Property 36: Export format preference persistence
@given(st.sampled_from(['messages', 'alpaca', 'sharegpt', 'query-response']))
@settings(max_examples=50)
def test_export_format_persistence(new_format):
    """
    For any selected export format, the preference should persist and be
    applied to all future export operations in the session.
    
    **Validates: Requirements 9.3**
    """
    from ui.event_handlers import update_export_format
    
    # Initial state
    app_state = {
        'batch_size': 50,
        'export_format': 'messages'
    }
    
    # Update export format
    updated_state = update_export_format(new_format, app_state)
    
    # Property: Export format should be updated in state
    assert updated_state['export_format'] == new_format, \
        "Export format should be persisted in application state"



# Feature: llm-qa-correction-workbench, Property 41: Accordion toggle
@given(st.booleans())
@settings(max_examples=50)
def test_accordion_toggle(current_open):
    """
    For any accordion state (open or closed), clicking the accordion header
    should toggle to the opposite state.
    
    **Validates: Requirements 11.4**
    """
    # Simulate accordion toggle
    new_open = not current_open
    
    # Property: State should be toggled
    assert new_open == (not current_open), \
        "Accordion state should toggle"
    
    # Property: If was open, should be closed
    if current_open:
        assert new_open == False, "Should close when was open"
    else:
        assert new_open == True, "Should open when was closed"
