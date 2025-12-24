"""
UI layout components for LLM-QA Correction Workbench.

Defines the three-column Gradio layout structure with improved styling.
"""

import gradio as gr
from typing import Dict, Any


# 全局样式 - 增大字体、蓝色分割线、紧凑布局、Times New Roman字体
GLOBAL_CSS = """
<style>
/* 全局字体设置 - 英文使用Times New Roman */
* {
    font-family: "Times New Roman", "SimSun", "宋体", serif !important;
}

/* 全局字体增大 */
.gradio-container {
    font-size: 18px !important;
    font-family: "Times New Roman", "SimSun", "宋体", serif !important;
}

/* 标题字体 */
h1 { 
    font-size: 32px !important; 
    font-family: "Times New Roman", "SimSun", "宋体", serif !important;
}
h2 { 
    font-size: 26px !important; 
    font-family: "Times New Roman", "SimSun", "宋体", serif !important;
}
h3 { 
    font-size: 22px !important; 
    font-family: "Times New Roman", "SimSun", "宋体", serif !important;
}

/* 文本框字体增大 */
textarea, input, .prose {
    font-size: 18px !important;
    line-height: 1.6 !important;
    font-family: "Times New Roman", "SimSun", "宋体", serif !important;
}

/* 按钮字体 */
button {
    font-size: 16px !important;
    font-family: "Times New Roman", "SimSun", "宋体", serif !important;
}

/* 参考内容区域样式 - 带滚动条 */
.reference-content {
    font-size: 18px !important;
    line-height: 1.8 !important;
    padding: 15px;
    background: #fafafa;
    border: 1px solid #1976d2;
    border-radius: 8px;
    font-family: "Times New Roman", "SimSun", "宋体", serif !important;
}

/* ========== 关键：参考内容区域LaTeX渲染容器 ========== */
/* ⚠️ 重要：模仿数据校正区域文本框的样式，滚动条在边框内部 */
#reference_display {
    border: 2px solid #1976d2 !important;
    border-radius: 8px !important;
    max-height: 600px !important;
    height: 600px !important;
    overflow-y: auto !important;
    overflow-x: hidden !important;
    padding: 0 !important;
    background: #fafafa !important;
}

/* 内层容器：LaTeX在此渲染，无边框只有内边距 */
.reference-content {
    font-size: 18px !important;
    line-height: 1.8 !important;
    font-family: "Times New Roman", "SimSun", "宋体", serif !important;
    padding: 15px !important;
    background: transparent !important;
    border: none !important;
    box-sizing: border-box !important;
}

/* 样本列表样式 */
.sample-list-container {
    max-height: 600px;
    height: 600px;
    overflow-y: auto;
    border: 1px solid #1976d2;
    border-radius: 8px;
    padding: 10px;
    font-family: "Times New Roman", "SimSun", "宋体", serif !important;
}

/* 隐藏的样本点击索引输入框 */
.hidden-click-input {
    position: absolute !important;
    opacity: 0 !important;
    pointer-events: none !important;
    width: 1px !important;
    height: 1px !important;
    overflow: hidden !important;
}

/* 进度条样式 */
.progress-bar {
    background: linear-gradient(90deg, #4CAF50, #8BC34A);
    padding: 8px 12px;
    border-radius: 6px;
    color: white;
    font-weight: bold;
    text-align: center;
    margin: 5px 0;
    font-family: "Times New Roman", "SimSun", "宋体", serif !important;
}

/* 阶段标题样式 */
.phase-title {
    background: #e3f2fd;
    color: #1976d2;
    border: 1px solid #1976d2;
    padding: 8px 12px;
    border-radius: 6px;
    font-size: 18px !important;
    font-weight: bold;
    margin-bottom: 10px;
    font-family: "Times New Roman", "SimSun", "宋体", serif !important;
}

/* 列标题样式 */
.column-title {
    background: #e3f2fd;
    padding: 8px 12px;
    border-radius: 6px;
    border-left: 4px solid #1976d2;
    font-size: 18px !important;
    font-weight: bold;
    margin-bottom: 8px;
    font-family: "Times New Roman", "SimSun", "宋体", serif !important;
}

/* 文本框标签样式 */
.textbox-label {
    font-size: 16px !important;
    font-weight: bold;
    color: #333;
    margin-bottom: 3px;
    font-family: "Times New Roman", "SimSun", "宋体", serif !important;
}

/* 数据加载状态样式 - 简洁单层设计 */
.load-status {
    padding: 10px 15px !important;
    border-radius: 6px !important;
    font-size: 16px !important;
    font-weight: bold !important;
    margin: 0 !important;
    font-family: "Times New Roman", "SimSun", "宋体", serif !important;
    background: #fafafa !important;
    border: 2px solid #90caf9 !important;
}

.load-status p {
    margin: 0 !important;
    padding: 0 !important;
}

/* 按钮功能色彩区分 */
.nav-btn {
    font-size: 14px !important;
    padding: 6px 12px !important;
    background: #e3f2fd !important;
    border: 1px solid #1976d2 !important;
    color: #1976d2 !important;
}

.primary-btn {
    font-size: 16px !important;
    padding: 10px 20px !important;
    background: #1976d2 !important;
    color: white !important;
}

.success-btn {
    background: #4CAF50 !important;
    color: white !important;
}

.danger-btn {
    background: #f44336 !important;
    color: white !important;
}

.warning-btn {
    background: #ff9800 !important;
    color: white !important;
}

.secondary-btn {
    background: #e3f2fd !important;
    color: #1976d2 !important;
    border: 1px solid #1976d2 !important;
}

/* 紧凑间距 */
.compact-row {
    margin: 3px 0 !important;
}

.compact-group {
    margin: 5px 0 !important;
}

/* 大文本框样式 */
.large-textbox textarea {
    font-size: 18px !important;
    min-height: 120px !important;
    font-family: "Times New Roman", "SimSun", "宋体", serif !important;
}

/* 中等文本框样式 */
.medium-textbox textarea {
    font-size: 18px !important;
    min-height: 180px !important;
    font-family: "Times New Roman", "SimSun", "宋体", serif !important;
}

/* 小文件上传框 */
.small-file-upload {
    height: 60px !important;
}

/* 大字体文本 */
.large-text {
    font-size: 20px !important;
    line-height: 1.8 !important;
    font-family: "Times New Roman", "SimSun", "宋体", serif !important;
}

/* 紧凑间距 - 去除多余空白 */
.compact-status {
    margin: 0 !important;
    padding: 0 !important;
}

/* 下拉框标题字体放大 - 原来的2倍 (原18px -> 36px) */
.accordion-container .accordion-header,
.accordion-container summary,
.accordion-container .accordion-title,
.accordion-container details summary {
    font-size: 36px !important;
    font-weight: bold !important;
    font-family: "Times New Roman", "SimSun", "宋体", serif !important;
}

/* 下拉框边缘线条 */
.accordion-container {
    border: 2px solid #1976d2 !important;
    border-radius: 8px !important;
    padding: 5px !important;
}

/* Gradio Accordion组件的标题样式 - 原来的2倍 */
.accordion-container .gr-accordion .gr-accordion-header {
    font-size: 36px !important;
    font-weight: bold !important;
    font-family: "Times New Roman", "SimSun", "宋体", serif !important;
}

/* Gradio Accordion summary span 标题样式 - 原来的2倍 */
.accordion-container summary span {
    font-size: 36px !important;
    font-weight: bold !important;
    font-family: "Times New Roman", "SimSun", "宋体", serif !important;
}

/* Markdown内容字体 */
.markdown-text, .prose, p, div {
    font-family: "Times New Roman", "SimSun", "宋体", serif !important;
}

/* 下拉选择框字体 */
select, option {
    font-family: "Times New Roman", "SimSun", "宋体", serif !important;
}

/* 标签字体 */
label {
    font-family: "Times New Roman", "SimSun", "宋体", serif !important;
}

/* 文件上传框边缘线条 */
.file-upload-container {
    border: 2px solid #1976d2 !important;
    border-radius: 8px !important;
    padding: 5px !important;
}

/* 可编辑文本框样式 - 浅蓝色边缘线 */
.editable-textbox {
    border: 2px solid #90caf9 !important;
    border-radius: 6px !important;
    font-family: "Times New Roman", "SimSun", "宋体", serif !important;
    font-size: 18px !important;
    overflow-y: auto !important;
}

/* 可编辑文本框内部textarea也要有浅蓝色边缘线 */
.editable-textbox textarea {
    border: 2px solid #90caf9 !important;
    border-radius: 6px !important;
}

/* 差异显示框样式 - 浅蓝色边缘线 */
.diff-display-box {
    border: 2px solid #90caf9 !important;
    border-radius: 6px !important;
    font-family: "Times New Roman", "SimSun", "宋体", serif !important;
    font-size: 18px !important;
    overflow-y: auto !important;
    max-height: 300px !important;
}

/* 可编辑的差异显示框样式 */
.editable-diff-display {
    border: 2px solid #90caf9 !important;
    border-radius: 6px !important;
    padding: 10px !important;
    background: #fafafa !important;
    font-family: "Times New Roman", "SimSun", "宋体", serif !important;
    font-size: 18px !important;
    line-height: 1.8 !important;
    overflow-y: auto !important;
}

/* 差异框内的内容盒子 */
.diff-editable-box {
    padding: 10px;
    background: #fafafa;
    border-radius: 5px;
    font-family: "Times New Roman", "SimSun", "宋体", serif !important;
    font-size: 18px !important;
    line-height: 1.8 !important;
}

/* KaTeX渲染目标容器 */
.katex-render-target {
    font-family: "Times New Roman", "SimSun", "宋体", serif !important;
    font-size: 18px !important;
    line-height: 1.8 !important;
}

/* 差异文本框样式 - 用于显示带<false>/<true>标记的文本 */
.diff-textbox textarea {
    font-family: "Times New Roman", "SimSun", "宋体", serif !important;
    font-size: 18px !important;
    line-height: 1.8 !important;
    white-space: pre-wrap !important;
}
</style>
"""


