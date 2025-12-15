"""
LLM-QA Correction Workbench
大模型问答数据校正工作台

Main entry point for the Gradio application.
"""

import gradio as gr
from ui import create_three_column_layout, create_usage_instructions, create_csv_upload
from ui.event_handlers import (
    handle_csv_upload,
    load_sample_to_ui,
    handle_generate_preview,
    handle_submit,
    handle_discard,
    handle_refresh_diff,
    handle_export,
    handle_navigation
)
from services import RenderEngine


def main():
    """Main application entry point."""
    # Initialize render engine for KaTeX support
    render_engine = RenderEngine()
    
    with gr.Blocks(
        title="LLM-QA Correction Workbench",
        theme=gr.themes.Soft(),
        head=render_engine.get_katex_header()
    ) as app:
        # Header
        gr.Markdown("# 🎯 LLM-QA Correction Workbench")
        gr.Markdown("### 大模型问答数据校正工作台")
        
        # CSV Upload
        csv_upload = create_csv_upload()
        upload_status = gr.Markdown("📁 请上传CSV文件开始")
        
        # Application State
        app_state = gr.State({
            "current_index": 0,
            "samples": [],
            "data_manager": None,
            "export_manager": None,
            "phase": 1,
            "batch_size": 50,
            "export_format": "messages"
        })
        
        # Three-column layout
        components = create_three_column_layout()
        
        # Usage instructions
        instructions = create_usage_instructions()
        
        # Inject WYSIWYG controls
        gr.HTML(render_engine.inject_wysiwyg_controls())
        
        # Wire CSV upload handler with error handling
        def on_csv_upload(file_path, batch_size):
            new_state, msg = handle_csv_upload(file_path, batch_size)
            if new_state.get('samples'):
                # Load first sample to UI
                instruction, output, ref_html, progress, sample_list = load_sample_to_ui(new_state)
                return new_state, msg, instruction, output, ref_html, progress, sample_list
            return new_state, msg, "", "", "<div>暂无数据</div>", "**进度**: 0 / 0", "<div>暂无数据</div>"
        
        csv_upload.upload(
            fn=on_csv_upload,
            inputs=[csv_upload, components['batch_size_input']],
            outputs=[
                app_state,
                upload_status,
                components['instruction_editor'],
                components['output_editor'],
                components['reference_display'],
                components['progress_display'],
                components['sample_list']
            ]
        )
        
        # Wire navigation buttons
        components['prev_btn'].click(
            fn=lambda state: handle_navigation("prev", state),
            inputs=[app_state],
            outputs=[
                app_state,
                components['instruction_editor'],
                components['output_editor'],
                components['reference_display'],
                components['progress_display'],
                components['sample_list']
            ]
        )
        
        components['next_btn'].click(
            fn=lambda state: handle_navigation("next", state),
            inputs=[app_state],
            outputs=[
                app_state,
                components['instruction_editor'],
                components['output_editor'],
                components['reference_display'],
                components['progress_display'],
                components['sample_list']
            ]
        )
        
        # Wire generate preview button
        def on_generate_preview(instruction, output, state):
            state, original, diff, phase1_vis, phase2_vis = handle_generate_preview(instruction, output, state)
            return state, original, diff, gr.update(visible=phase1_vis), gr.update(visible=phase2_vis)
        
        components['generate_preview_btn'].click(
            fn=on_generate_preview,
            inputs=[
                components['instruction_editor'],
                components['output_editor'],
                app_state
            ],
            outputs=[
                app_state,
                components['original_display'],
                components['diff_editor'],
                components['phase1_group'],
                components['phase2_group']
            ]
        )
        
        # Wire submit button
        def on_submit(state):
            state, instruction, output, reference, progress, sample_list, phase1_vis, phase2_vis = handle_submit(state)
            return state, instruction, output, reference, progress, sample_list, gr.update(visible=phase1_vis), gr.update(visible=phase2_vis)
        
        components['submit_btn'].click(
            fn=on_submit,
            inputs=[app_state],
            outputs=[
                app_state,
                components['instruction_editor'],
                components['output_editor'],
                components['reference_display'],
                components['progress_display'],
                components['sample_list'],
                components['phase1_group'],
                components['phase2_group']
            ]
        )
        
        # Wire discard button
        def on_discard(state):
            state, instruction, output, reference, progress, sample_list, phase1_vis, phase2_vis = handle_discard(state)
            return state, instruction, output, reference, progress, sample_list, gr.update(visible=phase1_vis), gr.update(visible=phase2_vis)
        
        components['discard_btn'].click(
            fn=on_discard,
            inputs=[app_state],
            outputs=[
                app_state,
                components['instruction_editor'],
                components['output_editor'],
                components['reference_display'],
                components['progress_display'],
                components['sample_list'],
                components['phase1_group'],
                components['phase2_group']
            ]
        )
        
        # Wire refresh button
        components['refresh_btn'].click(
            fn=handle_refresh_diff,
            inputs=[components['diff_editor'], app_state],
            outputs=[components['diff_editor']]
        )
        
        # Wire export button
        components['export_btn'].click(
            fn=handle_export,
            inputs=[app_state],
            outputs=[gr.File(), upload_status]
        )
        
        gr.Markdown("---")
        gr.Markdown("✅ 所有事件处理器已连接")
    
    return app


if __name__ == "__main__":
    app = main()
    app.launch()
