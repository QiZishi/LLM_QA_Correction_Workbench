"""
KaTeX渲染调试工具 - 带终端输出
"""

import gradio as gr
from services.render_engine import RenderEngine
import sys

def debug_render(text):
    """调试渲染函数，输出详细信息到终端"""
    print("\n" + "="*80)
    print("🔍 开始渲染调试")
    print("="*80)
    
    render_engine = RenderEngine()
    
    # 1. 输出原始文本
    print(f"📝 原始文本:\n{text[:200]}...")
    print()
    
    # 2. 检测LaTeX
    has_dollar = '$' in text
    print(f"💲 包含'$'符号: {has_dollar}")
    print()
    
    # 3. 渲染
    try:
        html_output = render_engine.render_markdown_latex(text)
        print(f"✅ 渲染成功")
        print(f"📄 HTML长度: {len(html_output)} 字符")
        print()
        
        # 4. 检查HTML关键元素
        print("🔎 HTML内容检查:")
        print(f"  - 包含 '$': {('$' in html_output)}")
        print(f"  - 包含 'data-katex-render': {('data-katex-render' in html_output)}")
        print(f"  - 包含 'katex-render-target': {('katex-render-target' in html_output)}")
        print(f"  - 包含 '\\mathrm{{h}}': {('mathrm{h}' in html_output)}")
        print()
        
        # 5. 输出HTML片段
        print("📋 HTML输出预览:")
        print(html_output[:500])
        print("...")
        print(html_output[-200:])
        print()
        
        return html_output
        
    except Exception as e:
        print(f"❌ 渲染失败: {e}")
        import traceback
        traceback.print_exc()
        return f"<div style='color:red;'>渲染错误: {e}</div>"

def create_debug_app():
    """创建调试应用"""
    
    render_engine = RenderEngine()
    
    with gr.Blocks(
        title="KaTeX渲染调试工具",
        head=render_engine.get_katex_header()
    ) as app:
        
        gr.Markdown("# 🔬 KaTeX渲染调试工具")
        gr.Markdown("**在终端查看详细的渲染日志**")
        
        with gr.Row():
            with gr.Column():
                input_text = gr.Textbox(
                    label="输入包含LaTeX的文本",
                    lines=10,
                    value="""所有发病 $< 12\\mathrm{h}$ 的STEMI患者均首选直接（急诊）PCI以改善预后[4-5,7,12,65]（Ⅰ，A）。

高危者，建议发病 $24\\mathrm{h}$ 内转运至PCI中心行早期 $< 24\\mathrm{h}$ S

或住院期间PCI；非高危者，建议转运至PCI中心。"""
                )
                
                render_btn = gr.Button("🔄 渲染并调试", size="lg")
            
            with gr.Column():
                output_html = gr.HTML(label="渲染结果")
        
        # 监听渲染事件
        def on_render(text):
            print("\n" + "🚀 " * 40)
            print("用户点击了渲染按钮")
            print("🚀 " * 40)
            
            result = debug_render(text)
            
            print("\n" + "✨ " * 40)
            print("渲染完成，HTML已返回到前端")
            print("✨ " * 40)
            print()
            
            return result
        
        render_btn.click(
            fn=on_render,
            inputs=[input_text],
            outputs=[output_html]
        )
        
        # 页面加载时的诊断
        def on_load():
            print("\n" + "🌐 " * 40)
            print("Gradio应用已启动")
            print("🌐 " * 40)
            print()
            print("📋 KaTeX配置:")
            print(f"  - get_katex_header() 方法存在: {hasattr(render_engine, 'get_katex_header')}")
            
            header = render_engine.get_katex_header()
            print(f"  - Header长度: {len(header)} 字符")
            print(f"  - 包含CSS链接: {'katex.min.css' in header}")
            print(f"  - 包含JS链接: {'katex.min.js' in header}")
            print(f"  - 包含auto-render: {'auto-render.min.js' in header}")
            print(f"  - 包含renderAllMath函数: {'renderAllMath' in header}")
            print()
            
            return "调试应用已加载，请输入文本并点击渲染"
        
        gr.Textbox(
            value=on_load,
            visible=False
        )
        
        gr.Markdown("""
---
### 📖 使用说明

1. **终端输出**：所有调试信息会在运行此脚本的终端中显示
2. **渲染测试**：修改左侧文本框内容，点击"渲染并调试"按钮
3. **查看结果**：右侧显示渲染后的HTML，终端显示详细日志

### 🔍 终端输出内容

- ✅ 渲染成功/失败状态
- 📝 原始文本内容
- 💲 LaTeX符号检测
- 📄 生成的HTML长度
- 🔎 HTML关键元素检查
- 📋 HTML输出预览
        """)
    
    return app

if __name__ == "__main__":
    print("\n" + "🎯 " * 40)
    print("KaTeX渲染调试工具启动中...")
    print("🎯 " * 40)
    print()
    
    app = create_debug_app()
    
    print("✅ 应用配置完成，启动服务器...")
    print()
    
    # 强制刷新stdout
    sys.stdout.flush()
    
    app.launch(
        server_name="0.0.0.0",
        server_port=7861,
        share=False
    )