def get_global_css() -> str:
    """返回全局CSS样式"""
    return GLOBAL_CSS


def create_header_with_instructions(components: Dict[str, Any]) -> None:
    """创建标题行与使用说明、设置（第一行）"""
    # 第一行：应用标题、使用说明、设置在同一行，对齐下方三列比例(1:5:4)
    with gr.Row():
        # 应用标题 - 对齐左侧导航列
        with gr.Column(scale=1):
            gr.Markdown("# 🎯 大模型数据校正")
        
        # 使用说明下拉框 - 对齐中间数据校正区域
        with gr.Column(scale=5):
            with gr.Accordion("📖 使用说明（首次使用必看！）", open=False, elem_classes=["accordion-container"]):
                gr.Markdown("""
**详细操作流程：**

**1. 上传CSV文件：** 准备包含instruction（问题）、output（回答）、chunk（参考内容）三列的CSV文件，点击"上传CSV文件"按钮选择文件，系统会自动加载前50条数据。

**2. 查看样本列表：** 左侧显示所有加载的样本，⭕表示待处理，✅表示已校正，❌表示已丢弃。

**3. 首次校正：** 在中间区域"阶段1：首次校正"中编辑问题和回答内容，可以修改、完善或重写。

**4. 生成预览：** 编辑完成后点击"生成校正预览"按钮，进入"阶段2：校正确认"。

**5. 确认差异：** 查看校正前后的差异对比，红色表示模型生成的错误内容（将被删除），绿色表示人工校正后的正确内容（新增或修正）。

**6. 提交或丢弃：** 确认无误后点击"提交最终样本"保存校正结果，或点击"丢弃此样本"跳过当前样本。

**7. 导出数据：** 完成所有样本校正后，点击"导出已校正数据"按钮生成JSON文件，文件名格式为"原文件名_时间戳_校正样本数.json"。

**8. 下载文件：** 导出成功后，在"导出文件下载"框中点击下载生成的文件。
                """)
        
        # 设置下拉框
        with gr.Column(scale=2):
            with gr.Accordion("⚙️ 设置", open=False, elem_classes=["accordion-container"]):
                components['batch_size_input'] = gr.Number(
                    label="每批加载数量",
                    value=50,
                    minimum=10,
                    maximum=200
                )
                
                components['export_format_dropdown'] = gr.Dropdown(
                    choices=[
                        ("Messages格式", "messages"),
                        ("ShareGPT格式", "sharegpt"),
                        ("Query-Response格式", "query-response"),
                        ("Alpaca格式", "alpaca")
                    ],
                    value="messages",
                    label="导出格式"
                )
                
                components['export_filename_input'] = gr.Textbox(
                    label="自定义导出文件名",
                    placeholder="原文件名_时间戳_样本数.json"
                )
    
    gr.HTML('<hr style="border: 2px solid #1976d2; margin: 3px 0;">')


