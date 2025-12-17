"""
LLM-QA Correction Workbench
大模型问答数据校正工作台

Main entry point for the Gradio application.
"""

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
    update_export_format
)
from services import RenderEngine


def main():
    """Main application entry point."""
    # Initialize render engine for KaTeX support
    render_engine = RenderEngine()
    
    with gr.Blocks(
        title="大模型问答数据校正工作台",
        theme=gr.themes.Soft(),
        head=render_engine.get_katex_header(),
        css="""
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
            new_state, msg = handle_csv_upload(file_path, batch_size)
            # Preserve export format from previous state
            new_state['export_format'] = state.get('export_format', 'messages')
            new_state['custom_filename'] = state.get('custom_filename', '')
            
            # 包装状态消息为HTML格式
            status_html = f'<div class="load-status">{msg}</div>'
            
            if new_state.get('samples'):
                instruction, output, ref_html, progress, sample_list = load_sample_to_ui(new_state)
                return (
                    new_state, status_html, instruction, output, ref_html, sample_list,
                    gr.update(visible=True), gr.update(visible=False)
                )
            return (
                new_state, status_html, "", "", 
                '<div class="reference-content" style="min-height: 500px;">暂无数据</div>',
                '<div class="sample-list-container">暂无数据</div>',
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
                components['phase1_group'],
                components['phase2_group']
            ]
        )
        
        # Navigation Handlers
        def on_navigation(direction, state):
            state, instruction, output, ref_html, progress, sample_list = handle_navigation(direction, state)
            return (
                state, instruction, output, ref_html, sample_list,
                gr.update(visible=True), gr.update(visible=False)
            )
        
        components['prev_btn'].click(
            fn=lambda state: on_navigation("prev", state),
            inputs=[app_state],
            outputs=[
                app_state,
                components['instruction_editor'],
                components['output_editor'],
                components['reference_display'],
                components['sample_list'],
                components['phase1_group'],
                components['phase2_group']
            ]
        )
        
        components['next_btn'].click(
            fn=lambda state: on_navigation("next", state),
            inputs=[app_state],
            outputs=[
                app_state,
                components['instruction_editor'],
                components['output_editor'],
                components['reference_display'],
                components['sample_list'],
                components['phase1_group'],
                components['phase2_group']
            ]
        )
        
        # Generate Preview Handler
        def on_generate_preview(instruction, output, state):
            from services import DiffEngine, RenderEngine
            
            if not state.get('samples'):
                gr.Warning("无数据可处理")
                no_data_html = '<div>无数据</div>'
                return (
                    state, 
                    instruction,
                    output,
                    no_data_html,
                    no_data_html,
                    gr.update(visible=True), 
                    gr.update(visible=False)
                )
            
            try:
                current_sample = state['samples'][state['current_index']]
                
                # 计算差异
                diff_engine = DiffEngine()
                render_engine = RenderEngine()
                
                # 计算问题差异
                instruction_diff = diff_engine.compute_diff(current_sample.instruction, instruction)
                instruction_diff_html = render_engine.render_diff_tags(instruction_diff)
                
                # 计算回答差异
                output_diff = diff_engine.compute_diff(current_sample.output, output)
                output_diff_html = render_engine.render_diff_tags(output_diff)
                
                # 存储编辑内容
                current_sample.edited_instruction = instruction
                current_sample.edited_output = output
                
                # 更新阶段
                state['phase'] = 2
                
                return (
                    state,
                    instruction,  # 在阶段2显示编辑后的内容
                    output,
                    instruction_diff_html,  # 问题差异HTML
                    output_diff_html,       # 回答差异HTML
                    gr.update(visible=False),
                    gr.update(visible=True)
                )
                
            except Exception as e:
                gr.Error(f"生成预览失败: {str(e)}")
                error_html = f'<div style="color: red;">生成预览失败: {str(e)}</div>'
                return (
                    state,
                    instruction,
                    output,
                    error_html,
                    error_html,
                    gr.update(visible=True),
                    gr.update(visible=False)
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
            
            state, instruction, output, reference, progress, sample_list, phase1_vis, phase2_vis = handle_submit(state)
            return (
                state, instruction, output, reference, progress, sample_list,
                gr.update(visible=phase1_vis), gr.update(visible=phase2_vis)
            )
        
        components['submit_btn'].click(
            fn=on_submit,
            inputs=[app_state],
            outputs=[
                app_state,
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
            state, instruction, output, reference, progress, sample_list, phase1_vis, phase2_vis = handle_discard(state)
            return (
                state, instruction, output, reference, progress, sample_list,
                gr.update(visible=phase1_vis), gr.update(visible=phase2_vis)
            )
        
        components['discard_btn'].click(
            fn=on_discard,
            inputs=[app_state],
            outputs=[
                app_state,
                components['instruction_editor'],
                components['output_editor'],
                components['reference_display'],
                components['sample_list'],
                components['phase1_group'],
                components['phase2_group']
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
                # 使用当前编辑框中的内容重新计算差异
                instruction_diff = diff_engine.compute_diff(
                    current_sample.instruction, 
                    corrected_instruction
                )
                output_diff = diff_engine.compute_diff(
                    current_sample.output, 
                    corrected_output
                )
                
                # 渲染差异
                instruction_html = render_engine.render_diff_tags(instruction_diff)
                output_html = render_engine.render_diff_tags(output_diff)
                
                # 更新存储的编辑内容
                current_sample.edited_instruction = corrected_instruction
                current_sample.edited_output = corrected_output
                
                return corrected_instruction, corrected_output, instruction_html, output_html
                    
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
            ]
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
        
        # Footer
        gr.HTML('<hr style="border: 1px solid #e0e0e0; margin: 20px 0;">')
        gr.Markdown("✅ 系统已就绪，请上传CSV文件开始校正工作")
    
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
