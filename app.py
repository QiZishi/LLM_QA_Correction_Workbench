"""
LLM-QA Correction Workbench
大模型问答数据校正工作台

Main entry point for the Gradio application.
"""

import warnings
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', message='.*too many values to unpack.*')

import gradio as gr
from ui.layout import create_three_column_layout, get_global_css
from ui.event_handlers import (
    handle_csv_upload,
    load_sample_to_ui,
    handle_generate_preview,
    handle_submit,
    handle_discard,
    handle_refresh_diff,
    handle_export,
    handle_navigation,
    update_export_format,
    handle_sample_click
)
from services import RenderEngine


def main():
    """Main application entry point."""
    # Initialize render engine
    render_engine = RenderEngine()
    
    with gr.Blocks(
        title="大模型数据校正",
        theme=gr.themes.Soft(),
        head=render_engine.get_katex_header(),
        css="""
        /* 全局缩放85% */
        .gradio-container { zoom: 0.85; transform-origin: top center; }
        /* 全局字体设置 - 英文使用Times New Roman */
        * { font-family: "Times New Roman", "SimSun", "宋体", serif !important; }
        .gradio-container { font-size: 18px !important; font-family: "Times New Roman", "SimSun", "宋体", serif !important; }
        h1 { font-size: 32px !important; font-family: "Times New Roman", "SimSun", "宋体", serif !important; }
        h2 { font-size: 26px !important; font-family: "Times New Roman", "SimSun", "宋体", serif !important; }
        h3 { font-size: 22px !important; font-family: "Times New Roman", "SimSun", "宋体", serif !important; }
        textarea, input, .prose { font-size: 18px !important; line-height: 1.6 !important; font-family: "Times New Roman", "SimSun", "宋体", serif !important; }
        button { font-size: 16px !important; font-family: "Times New Roman", "SimSun", "宋体", serif !important; }
        .large-textbox textarea { font-size: 18px !important; min-height: 150px; font-family: "Times New Roman", "SimSun", "宋体", serif !important; }
        """
    ) as app:
        
        # Application State
        app_state = gr.State({
            "current_index": 0,
            "samples": [],
            "data_manager": None,
            "export_manager": None,
            "phase": 1,
            "batch_size": 50,
            "export_format": "messages",
            "custom_filename": ""
        })
        
        # Create three-column layout (includes header, instructions, settings, etc.)
        components = create_three_column_layout()
        
        # Inject WYSIWYG controls
        gr.HTML(render_engine.inject_wysiwyg_controls())
        
        # ========== Event Handlers ==========
        
        # CSV Upload Handler
        def on_csv_upload(file_path, batch_size, state):
            from ui.event_handlers import get_stats_html
            new_state, msg = handle_csv_upload(file_path, batch_size)
            # Preserve export format from previous state
            new_state['export_format'] = state.get('export_format', 'messages')
            new_state['custom_filename'] = state.get('custom_filename', '')
            
            if new_state.get('samples'):
                instruction, output, ref_html, status_html, progress, sample_list = load_sample_to_ui(new_state)
                stats_html = get_stats_html(new_state)
                return (
                    new_state, status_html, instruction, output, ref_html, sample_list, stats_html,
                    gr.update(visible=True), gr.update(visible=False)
                )
            # 如果加载失败，使用错误消息HTML
            return (
                new_state, msg, "", "", 
                '<div class="reference-content" style="min-height: 500px;">暂无数据</div>',
                '<div class="sample-list-container">暂无数据</div>',
                '<div style="padding: 8px; margin: 5px 0; background: #f5f5f5; border: 1px solid #1976d2; border-radius: 5px; font-size: 14px; text-align: center;">📊 统计: 待处理 <span style="color: #9E9E9E;">0</span> | 已校正 <span style="color: #4CAF50;">0</span> | 已丢弃 <span style="color: #F44336;">0</span></div>',
                gr.update(visible=True), gr.update(visible=False)
            )
        
        components['csv_upload'].upload(
            fn=on_csv_upload,
            inputs=[components['csv_upload'], components['batch_size_input'], app_state],
            outputs=[
                app_state,
                components['upload_status'],
                components['instruction_editor'],
                components['output_editor'],
                components['reference_display'],
                components['sample_list'],
                components['stats_display'],
                components['phase1_group'],
                components['phase2_group']
            ]
        )
        
        # Navigation Handlers
        def on_navigation(direction, state):
            # handle_navigation now returns 18 values including phase2 components
            return handle_navigation(direction, state)
        
        components['prev_btn'].click(
            fn=lambda state: on_navigation("prev", state),
            inputs=[app_state],
            outputs=[
                app_state,
                components['upload_status'],
                components['instruction_editor'],
                components['output_editor'],
                components['reference_display'],
                components['sample_list'],
                components['stats_display'],
                components['phase1_group'],
                components['phase2_group'],
                components['discard_phase1_btn'],
                components['generate_preview_btn'],
                components['discard_btn'],
                components['submit_btn'],
                components['refresh_btn'],
                components['corrected_instruction_editor'],
                components['corrected_output_editor'],
                components['corrected_instruction_display'],
                components['corrected_output_display']
            ]
        )
        
        components['next_btn'].click(
            fn=lambda state: on_navigation("next", state),
            inputs=[app_state],
            outputs=[
                app_state,
                components['upload_status'],
                components['instruction_editor'],
                components['output_editor'],
                components['reference_display'],
                components['sample_list'],
                components['stats_display'],
                components['phase1_group'],
                components['phase2_group'],
                components['discard_phase1_btn'],
                components['generate_preview_btn'],
                components['discard_btn'],
                components['submit_btn'],
                components['refresh_btn'],
                components['corrected_instruction_editor'],
                components['corrected_output_editor'],
                components['corrected_instruction_display'],
                components['corrected_output_display']
            ]
        )
        
        # 样本点击跳转事件
        components['sample_click_index'].change(
            fn=handle_sample_click,
            inputs=[components['sample_click_index'], app_state],
            outputs=[
                app_state,
                components['upload_status'],
                components['instruction_editor'],
                components['output_editor'],
                components['reference_display'],
                components['sample_list'],
                components['stats_display'],
                components['phase1_group'],
                components['phase2_group'],
                components['discard_phase1_btn'],
                components['generate_preview_btn'],
                components['discard_btn'],
                components['submit_btn'],
                components['refresh_btn'],
                components['corrected_instruction_editor'],
                components['corrected_output_editor'],
                components['corrected_instruction_display'],
                components['corrected_output_display']
            ]
        )
        
        # Generate Preview Handler
        def on_generate_preview(instruction, output, state):
            from ui.event_handlers import handle_generate_preview
            
            # handle_generate_preview returns: (app_state, instruction_diff_html, instruction_text, output_diff_html, output_text, phase1_visible, phase2_visible)
            state, instruction_diff_html, instruction_text, output_diff_html, output_text, phase1_vis, phase2_vis = handle_generate_preview(instruction, output, state)
            
            return (
                state,
                instruction_text,  # 编辑器显示纯净内容
                output_text,      # 编辑器显示纯净内容
                instruction_diff_html,  # 差异显示
                output_diff_html,       # 差异显示
                gr.update(visible=phase1_vis),
                gr.update(visible=phase2_vis)
            )
        
        components['generate_preview_btn'].click(
            fn=on_generate_preview,
            inputs=[
                components['instruction_editor'],
                components['output_editor'],
                app_state
            ],
            outputs=[
                app_state,
                components['corrected_instruction_editor'],
                components['corrected_output_editor'],
                components['corrected_instruction_display'],
                components['corrected_output_display'],
                components['phase1_group'],
                components['phase2_group']
            ]
        )
        
        # Submit Handler
        def on_submit(state):
            # 计算并存储带有<false>和<true>标记的差异结果
            if state.get('samples') and state.get('current_index') is not None:
                current_sample = state['samples'][state['current_index']]
                if hasattr(current_sample, 'edited_instruction') and hasattr(current_sample, 'edited_output'):
                    from services import DiffEngine
                    diff_engine = DiffEngine()
                    
                    # 计算差异并存储带标记的结果
                    instruction_diff = diff_engine.compute_diff(
                        current_sample.original_instruction, 
                        current_sample.edited_instruction
                    )
                    output_diff = diff_engine.compute_diff(
                        current_sample.original_output, 
                        current_sample.edited_output
                    )
                    
                    # 存储带有<false>和<true>标记的差异结果
                    current_sample.final_instruction = instruction_diff
                    current_sample.final_output = output_diff
            
            state, status_html, instruction, output, reference, progress, sample_list, phase1_vis, phase2_vis = handle_submit(state)
            return (
                state, status_html, instruction, output, reference, sample_list,
                gr.update(visible=phase1_vis), gr.update(visible=phase2_vis)
            )
        
        components['submit_btn'].click(
            fn=on_submit,
            inputs=[app_state],
            outputs=[
                app_state,
                components['upload_status'],
                components['instruction_editor'],
                components['output_editor'],
                components['reference_display'],
                components['sample_list'],
                components['phase1_group'],
                components['phase2_group']
            ]
        )
        
        # Discard Handler
        def on_discard(state):
            state, status_html, instruction, output, reference, progress, sample_list, phase1_vis, phase2_vis = handle_discard(state)
            return (
                state, status_html, instruction, output, reference, sample_list,
                gr.update(visible=phase1_vis), gr.update(visible=phase2_vis)
            )
        
        components['discard_btn'].click(
            fn=on_discard,
            inputs=[app_state],
            outputs=[
                app_state,
                components['upload_status'],
                components['instruction_editor'],
                components['output_editor'],
                components['reference_display'],
                components['sample_list'],
                components['phase1_group'],
                components['phase2_group']
            ]
        )
        
        # Discard Phase 1 Handler
        def on_discard_phase1(state):
            from ui.event_handlers import handle_discard_phase1, get_stats_html
            state, status_html, instruction, output, reference, progress, sample_list, btn_update, preview_visible = handle_discard_phase1(state)
            stats_html = get_stats_html(state)
            return (
                state, status_html, instruction, output, reference, sample_list, stats_html,
                gr.update(visible=True), gr.update(visible=False), btn_update, preview_visible
            )
        
        components['discard_phase1_btn'].click(
            fn=on_discard_phase1,
            inputs=[app_state],
            outputs=[
                app_state,
                components['upload_status'],
                components['instruction_editor'],
                components['output_editor'],
                components['reference_display'],
                components['sample_list'],
                components['stats_display'],
                components['phase1_group'],
                components['phase2_group'],
                components['discard_phase1_btn'],
                components['generate_preview_btn']
            ]
        )
        
        # Refresh Diff Handler
        def on_refresh(corrected_instruction, corrected_output, state):
            from services import DiffEngine, RenderEngine
            
            if not state.get('samples'):
                no_data = '<div>无数据</div>'
                return corrected_instruction, corrected_output, no_data, no_data
            
            current_sample = state['samples'][state['current_index']]
            
            # 重新计算差异
            diff_engine = DiffEngine()
            render_engine = RenderEngine()
            
            try:
                # 先清理编辑器内容中可能存在的标记（防止标记嵌套）
                from ui.event_handlers import extract_final_content_from_tags
                clean_instruction = extract_final_content_from_tags(corrected_instruction)
                clean_output = extract_final_content_from_tags(corrected_output)
                
                # 使用清理后的内容计算差异
                instruction_diff = diff_engine.compute_diff(
                    current_sample.instruction, 
                    clean_instruction
                )
                output_diff = diff_engine.compute_diff(
                    current_sample.output, 
                    clean_output
                )
                
                # 渲染差异
                instruction_html = render_engine.render_diff_tags(instruction_diff)
                output_html = render_engine.render_diff_tags(output_diff)
                
                # 更新存储的编辑内容
                # edited_* 存储带标记的差异结果（用于导出）
                current_sample.edited_instruction = instruction_diff
                current_sample.edited_output = output_diff
                # final_* 存储纯净内容（用于编辑器显示）
                current_sample.final_instruction = clean_instruction
                current_sample.final_output = clean_output
                
                # 返回清理后的内容给编辑器
                return clean_instruction, clean_output, instruction_html, output_html
                    
            except Exception as e:
                error_msg = f'<div style="color: red;">刷新失败: {str(e)}</div>'
                return corrected_instruction, corrected_output, error_msg, error_msg
        
        components['refresh_btn'].click(
            fn=on_refresh,
            inputs=[
                components['corrected_instruction_editor'],
                components['corrected_output_editor'],
                app_state
            ],
            outputs=[
                components['corrected_instruction_editor'],
                components['corrected_output_editor'],
                components['corrected_instruction_display'],
                components['corrected_output_display']
            ]
        )
        
        # Export Handler
        def on_export(export_format, custom_filename, state):
            # 更新导出格式
            if state.get('export_manager'):
                state['export_manager'].format = export_format
            state['export_format'] = export_format
            state['custom_filename'] = custom_filename
            
            file_path, status_msg = handle_export(state)
            
            # 包装状态消息为HTML格式
            status_html = f'<div class="load-status">{status_msg}</div>'
            
            # 如果导出成功，显示下载框
            if file_path:
                return file_path, status_html, gr.update(visible=True)
            else:
                return None, status_html, gr.update(visible=False)
        
        components['export_btn'].click(
            fn=on_export,
            inputs=[
                components['export_format_dropdown'],
                components['export_filename_input'],
                app_state
            ],
            outputs=[
                components['export_file'], 
                components['upload_status'],
                components['export_file']  # 控制显示/隐藏
            ]
        )
        
        # Export Format Change Handler
        def on_format_change(new_format, state):
            state['export_format'] = new_format
            if state.get('export_manager'):
                state['export_manager'].format = new_format
            return state
        
        components['export_format_dropdown'].change(
            fn=on_format_change,
            inputs=[components['export_format_dropdown'], app_state],
            outputs=[app_state]
        )
        
        # Batch Size Change Handler
        def on_batch_size_change(new_size, state):
            state['batch_size'] = int(new_size)
            return state
        
        components['batch_size_input'].change(
            fn=on_batch_size_change,
            inputs=[components['batch_size_input'], app_state],
            outputs=[app_state]
        )
        
        # Backtrack Toggle Handler
        def on_backtrack_toggle(state):
            from ui.event_handlers import handle_backtrack_toggle
            visible, msg = handle_backtrack_toggle(state)
            return gr.update(visible=visible)
        
        components['backtrack_btn'].click(
            fn=on_backtrack_toggle,
            inputs=[app_state],
            outputs=[components['backtrack_upload']]
        )
        
        # Backtrack Upload Handler
        def on_backtrack_upload(file_path, state):
            from ui.event_handlers import handle_backtrack_upload
            result = handle_backtrack_upload(file_path, state)
            # handle_backtrack_upload returns 14 values
            state, status_html, instruction, output, ref_html, sample_list, stats_html, phase1_vis, phase2_vis, discard_btn, preview_btn, discard_btn2, submit_btn, refresh_btn = result
            return (
                state, status_html, instruction, output, ref_html, sample_list, stats_html,
                gr.update(visible=phase1_vis), gr.update(visible=phase2_vis),
                discard_btn, preview_btn, discard_btn2, submit_btn, refresh_btn
            )
        
        components['backtrack_upload'].upload(
            fn=on_backtrack_upload,
            inputs=[components['backtrack_upload'], app_state],
            outputs=[
                app_state,
                components['upload_status'],
                components['instruction_editor'],
                components['output_editor'],
                components['reference_display'],
                components['sample_list'],
                components['stats_display'],
                components['phase1_group'],
                components['phase2_group'],
                components['discard_phase1_btn'],
                components['generate_preview_btn'],
                components['discard_btn'],
                components['submit_btn'],
                components['refresh_btn']
            ]
        )
        
        # Collapse/Expand Navigation Handlers
        def on_collapse():
            return (
                gr.update(visible=False),  # left_col (整个左侧导航列)
                gr.update(visible=True)    # standalone_expand_btn (独立展开按钮)
            )
        
        def on_expand():
            return (
                gr.update(visible=True),   # left_col (整个左侧导航列)
                gr.update(visible=False)   # standalone_expand_btn (独立展开按钮)
            )
        
        components['collapse_btn'].click(
            fn=on_collapse,
            inputs=[],
            outputs=[
                components['left_col'],
                components['standalone_expand_btn']
            ],
            show_progress=False
        )
        
        # 两个展开按钮都绑定同一个函数
        components['expand_btn'].click(
            fn=on_expand,
            inputs=[],
            outputs=[
                components['left_col'],
                components['standalone_expand_btn']
            ]
        )
        
        components['standalone_expand_btn'].click(
            fn=on_expand,
            inputs=[],
            outputs=[
                components['left_col'],
                components['standalone_expand_btn']
            ]
        )
        
    return app


if __name__ == "__main__":
    app = main()
    # 禁用缓存，确保每次都加载最新资源
    app.launch(
        show_error=True,
        quiet=False,
        # 添加自定义响应头来控制缓存
        allowed_paths=[],
        # 不使用CDN缓存
        favicon_path=None
    )