def create_upload_export_row(components: Dict[str, Any]) -> None:
    """创建数据加载状况、上传CSV、导出文件下载、导出按钮（第二行）"""
    with gr.Row():
        # 数据加载状况显示 - 缩短宽度
        with gr.Column(scale=0.3):
            components['upload_status'] = gr.HTML(
                '<div class="load-status">📁 等待上传CSV文件<br>当前样本: - / -</div>'
            )
        
        # 上传CSV文件
        with gr.Column(scale=2):
            components['csv_upload'] = gr.File(
                label="📁 上传CSV文件",
                file_types=[".csv"],
                type="filepath",
                height=100,
                elem_classes=["file-upload-container"]
            )
        
        # 导出按钮
        with gr.Column(scale=2):
            components['export_btn'] = gr.Button(
                "💾 导出已校正数据",
                size="lg",
                elem_classes=["success-btn"]
            )

        # 文件导出下载框 - 默认隐藏
        with gr.Column(scale=2):
            components['export_file'] = gr.File(
                label="📥 导出文件下载",
                interactive=False,
                height=100,
                visible=False
            )
        




def create_column_titles() -> None:
    """创建三列标题行（第四行）"""
    with gr.Row(elem_classes=["compact-row"]):
        with gr.Column(scale=1):  # 左侧导航列：最小宽度
            gr.HTML('<div class="column-title">📋 样本导航</div>')
        with gr.Column(scale=5):  # 中间数据校正区域：最大宽度
            gr.HTML('<div class="column-title">📝 数据校正区域</div>')
        with gr.Column(scale=4):  # 右侧参考内容列：中等宽度
            gr.HTML('<div class="column-title">📚 参考内容</div>')


