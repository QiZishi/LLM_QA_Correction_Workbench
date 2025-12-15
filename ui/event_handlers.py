"""
Event handlers for UI components.

Handles user interactions and state updates.
"""

from typing import Dict, Any, Tuple, List, Optional
import os
import gradio as gr
from models import Sample
from utils.validation import (
    validate_tag_closure,
    validate_content_not_empty,
    validate_export_preconditions,
    auto_fix_malformed_tags
)


def toggle_left_column(current_visible: bool) -> Tuple[bool, str]:
    """
    Toggle visibility of left navigation column.
    
    Args:
        current_visible: Current visibility state
    
    Returns:
        Tuple of (new visibility state, button text)
    """
    new_visible = not current_visible
    button_text = "▶ 展开导航" if not new_visible else "◀ 收起导航"
    
    return new_visible, button_text


def navigate_previous(current_index: int, total_samples: int) -> int:
    """
    Navigate to previous sample.
    
    Args:
        current_index: Current sample index
        total_samples: Total number of loaded samples
    
    Returns:
        New index (stays at 0 if already at first)
    """
    if current_index > 0:
        return current_index - 1
    return current_index


def navigate_next(current_index: int, total_samples: int) -> int:
    """
    Navigate to next sample.
    
    Args:
        current_index: Current sample index
        total_samples: Total number of loaded samples
    
    Returns:
        New index (stays at last if already at end)
    """
    if current_index < total_samples - 1:
        return current_index + 1
    return current_index


def update_progress_display(corrected_count: int, total_loaded: int) -> str:
    """
    Generate progress display markdown.
    
    Args:
        corrected_count: Number of corrected samples
        total_loaded: Total number of loaded samples
    
    Returns:
        Markdown string for progress display
    """
    return f"**进度**: {corrected_count} / {total_loaded}"


def generate_sample_list_html(samples: list, current_index: int) -> str:
    """
    Generate HTML for sample list with status markers.
    
    Args:
        samples: List of Sample objects
        current_index: Currently selected sample index
    
    Returns:
        HTML string for sample list
    """
    if not samples:
        return "<div>暂无数据</div>"
    
    html_parts = ["<div style='max-height: 400px; overflow-y: auto;'>"]
    
    for i, sample in enumerate(samples):
        # Status marker
        if sample.status == "corrected":
            marker = "✅"
            color = "#4CAF50"
        elif sample.status == "discarded":
            marker = "❌"
            color = "#F44336"
        else:
            marker = "⭕"
            color = "#9E9E9E"
        
        # Highlight current sample
        bg_color = "#E3F2FD" if i == current_index else "transparent"
        
        html_parts.append(f"""
        <div style='padding: 8px; margin: 4px 0; background: {bg_color}; 
                    border-left: 3px solid {color}; cursor: pointer;'
             onclick='alert("Sample {i} clicked")'>
            <span style='color: {color};'>{marker}</span>
            <strong>#{sample.id}</strong>: {sample.instruction[:30]}...
        </div>
        """)
    
    html_parts.append("</div>")
    return "".join(html_parts)



