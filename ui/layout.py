"""
UI layout components for LLM-QA Correction Workbench.

Defines the three-column Gradio layout structure.
"""

import gradio as gr
from typing import Dict, Any


def create_three_column_layout() -> Dict[str, Any]:
    """
    Create the three-column layout structure.
    
    Returns:
        Dictionary containing all UI components
    """
    components = {}
    
    with gr.Row():
        # Left Column: Navigation (scale=2)
        with gr.Column(scale=2, visible=True) as left_col:
            components['left_col'] = left_col
            
            with gr.Row():
                components['prev_btn'] = gr.Button("⬅️ 上一条", size="sm")
                components['next_btn'] = gr.Button("下一条 ➡️", size="sm")
            
            components['progress_display'] = gr.Markdown("**进度**: 0 / 0")
            components['sample_list'] = gr.HTML("<div>加载数据后显示样本列表</div>")
            
            components['collapse_btn'] = gr.Button("◀ 收起导航", size="sm")
        
        # Center Column: Editor (scale=5)
        with gr.Column(scale=5):
            gr.Markdown("## 📝 数据校正区域")
            
            # Phase 1: Initial Editing
            with gr.Group() as phase1_group:
                components['phase1_group'] = phase1_group
                gr.Markdown("### Phase 1: 初次编辑")
                
                components['instruction_editor'] = gr.Textbox(
                    label="问题 (Instruction)",
                    lines=5,
                    placeholder="在此编辑问题内容..."
                )
                
                components['output_editor'] = gr.Textbox(
                    label="回答 (Output)",
                    lines=10,
                    placeholder="在此编辑回答内容..."
                )
                
                with gr.Row():
                    components['bold_btn'] = gr.Button("**B** 加粗", size="sm")
                    components['list_btn'] = gr.Button("• 列表", size="sm")
                
                components['generate_preview_btn'] = gr.Button(
                    "🔍 生成校正预览",
                    variant="primary",
                    size="lg"
                )
            
            # Phase 2: Diff Confirmation
            with gr.Group(visible=False) as phase2_group:
                components['phase2_group'] = phase2_group
                gr.Markdown("### Phase 2: 差异确认")
                
                components['original_display'] = gr.Markdown(
                    label="原始内容（只读）",
                    value="原始内容将在此显示"
                )
                
                components['diff_editor'] = gr.HTML(
                    label="校正结果（可编辑）",
                    value="<div>差异结果将在此显示</div>"
                )
                
                with gr.Row():
                    components['discard_btn'] = gr.Button(
                        "❌ 丢弃此样本",
                        variant="stop"
                    )
                    components['refresh_btn'] = gr.Button("🔄 刷新校正结果")
                    components['submit_btn'] = gr.Button(
                        "✅ 提交最终样本",
                        variant="primary"
                    )
        
        # Right Column: Reference & Tools (scale=3)
        with gr.Column(scale=3):
            gr.Markdown("## 🔧 工具与参考")
            
            with gr.Row():
                components['export_btn'] = gr.Button("💾 导出数据", variant="secondary")
                components['settings_btn'] = gr.Button("⚙️ 设置")
            
            components['reference_display'] = gr.HTML(
                label="参考内容 (Chunk)",
                value="<div>参考内容将在此显示</div>"
            )
            
            # Settings Panel (collapsed by default)
            with gr.Accordion("⚙️ 设置", open=False) as settings_panel:
                components['settings_panel'] = settings_panel
                
                components['batch_size_input'] = gr.Number(
                    label="每批加载数量",
                    value=50,
                    minimum=10,
                    maximum=200
                )
                
                components['export_format_dropdown'] = gr.Dropdown(
                    choices=["messages", "alpaca", "sharegpt", "query-response"],
                    value="messages",
                    label="导出格式"
                )
    
    return components


def create_usage_instructions() -> gr.Accordion:
    """
    Create usage instructions accordion.
    
    Returns:
        Gradio Accordion component
    """
    with gr.Accordion("📖 使用说明", open=True) as accordion:
        gr.Markdown("""
        ### 操作流程
        
        1. **上传数据**: 点击下方上传 CSV 文件，系统自动加载前 50 条数据
        2. **初次编辑**: 在 Phase 1 区域编辑问题和回答，点击"生成校正预览"
        3. **差异确认**: 在 Phase 2 区域查看标记结果，可进行二次编辑
        4. **提交样本**: 点击"提交最终样本"保存，或"丢弃此样本"跳过
        5. **导航切换**: 使用左侧导航或上下按钮切换样本
        6. **导出数据**: 完成后点击"导出数据"下载 JSON 文件
        
        ### 快捷键
        
        - **Ctrl+B**: 加粗选中文本
        - **Ctrl+I**: 斜体选中文本
        - **Ctrl+L**: 将选中文本转为列表
        
        ### 格式支持
        
        - **Markdown**: 支持 `**粗体**`、`*斜体*`、`- 列表` 等格式
        - **LaTeX**: 支持 `$公式$` 和 `$$公式$$` 数学公式
        """)
    
    return accordion


def create_csv_upload() -> gr.File:
    """
    Create CSV file upload component.
    
    Returns:
        Gradio File component
    """
    return gr.File(
        label="📁 上传 CSV 文件",
        file_types=[".csv"],
        type="filepath"
    )