def create_left_column(components: Dict[str, Any]) -> None:
    """创建左侧列布局"""
    # 第一行：收起/展开导航按钮并排
    with gr.Row(elem_classes=["compact-row"]):
        components['collapse_btn'] = gr.Button(
            "◀ 收起导航",
            size="sm",
            elem_classes=["nav-btn"]
        )
        components['expand_btn'] = gr.Button(
            "▶ 展开导航",
            size="sm",
            visible=False,
            elem_classes=["nav-btn"]
        )
    
    # 第二行：上一条/下一条按钮并排
    with gr.Row(elem_classes=["compact-row"]):
        components['prev_btn'] = gr.Button(
            "⬅️ 上一条",
            size="sm",
            elem_classes=["nav-btn"]
        )
        components['next_btn'] = gr.Button(
            "下一条 ➡️",
            size="sm",
            elem_classes=["nav-btn"]
        )
    
    # 统计显示框（放在下一条按钮下方，宽度一致）
    components['stats_display'] = gr.HTML(
        '<div style="padding: 8px; margin: 5px 0; background: #f5f5f5; border: 1px solid #1976d2; border-radius: 5px; font-size: 14px; text-align: center;">📊 统计: 待处理 <span style="color: #9E9E9E;">0</span> | 已校正 <span style="color: #4CAF50;">0</span> | 已丢弃 <span style="color: #F44336;">0</span></div>'
    )
    
    # 隐藏的样本索引输入框（用于接收点击事件）
    # 使用elem_classes来CSS隐藏，而不是visible=False（那样会完全不渲染）
    components['sample_click_index'] = gr.Number(
        value=-1,
        label="",
        show_label=False,
        elem_id="sample_click_index",
        elem_classes="hidden-click-input",
        minimum=-1,
        maximum=999999,
        container=False
    )
    
    # 样本导航列表（移除了进度条）
    components['sample_list'] = gr.HTML(
        '<div class="sample-list-container">加载数据后显示样本列表</div>'
    )
    



