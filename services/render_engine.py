"""
RenderEngine for Markdown and LaTeX rendering.

Handles conversion of Markdown and LaTeX to HTML, and styling of diff tags.
Supports multiple LaTeX formats for better compatibility.
"""

import re
import html
import markdown
import uuid


class RenderEngine:
    """
    Rendering engine for Markdown, LaTeX, and diff tags.
    
    Provides methods to:
    - Render Markdown to HTML
    - Render LaTeX formulas (using KaTeX/MathJax)
    - Style diff tags (<false>/<true>)
    - Inject WYSIWYG editing controls
    """
    
    # LaTeX 分隔符模式 - 支持多种格式
    LATEX_PATTERNS = [
        # Display math: $$...$$
        (r'\$\$(.+?)\$\$', 'display'),
        # Display math: \[...\]
        (r'\\\[(.+?)\\\]', 'display'),
        # Inline math: $...$  (非贪婪，避免跨行匹配)
        (r'\$([^\$\n]+?)\$', 'inline'),
        # Inline math: \(...\)
        (r'\\\((.+?)\\\)', 'inline'),
        # Display math: \begin{equation}...\end{equation}
        (r'\\begin\{equation\}(.+?)\\end\{equation\}', 'display'),
        # Display math: \begin{align}...\end{align}
        (r'\\begin\{align\*?\}(.+?)\\end\{align\*?\}', 'display'),
        # Display math: \begin{gather}...\end{gather}
        (r'\\begin\{gather\*?\}(.+?)\\end\{gather\*?\}', 'display'),
    ]
    
    def __init__(self):
        """Initialize RenderEngine with Markdown processor."""
        self.md = markdown.Markdown(extensions=['extra', 'nl2br', 'sane_lists'])
    
    def _escape_html_in_latex(self, latex_content: str) -> str:
        """
        转义 LaTeX 内容中的 HTML 特殊字符，但保留 LaTeX 命令
        """
        # 只转义 < 和 > 以防止 HTML 注入，但保留其他字符
        result = latex_content.replace('&', '&amp;')
        result = result.replace('<', '&lt;')
        result = result.replace('>', '&gt;')
        return result
    
    def _protect_latex(self, text: str) -> tuple:
        """
        保护 LaTeX 公式不被 Markdown 处理
        
        Returns:
            (处理后的文本, LaTeX占位符列表)
        """
        if not text:
            return text, []
        
        latex_placeholders = []
        placeholder_index = [0]  # 使用列表以便在闭包中修改
        
        def replace_latex(match, display_type):
            """替换 LaTeX 为占位符"""
            formula = match.group(1).strip()
            # 使用HTML注释格式的占位符,避免被Markdown解析
            unique_id = str(uuid.uuid4()).replace('-', '')
            placeholder = f"<!--LATEX_{unique_id}-->"
            latex_placeholders.append({
                'placeholder': placeholder,
                'formula': formula,
                'display': display_type,
                'original': match.group(0)
            })
            placeholder_index[0] += 1
            return placeholder
        
        result = text
        
        # 按顺序处理各种 LaTeX 模式（先处理 display，再处理 inline）
        for pattern, display_type in self.LATEX_PATTERNS:
            try:
                result = re.sub(
                    pattern,
                    lambda m, dt=display_type: replace_latex(m, dt),
                    result,
                    flags=re.DOTALL
                )
            except re.error:
                # 如果正则表达式出错，跳过该模式
                continue
        
        return result, latex_placeholders

    def _restore_latex(self, html_text: str, latex_placeholders: list) -> str:
        """
        恢复 LaTeX 公式，直接输出$...$格式供KaTeX渲染
        不需要额外的span包装，KaTeX会自动处理
        
        ⚠️ 关键修复：LaTeX公式周围的HTML实体需要保持转义状态
        但公式内部的内容不需要额外处理，KaTeX会正确渲染
        """
        result = html_text
        
        for item in latex_placeholders:
            placeholder = item['placeholder']
            formula = item['formula']
            display_type = item['display']
            original = item['original']
            
            # 直接恢复原始LaTeX格式，让KaTeX的auto-render处理
            # 不进行HTML转义，因为这些内容会被KaTeX JavaScript处理
            if display_type == 'display':
                latex_html = f'$${formula}$$'
            else:
                latex_html = f'${formula}$'
            
            result = result.replace(placeholder, latex_html)
        
        return result
    
    def render_markdown_latex(self, text: str) -> str:
        """
        Render Markdown and LaTeX to HTML.
        
        Converts Markdown syntax to HTML and preserves LaTeX formulas
        for rendering with KaTeX.
        
        Args:
            text: Text containing Markdown and/or LaTeX
        
        Returns:
            HTML string with rendered Markdown and LaTeX
        """
        if not text:
            return ""
        
        try:
            # 1. 保护 LaTeX 公式
            protected_text, latex_placeholders = self._protect_latex(text)
            
            # 2. 渲染 Markdown
            html_content = self.md.convert(protected_text)
            
            # 3. 恢复 LaTeX 公式
            if latex_placeholders:
                html_content = self._restore_latex(html_content, latex_placeholders)
            
            # 4. 重置 Markdown 处理器
            self.md.reset()
            
            # ========== 关键步骤：标记LaTeX渲染容器 ==========
            # ⚠️ data-katex-render="true" 让JavaScript能找到并渲染LaTeX
            # 不要移除这个属性，否则LaTeX无法渲染！
            return f'''
            <div class="reference-content katex-render-target" data-katex-render="true" style="font-size: 18px; line-height: 1.8; padding: 15px;">
                {html_content}
            </div>
            '''
        except Exception as e:
            # 如果渲染失败，返回原始文本（HTML转义）
            escaped_text = html.escape(text)
            return f'''
            <div class="reference-content" style="font-size: 18px; line-height: 1.8; padding: 15px;">
                <pre style="white-space: pre-wrap; word-wrap: break-word;">{escaped_text}</pre>
            </div>
            '''
    
    def render_diff_tags(self, text: str) -> str:
        """
        Convert <false>/<true> tags to styled HTML, preserving LaTeX.
        
        Applies visual styling:
        - <false> → red text with strikethrough
        - <true> → green text
        
        Also handles LaTeX formulas within diff tags.
        
        Args:
            text: Text with <false> and <true> tags (may contain LaTeX)
        
        Returns:
            HTML with styled spans and rendered LaTeX
        """
        if not text:
            return ""
        
        # 1. 先保护LaTeX公式
        protected_text, latex_placeholders = self._protect_latex(text)
        
        # 2. Replace <false> tags with styled spans
        protected_text = re.sub(
            r'<false>(.*?)</false>',
            r'<span style="color: #d32f2f; text-decoration: line-through; background: #ffebee; padding: 2px 4px; border-radius: 3px;">\1</span>',
            protected_text,
            flags=re.DOTALL
        )
        
        # 3. Replace <true> tags with styled spans
        protected_text = re.sub(
            r'<true>(.*?)</true>',
            r'<span style="color: #388e3c; background: #e8f5e9; padding: 2px 4px; border-radius: 3px;">\1</span>',
            protected_text,
            flags=re.DOTALL
        )
        
        # 4. 恢复LaTeX公式
        if latex_placeholders:
            protected_text = self._restore_latex(protected_text, latex_placeholders)
        
        # ========== 关键：标记diff内容中的LaTeX ==========
        # ⚠️ data-katex-render="true" 确保差异显示中的LaTeX也能被渲染
        return f'<div class="katex-render-target" data-katex-render="true">{protected_text}</div>'
    
    def render_markdown_latex_with_diff(self, text: str) -> str:
        """
        Render text with both Markdown/LaTeX and diff tag styling.
        
        This combines both rendering operations:
        1. First apply diff tag styling
        2. Then render Markdown and LaTeX
        
        Args:
            text: Text with Markdown, LaTeX, and diff tags
        
        Returns:
            Fully rendered HTML
        """
        # First apply diff tag styling
        html_content = self.render_diff_tags(text)
        
        return html_content
    
    def inject_wysiwyg_controls(self) -> str:
        """
        Generate JavaScript code for WYSIWYG editing controls.
        
        Provides:
        - Text selection toolbar (bold, italic, list)
        - Keyboard shortcuts (Ctrl+B for bold, etc.)
        
        Returns:
            JavaScript code as string
        """
        js_code = """
        <script>
        // WYSIWYG Editing Controls
        
        function insertMarkdown(textarea, prefix, suffix) {
            const start = textarea.selectionStart;
            const end = textarea.selectionEnd;
            const selectedText = textarea.value.substring(start, end);
            const before = textarea.value.substring(0, start);
            const after = textarea.value.substring(end);
            
            textarea.value = before + prefix + selectedText + suffix + after;
            
            // Set cursor position
            const newPos = start + prefix.length + selectedText.length + suffix.length;
            textarea.setSelectionRange(newPos, newPos);
            textarea.focus();
            
            // Trigger change event
            textarea.dispatchEvent(new Event('input', { bubbles: true }));
        }
        
        function makeBold(textarea) {
            insertMarkdown(textarea, '**', '**');
        }
        
        function makeItalic(textarea) {
            insertMarkdown(textarea, '*', '*');
        }
        
        function makeList(textarea) {
            const start = textarea.selectionStart;
            const end = textarea.selectionEnd;
            const selectedText = textarea.value.substring(start, end);
            const lines = selectedText.split('\\n');
            const listText = lines.map(line => '- ' + line).join('\\n');
            
            const before = textarea.value.substring(0, start);
            const after = textarea.value.substring(end);
            
            textarea.value = before + listText + after;
            textarea.focus();
            textarea.dispatchEvent(new Event('input', { bubbles: true }));
        }
        
        // Keyboard shortcuts
        document.addEventListener('keydown', function(e) {
            const target = e.target;
            if (target.tagName !== 'TEXTAREA') return;
            
            // Ctrl+B for bold
            if (e.ctrlKey && e.key === 'b') {
                e.preventDefault();
                makeBold(target);
            }
            
            // Ctrl+I for italic
            if (e.ctrlKey && e.key === 'i') {
                e.preventDefault();
                makeItalic(target);
            }
            
            // Ctrl+L for list
            if (e.ctrlKey && e.key === 'l') {
                e.preventDefault();
                makeList(target);
            }
        });
        </script>
        """
        
        return js_code

    def get_katex_header(self) -> str:
        """
        ========== 关键方法：KaTeX LaTeX渲染配置 ==========
        此方法生成KaTeX所需的CSS和JavaScript
        
        ⚠️ ModelScope环境优化：
        1. 使用国内可访问的CDN源
        2. 移除所有可能被CSP阻止的属性
        3. 使用完整的错误降级方案
        
        Returns:
            HTML string with KaTeX CDN links and auto-render configuration
        """
        
        # ========== 使用国内稳定CDN，完全兼容ModelScope ==========
        header = '''
        <!-- KaTeX CSS -->
        <link rel="stylesheet" href="https://lib.baomitu.com/KaTeX/0.16.9/katex.min.css">
        
        <script>
        // 初始化全局状态
        window.katexStatus = {
            loaded: false,
            autoRenderLoaded: false,
            initialized: false,
            renderCount: 0
        };
        </script>
        
        <!-- KaTeX 核心库 -->
        <script src="https://lib.baomitu.com/KaTeX/0.16.9/katex.min.js" onload="window.katexStatus.loaded = true; console.log('✅ KaTeX loaded from baomitu'); tryInitKaTeX();" onerror="loadKatexBackup();"></script>
        
        <!-- KaTeX Auto-render -->
        <script src="https://lib.baomitu.com/KaTeX/0.16.9/contrib/auto-render.min.js" onload="window.katexStatus.autoRenderLoaded = true; console.log('✅ auto-render loaded'); tryInitKaTeX();" onerror="loadAutoRenderBackup();"></script>
        
        <script>
        // 备用CDN加载函数
        function loadKatexBackup() {
            console.warn('⚠️ baomitu CDN失败，尝试unpkg...');
            var script = document.createElement('script');
            script.src = 'https://unpkg.com/katex@0.16.9/dist/katex.min.js';
            script.onload = function() {
                window.katexStatus.loaded = true;
                console.log('✅ KaTeX loaded from unpkg');
                tryInitKaTeX();
            };
            script.onerror = function() {
                console.error('❌ 所有KaTeX CDN均失败');
            };
            document.head.appendChild(script);
        }
        
        function loadAutoRenderBackup() {
            console.warn('⚠️ baomitu auto-render失败，尝试unpkg...');
            var script = document.createElement('script');
            script.src = 'https://unpkg.com/katex@0.16.9/dist/contrib/auto-render.min.js';
            script.onload = function() {
                window.katexStatus.autoRenderLoaded = true;
                console.log('✅ auto-render loaded from unpkg');
                tryInitKaTeX();
            };
            script.onerror = function() {
                console.error('❌ 所有auto-render CDN均失败');
            };
            document.head.appendChild(script);
        }
        
        // 尝试初始化KaTeX
        function tryInitKaTeX() {
            if (window.katexStatus.loaded && window.katexStatus.autoRenderLoaded && !window.katexStatus.initialized) {
                if (typeof window.katex !== 'undefined' && typeof renderMathInElement !== 'undefined') {
                    console.log('✅ 准备初始化KaTeX渲染系统');
                    window.katexStatus.initialized = true;
                    setTimeout(initKaTeXRendering, 100);
                } else {
                    console.warn('⚠️ 函数未定义，500ms后重试');
                    setTimeout(tryInitKaTeX, 500);
                }
            }
        }
        
        // 初始化KaTeX渲染系统
        function initKaTeXRendering() {
            console.log('🚀 启动KaTeX渲染引擎');
            
            // 立即渲染一次
            performRender();
            
            // 多次延迟渲染确保捕获动态内容
            var delays = [300, 800, 1500, 3000];
            delays.forEach(function(delay) {
                setTimeout(performRender, delay);
            });
            
            // 定期检查新内容
            setInterval(performRender, 3000);
            
            // 启动DOM观察器
            if (typeof MutationObserver !== 'undefined') {
                var debounce;
                var observer = new MutationObserver(function() {
                    clearTimeout(debounce);
                    debounce = setTimeout(performRender, 150);
                });
                
                setTimeout(function() {
                    if (document.body) {
                        observer.observe(document.body, {
                            childList: true,
                            subtree: true,
                            attributes: true,
                            attributeFilter: ['data-katex-render']
                        });
                        console.log('👁️ DOM观察器已启动');
                    }
                }, 800);
            }
        }
        
        // 执行LaTeX渲染
        function performRender() {
            if (typeof renderMathInElement === 'undefined') {
                return;
            }
            
            try {
                var targets = document.querySelectorAll('[data-katex-render="true"]');
                if (targets.length === 0) {
                    return;
                }
                
                var rendered = 0;
                console.log('🔍 发现 ' + targets.length + ' 个LaTeX容器');
                
                targets.forEach(function(elem) {
                    if (!elem || !elem.textContent) return;
                    
                    var hasFormula = elem.textContent.includes('$');
                    var alreadyRendered = elem.querySelector('.katex') !== null;
                    
                    if (hasFormula && !alreadyRendered) {
                        try {
                            renderMathInElement(elem, {
                                delimiters: [
                                    {left: '$$', right: '$$', display: true},
                                    {left: '$', right: '$', display: false}
                                ],
                                throwOnError: false,
                                errorColor: '#cc0000',
                                strict: false,
                                trust: true,
                                fleqn: false
                            });
                            
                            elem.setAttribute('data-katex-render', 'done');
                            rendered++;
                        } catch (e) {
                            console.error('❌ 渲染失败:', e.message);
                        }
                    }
                });
                
                if (rendered > 0) {
                    window.katexStatus.renderCount += rendered;
                    console.log('✨ 本次渲染 ' + rendered + ' 个容器 (总计: ' + window.katexStatus.renderCount + ')');
                }
            } catch (err) {
                console.error('❌ performRender错误:', err);
            }
        }
        
        // 页面加载完成后初始化
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', function() {
                setTimeout(tryInitKaTeX, 200);
            });
        } else {
            setTimeout(tryInitKaTeX, 200);
        }
        </script>
        
        <style>
        /* KaTeX样式优化 */
        .katex { font-size: 1.1em !important; }
        .katex-display { margin: 1em 0 !important; }
        .katex-error { color: #cc0000 !important; background: #fff3cd; padding: 2px 4px; border-radius: 3px; }
        </style>
        '''
        
        return header

    def inject_wysiwyg_controls(self) -> str:
        """
        Inject WYSIWYG editor control scripts.
        
        This is a placeholder for future rich text editing features.
        Currently returns empty script tags.
        
        Returns:
            HTML script tags for WYSIWYG controls
        """
        js_code = """
        <script>
        // 样本点击跳转处理函数
        window.handleSampleClick = function(sampleIndex) {
            console.log('Clicking sample:', sampleIndex);
            // 查找所有number类型输入框
            var allInputs = document.querySelectorAll('input[type="number"]');
            console.log('Total number inputs found:', allInputs.length);
            
            var targetInput = null;
            
            // 方法1: 查找值为-1的输入框（sample_click_index的初始值）
            for (var i = 0; i < allInputs.length; i++) {
                var inp = allInputs[i];
                console.log('Checking input', i, '- value:', inp.value, 'min:', inp.min, 'aria-label:', inp.getAttribute('aria-label'));
                
                // 查找最小值为-1的输入框（这是我们特意设置的）
                if (inp.min === '-1') {
                    targetInput = inp;
                    console.log('Found target input by min=-1');
                    break;
                }
            }
            
            if (targetInput) {
                console.log('Setting value to:', sampleIndex);
                targetInput.value = sampleIndex;
                targetInput.dispatchEvent(new Event('input', { bubbles: true }));
                targetInput.dispatchEvent(new Event('change', { bubbles: true }));
                targetInput.dispatchEvent(new Event('blur', { bubbles: true }));
                console.log('Events dispatched');
            } else {
                console.error('Target input with min=-1 not found!');
            }
        };
        </script>
        """
        
        return js_code