def update_batch_size(new_batch_size: int, app_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update batch size setting in application state.
    
    Args:
        new_batch_size: New batch size value
        app_state: Current application state
    
    Returns:
        Updated application state
    """
    app_state['batch_size'] = new_batch_size
    return app_state


def update_export_format(new_format: str, app_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update export format setting in application state.
    
    Args:
        new_format: New export format
        app_state: Current application state
    
    Returns:
        Updated application state
    """
    app_state['export_format'] = new_format
    return app_state


def handle_csv_upload(file_path: str, batch_size: int = 50) -> Tuple[Dict[str, Any], str]:
    """
    Handle CSV file upload with comprehensive error handling.
    
    Args:
        file_path: Path to uploaded CSV file
        batch_size: Number of samples to load per batch
    
    Returns:
        Tuple of (app_state dict, status message)
    """
    from services import DataManager, ExportManager
    
    if not file_path:
        return {
            "current_index": 0,
            "samples": [],
            "data_manager": None,
            "export_manager": None,
            "phase": 1,
            "batch_size": batch_size,
            "export_format": "messages"
        }, "⚠️ 请先上传CSV文件"
    
    try:
        # Initialize DataManager (this validates the CSV)
        data_manager = DataManager(file_path, batch_size)
        
        # Load first batch
        samples = data_manager.load_next_batch()
        
        if not samples:
            return {
                "current_index": 0,
                "samples": [],
                "data_manager": None,
                "export_manager": None,
                "phase": 1,
                "batch_size": batch_size,
                "export_format": "messages"
            }, "⚠️ CSV文件为空，没有数据可加载"
        
        # Initialize ExportManager
        export_manager = ExportManager(format="messages")
        
        # Create app state
        app_state = {
            "current_index": 0,
            "samples": samples,
            "data_manager": data_manager,
            "export_manager": export_manager,
            "phase": 1,
            "batch_size": batch_size,
            "export_format": "messages"
        }
        
        success_msg = f"✅ 成功加载 {len(samples)} 条数据（共 {data_manager.total_rows} 条）"
        return app_state, success_msg
        
    except FileNotFoundError as e:
        error_msg = f"❌ 文件未找到: {str(e)}"
        return {
            "current_index": 0,
            "samples": [],
            "data_manager": None,
            "export_manager": None,
            "phase": 1,
            "batch_size": batch_size,
            "export_format": "messages"
        }, error_msg
        
    except ValueError as e:
        # Handle missing columns or invalid format
        error_msg = f"❌ CSV格式错误: {str(e)}"
        return {
            "current_index": 0,
            "samples": [],
            "data_manager": None,
            "export_manager": None,
            "phase": 1,
            "batch_size": batch_size,
            "export_format": "messages"
        }, error_msg
        
    except UnicodeDecodeError as e:
        error_msg = f"❌ 编码错误: 文件编码不是UTF-8或GBK。请检查文件编码。"
        return {
            "current_index": 0,
            "samples": [],
            "data_manager": None,
            "export_manager": None,
            "phase": 1,
            "batch_size": batch_size,
            "export_format": "messages"
        }, error_msg
        
    except Exception as e:
        # Catch-all for unexpected errors
        error_msg = f"❌ 加载失败: {str(e)}"
        return {
            "current_index": 0,
            "samples": [],
            "data_manager": None,
            "export_manager": None,
            "phase": 1,
            "batch_size": batch_size,
            "export_format": "messages"
        }, error_msg


def load_sample_to_ui(app_state: Dict[str, Any]) -> Tuple[str, str, str, str, str]:
    """
    Load current sample data to UI components.
    
    Args:
        app_state: Current application state
    
    Returns:
        Tuple of (instruction, output, reference_html, progress_md, sample_list_html)
    """
    from services import RenderEngine
    
    if not app_state.get('samples') or not app_state.get('data_manager'):
        return "", "", "<div>暂无数据</div>", "**进度**: 0 / 0", "<div>暂无数据</div>"
    
    current_index = app_state['current_index']
    samples = app_state['samples']
    data_manager = app_state['data_manager']
    
    if current_index >= len(samples):
        return "", "", "<div>索引超出范围</div>", "**进度**: 0 / 0", "<div>暂无数据</div>"
    
    current_sample = samples[current_index]
    
    # Render reference content with Markdown and LaTeX
    render_engine = RenderEngine()
    reference_html = render_engine.render_markdown_latex(current_sample.chunk)
    
    # Get progress
    corrected_count, total_loaded = data_manager.get_progress()
    progress_md = f"**进度**: {corrected_count} / {total_loaded}"
    
    # Generate sample list
    sample_list_html = generate_sample_list_html(samples, current_index)
    
    return (
        current_sample.instruction,
        current_sample.output,
        reference_html,
        progress_md,
        sample_list_html
    )


def handle_generate_preview(instruction: str, output: str, app_state: Dict[str, Any]) -> Tuple[Dict[str, Any], str, str, bool, bool]:
    """
    Generate diff preview and transition to Phase 2.
    
    Args:
        instruction: Edited instruction text
        output: Edited output text
        app_state: Current application state
    
    Returns:
        Tuple of (updated_app_state, original_display, diff_html, phase1_visible, phase2_visible)
    """
    from services import DiffEngine, RenderEngine
    
    if not app_state.get('samples'):
        gr.Warning("无数据可处理")
        return app_state, "", "<div>无数据</div>", True, False
    
    try:
        current_index = app_state['current_index']
        current_sample = app_state['samples'][current_index]
        
        # Validate input
        is_valid, error_msg = validate_content_not_empty(instruction, "问题")
        if not is_valid:
            gr.Warning(error_msg)
            return app_state, "", f"<div>{error_msg}</div>", True, False
        
        is_valid, error_msg = validate_content_not_empty(output, "回答")
        if not is_valid:
            gr.Warning(error_msg)
            return app_state, "", f"<div>{error_msg}</div>", True, False
        
        # Store edited content
        current_sample.edited_instruction = instruction
        current_sample.edited_output = output
        
        # Compute diff with timeout protection
        diff_engine = DiffEngine()
        try:
            diff_result = diff_engine.compute_diff(current_sample.output, output)
        except TimeoutError:
            gr.Error("差异计算超时，文本可能过长")
            return app_state, "", "<div>差异计算超时</div>", True, False
        except Exception as e:
            gr.Error(f"差异计算失败: {str(e)}")
            return app_state, "", f"<div>差异计算失败: {str(e)}</div>", True, False
        
        # Store diff result
        current_sample.diff_result = diff_result
        
        # Render diff
        render_engine = RenderEngine()
        try:
            diff_html = render_engine.render_diff_tags(diff_result)
            original_display = render_engine.render_markdown_latex(current_sample.output)
        except Exception as e:
            gr.Error(f"渲染失败: {str(e)}")
            return app_state, "", f"<div>渲染失败: {str(e)}</div>", True, False
        
        # Update phase
        app_state['phase'] = 2
        
        return app_state, original_display, diff_html, False, True
        
    except Exception as e:
        gr.Error(f"生成预览失败: {str(e)}")
        return app_state, "", f"<div>生成预览失败: {str(e)}</div>", True, False


def handle_submit(app_state: Dict[str, Any]) -> Tuple[Dict[str, Any], str, str, str, str, str, bool, bool]:
    """
    Submit current sample and navigate to next.
    
    Args:
        app_state: Current application state
    
    Returns:
        Tuple of (updated_app_state, instruction, output, reference_html, progress_md, sample_list_html, phase1_visible, phase2_visible)
    """
    if not app_state.get('samples') or not app_state.get('export_manager'):
        gr.Warning("无数据可提交")
        return app_state, "", "", "<div>无数据</div>", "**进度**: 0 / 0", "<div>无数据</div>", True, False
    
    try:
        current_index = app_state['current_index']
        current_sample = app_state['samples'][current_index]
        data_manager = app_state['data_manager']
        export_manager = app_state['export_manager']
        
        # Validate that sample has been edited
        if not hasattr(current_sample, 'edited_instruction') or not current_sample.edited_instruction:
            gr.Warning("请先编辑并生成预览")
            return app_state, "", "", "<div>请先编辑并生成预览</div>", "**进度**: 0 / 0", "<div>无数据</div>", True, False
        
        # Update status to corrected
        try:
            data_manager.update_sample_status(current_sample.id, 'corrected')
        except Exception as e:
            gr.Error(f"更新状态失败: {str(e)}")
            return app_state, "", "", "<div>更新状态失败</div>", "**进度**: 0 / 0", "<div>无数据</div>", True, False
        
        # Add to export queue
        try:
            export_manager.add_sample(current_sample)
        except Exception as e:
            gr.Error(f"添加到导出队列失败: {str(e)}")
            # Revert status change
            data_manager.update_sample_status(current_sample.id, 'unprocessed')
            return app_state, "", "", "<div>添加到导出队列失败</div>", "**进度**: 0 / 0", "<div>无数据</div>", True, False
        
        # Check if should load next batch
        try:
            if data_manager.should_load_next_batch():
                new_samples = data_manager.load_next_batch()
                app_state['samples'].extend(new_samples)
        except Exception as e:
            gr.Warning(f"加载下一批数据失败: {str(e)}")
            # Continue anyway
        
        # Navigate to next sample
        if current_index < len(app_state['samples']) - 1:
            app_state['current_index'] += 1
        
        # Reset to Phase 1
        app_state['phase'] = 1
        
        # Load next sample to UI
        instruction, output, reference_html, progress_md, sample_list_html = load_sample_to_ui(app_state)
        
        gr.Info("样本已提交")
        return app_state, instruction, output, reference_html, progress_md, sample_list_html, True, False
        
    except Exception as e:
        gr.Error(f"提交失败: {str(e)}")
        return app_state, "", "", "<div>提交失败</div>", "**进度**: 0 / 0", "<div>无数据</div>", True, False


def handle_discard(app_state: Dict[str, Any]) -> Tuple[Dict[str, Any], str, str, str, str, str, bool, bool]:
    """
    Discard current sample and navigate to next.
    
    Args:
        app_state: Current application state
    
    Returns:
        Tuple of (updated_app_state, instruction, output, reference_html, progress_md, sample_list_html, phase1_visible, phase2_visible)
    """
    if not app_state.get('samples'):
        gr.Warning("无数据可丢弃")
        return app_state, "", "", "<div>无数据</div>", "**进度**: 0 / 0", "<div>无数据</div>", True, False
    
    try:
        current_index = app_state['current_index']
        current_sample = app_state['samples'][current_index]
        data_manager = app_state['data_manager']
        
        # Update status to discarded
        try:
            data_manager.update_sample_status(current_sample.id, 'discarded')
        except Exception as e:
            gr.Error(f"更新状态失败: {str(e)}")
            return app_state, "", "", "<div>更新状态失败</div>", "**进度**: 0 / 0", "<div>无数据</div>", True, False
        
        # Check if should load next batch
        try:
            if data_manager.should_load_next_batch():
                new_samples = data_manager.load_next_batch()
                app_state['samples'].extend(new_samples)
        except Exception as e:
            gr.Warning(f"加载下一批数据失败: {str(e)}")
            # Continue anyway
        
        # Navigate to next sample
        if current_index < len(app_state['samples']) - 1:
            app_state['current_index'] += 1
        
        # Reset to Phase 1
        app_state['phase'] = 1
        
        # Load next sample to UI
        instruction, output, reference_html, progress_md, sample_list_html = load_sample_to_ui(app_state)
        
        gr.Info("样本已丢弃")
        return app_state, instruction, output, reference_html, progress_md, sample_list_html, True, False
        
    except Exception as e:
        gr.Error(f"丢弃失败: {str(e)}")
        return app_state, "", "", "<div>丢弃失败</div>", "**进度**: 0 / 0", "<div>无数据</div>", True, False


def handle_refresh_diff(diff_content: str, app_state: Dict[str, Any]) -> str:
    """
    Refresh diff rendering after manual edits.
    
    Args:
        diff_content: Edited diff content (HTML)
        app_state: Current application state
    
    Returns:
        Re-rendered diff HTML
    """
    from services import RenderEngine
    
    if not app_state.get('samples'):
        gr.Warning("无数据")
        return "<div>无数据</div>"
    
    try:
        current_index = app_state['current_index']
        current_sample = app_state['samples'][current_index]
        
        # Validate tag closure
        is_valid, error_msg = validate_tag_closure(diff_content)
        if not is_valid:
            gr.Warning(f"标签格式错误: {error_msg}. 尝试自动修复...")
            # Auto-fix malformed tags
            diff_content = auto_fix_malformed_tags(diff_content)
        
        # Update stored diff result
        current_sample.diff_result = diff_content
        
        # Re-render
        render_engine = RenderEngine()
        rendered = render_engine.render_diff_tags(diff_content)
        
        gr.Info("差异结果已刷新")
        return rendered
        
    except Exception as e:
        gr.Error(f"刷新失败: {str(e)}")
        return f"<div>刷新失败: {str(e)}</div>"


def handle_export(app_state: Dict[str, Any]) -> Tuple[str, str]:
    """
    Export corrected samples to JSON file.
    
    Args:
        app_state: Current application state
    
    Returns:
        Tuple of (file_path, status_message)
    """
    if not app_state.get('export_manager'):
        return None, "❌ 导出管理器未初始化"
    
    export_manager = app_state['export_manager']
    data_manager = app_state.get('data_manager')
    
    # Get original filename from data manager
    original_filename = "export"
    if data_manager and hasattr(data_manager, 'csv_path'):
        original_filename = os.path.basename(data_manager.csv_path)
    
    # Validate export preconditions
    corrected_count = export_manager.get_sample_count()
    is_valid, error_msg = validate_export_preconditions(corrected_count)
    if not is_valid:
        gr.Warning(error_msg)
        return None, f"⚠️ {error_msg}"
    
    try:
        file_path = export_manager.export_to_json(original_filename)
        
        if not file_path:
            return None, "⚠️ 没有已校正的样本可导出"
        
        gr.Info(f"成功导出 {corrected_count} 条数据")
        return file_path, f"✅ 成功导出到: {file_path}"
    except ValueError as e:
        # Handle "no corrected samples" error
        gr.Warning(str(e))
        return None, f"⚠️ {str(e)}"
    except Exception as e:
        gr.Error(f"导出失败: {str(e)}")
        return None, f"❌ 导出失败: {str(e)}"


def handle_navigation(direction: str, app_state: Dict[str, Any]) -> Tuple[Dict[str, Any], str, str, str, str, str]:
    """
    Handle previous/next navigation.
    
    Args:
        direction: "prev" or "next"
        app_state: Current application state
    
    Returns:
        Tuple of (updated_app_state, instruction, output, reference_html, progress_md, sample_list_html)
    """
    if not app_state.get('samples'):
        gr.Warning("无数据可导航")
        return app_state, "", "", "<div>无数据</div>", "**进度**: 0 / 0", "<div>无数据</div>"
    
    try:
        current_index = app_state['current_index']
        total_samples = len(app_state['samples'])
        
        # Validate direction
        if direction not in ["prev", "next"]:
            gr.Error(f"无效的导航方向: {direction}")
            return app_state, "", "", "<div>无效的导航方向</div>", "**进度**: 0 / 0", "<div>无数据</div>"
        
        # Navigate
        if direction == "prev":
            if current_index > 0:
                app_state['current_index'] -= 1
            else:
                gr.Info("已经是第一条数据")
        elif direction == "next":
            if current_index < total_samples - 1:
                app_state['current_index'] += 1
            else:
                gr.Info("已经是最后一条数据")
        
        # Check if should load next batch
        if direction == "next" and app_state.get('data_manager'):
            try:
                data_manager = app_state['data_manager']
                if data_manager.should_load_next_batch():
                    new_samples = data_manager.load_next_batch()
                    app_state['samples'].extend(new_samples)
                    if new_samples:
                        gr.Info(f"已自动加载下一批 {len(new_samples)} 条数据")
            except Exception as e:
                gr.Warning(f"加载下一批数据失败: {str(e)}")
                # Continue anyway
        
        # Reset to Phase 1
        app_state['phase'] = 1
        
        # Load sample to UI
        instruction, output, reference_html, progress_md, sample_list_html = load_sample_to_ui(app_state)
        
        return app_state, instruction, output, reference_html, progress_md, sample_list_html
        
    except Exception as e:
        gr.Error(f"导航失败: {str(e)}")
        return app_state, "", "", "<div>导航失败</div>", "**进度**: 0 / 0", "<div>无数据</div>"


def insert_bold_marker(text: str, cursor_pos: int) -> str:
    """
    Insert bold markers around selected text or at cursor.
    
    Args:
        text: Current text content
        cursor_pos: Cursor position
    
    Returns:
        Updated text with bold markers
    """
    # Simple implementation: insert ** at cursor
    return text[:cursor_pos] + "****" + text[cursor_pos:]


def insert_list_marker(text: str, cursor_pos: int) -> str:
    """
    Insert list markers for selected text or at cursor.
    
    Args:
        text: Current text content
        cursor_pos: Cursor position
    
    Returns:
        Updated text with list markers
    """
    # Simple implementation: insert - at start of line
    lines = text.split('\n')
    # Find which line cursor is on
    char_count = 0
    for i, line in enumerate(lines):
        if char_count + len(line) >= cursor_pos:
            if not line.strip().startswith('-'):
                lines[i] = '- ' + line
            break
        char_count += len(line) + 1
    
    return '\n'.join(lines)