def create_center_column(components: Dict[str, Any]) -> None:
    """创建中间列布局"""
    # Phase 1: 首次校正
    with gr.Group(visible=True) as phase1_group:
        components['phase1_group'] = phase1_group
        
        # 子标题行
        gr.HTML('<div class="phase-title">📝 阶段1：首次校正</div>')
        
        # 问题标题行及文本框
        gr.HTML('<div class="textbox-label">❓ 问题 (Instruction)</div>')
        components['instruction_editor'] = gr.Textbox(
            label="",
            lines=5,
            max_lines=8,
            placeholder="在此编辑问题内容...",
            show_label=False,
            elem_classes=["large-textbox", "editable-textbox"],
            interactive=True
        )
        
        # 回答标题行及文本框
        gr.HTML('<div class="textbox-label">💬 回答 (Output)</div>')
        components['output_editor'] = gr.Textbox(
            label="",
            lines=8,
            max_lines=15,
            placeholder="在此编辑回答内容...",
            show_label=False,
            elem_classes=["medium-textbox", "editable-textbox"],
            interactive=True
        )
        
        # 生成校正预览按钮
        components['generate_preview_btn'] = gr.Button(
            "🔍 生成校正预览",
            size="lg",
            elem_classes=["primary-btn"]
        )
        
        # 丢弃此样本按钮（阶段一）
        components['discard_phase1_btn'] = gr.Button(
            "❌ 丢弃此样本",
            size="lg",
            elem_classes=["danger-btn"]
        )
    
    # Phase 2: 校正确认
    with gr.Group(visible=False) as phase2_group:
        components['phase2_group'] = phase2_group
        
        # 子标题行
        gr.HTML('<div class="phase-title">✅ 阶段2：校正确认（可在下方文本框中编辑，点击刷新更新差异）</div>')
        
        # 校正后问题 - 上方显示渲染后的差异，下方提供编辑框
        gr.HTML('<div class="textbox-label">❓ 校正后问题（红色删除线：模型错误内容，绿色：人工校正内容）</div>')
        components['corrected_instruction_display'] = gr.HTML(
            label="",
            value='<div class="diff-render-box" style="padding: 10px; background: #fafafa; border: 2px solid #90caf9; border-radius: 6px; min-height: 80px; font-size: 18px; line-height: 1.8;">校正后的问题内容...</div>'
        )
        gr.HTML('<div style="margin-top: 5px; margin-bottom: 3px; font-size: 14px; color: #666;">✏️ 编辑区（修改后点击"刷新校正结果"更新上方差异显示）：</div>')
        components['corrected_instruction_editor'] = gr.Textbox(
            label="",
            lines=5,
            max_lines=8,
            placeholder="在此编辑问题内容...",
            show_label=False,
            elem_classes=["large-textbox", "editable-textbox"],
            interactive=True
        )
        
        # 校正后回答 - 上方显示渲染后的差异，下方提供编辑框
        gr.HTML('<div class="textbox-label" style="margin-top: 15px;">💬 校正后回答（红色删除线：模型错误内容，绿色：人工校正内容）</div>')
        components['corrected_output_display'] = gr.HTML(
            label="",
            value='<div class="diff-render-box" style="padding: 10px; background: #fafafa; border: 2px solid #90caf9; border-radius: 6px; min-height: 150px; font-size: 18px; line-height: 1.8;">校正后的回答内容...</div>'
        )
        gr.HTML('<div style="margin-top: 5px; margin-bottom: 3px; font-size: 14px; color: #666;">✏️ 编辑区（修改后点击"刷新校正结果"更新上方差异显示）：</div>')
        components['corrected_output_editor'] = gr.Textbox(
            label="",
            lines=8,
            max_lines=15,
            placeholder="在此编辑回答内容...",
            show_label=False,
            elem_classes=["medium-textbox", "editable-textbox"],
            interactive=True
        )
        
        # 三个按钮并排
        with gr.Row(elem_classes=["compact-row"]):
            components['discard_btn'] = gr.Button(
                "❌ 丢弃此样本",
                size="lg",
                elem_classes=["danger-btn"]
            )
            components['refresh_btn'] = gr.Button(
                "🔄 刷新校正结果",
                size="lg",
                elem_classes=["secondary-btn"]
            )
            components['submit_btn'] = gr.Button(
                "✅ 提交最终样本",
                size="lg",
                elem_classes=["success-btn"]
            )


def create_right_column(components: Dict[str, Any]) -> None:
    """创建右侧列布局"""
    # 参考内容文本框 - 高度为问题+回答文本框高度之和，带滚动条
    components['reference_display'] = gr.HTML(
        value='<div class="reference-content">参考内容将在此显示</div>',
        label="",
        elem_id="reference_display"
    )


def create_three_column_layout() -> Dict[str, Any]:
    """
    创建完整的三列布局结构
    
    Returns:
        包含所有UI组件的字典
    """
    
    components = {}

    # 注入全局CSS
    gr.HTML(get_global_css())
    
    # 第一行：应用标题、使用说明、设置
    create_header_with_instructions(components)
    
    # 第二行：数据加载状况、上传CSV、导出文件下载、导出按钮
    create_upload_export_row(components)
    
    # 第三行：三列标题
    create_column_titles()
    
    # 第四行开始：三列详细布局
    with gr.Row():
        # 左侧区域：导航 + 展开按钮（最小宽度）
        with gr.Column(scale=1):
            # 左侧列：导航 (可收起)
            with gr.Column(visible=True) as left_col:
                components['left_col'] = left_col
                create_left_column(components)
            
            # 独立的展开按钮（当左侧列隐藏时显示）
            components['standalone_expand_btn'] = gr.Button(
                "▶ 展开导航",
                size="sm",
                visible=False,
                elem_classes=["nav-btn"]
            )
        
        # 中间列：编辑器（最大宽度）
        with gr.Column(scale=5):
            create_center_column(components)
        
        # 右侧列：参考内容（中等宽度）
        with gr.Column(scale=4):
            create_right_column(components)
    
    return components


# 保留旧函数以保持兼容性
def create_usage_instructions() -> gr.Accordion:
    """
    创建使用说明折叠框（兼容旧版本）
    """
    with gr.Accordion("📖 使用说明", open=True) as accordion:
        gr.Markdown("""
**操作流程：** 上传CSV文件 → 编辑问题和回答 → 生成校正预览 → 提交最终样本 → 导出数据
        """)
    return accordion


def create_csv_upload() -> gr.File:
    """
    创建CSV文件上传组件（兼容旧版本）
    """
    return gr.File(
        label="📁 上传CSV文件",
        file_types=[".csv"],
        type="filepath"
    )
