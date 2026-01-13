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
        
        ⚠️ 重要注意事项：
        1. 使用onload回调确保加载顺序正确
        2. 使用cdnjs.cloudflare.com作为主CDN（更稳定）
        3. 添加错误处理和回退机制
        4. renderAllMath函数通过data-katex-render属性查找需要渲染的元素
        
        Returns:
            HTML string with KaTeX CDN links and auto-render configuration
        """
        import time
        import random
        # 添加随机数+时间戳来强制浏览器每次都重新加载
        cache_buster = str(int(time.time() * 1000)) + str(random.randint(1000, 9999))
        
        # ========== 使用稳定的CDN，移除可能导致加载失败的属性 ==========
        # 不使用 defer/integrity，确保脚本按顺序同步加载
        header = '''
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css" crossorigin="anonymous">
        <script>
        // 全局变量用于跟踪加载状态
        window.katexLoaded = false;
        window.autoRenderLoaded = false;
        window.katexRetryCount = 0;
        </script>
        <script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js" crossorigin="anonymous" onload="window.katexLoaded = true; console.log('✅ KaTeX 核心已加载'); checkAndInit();" onerror="console.error('❌ KaTeX 核心加载失败'); loadKatexFallback();"></script>
        <script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js" crossorigin="anonymous" onload="window.autoRenderLoaded = true; console.log('✅ KaTeX auto-render 已加载'); checkAndInit();" onerror="console.error('❌ auto-render 加载失败'); loadAutoRenderFallback();"></script>
        <script>
        /* ========== 备用CDN加载 ========== */
        function loadKatexFallback() {
            if (window.katexRetryCount < 1) {
                window.katexRetryCount++;
                console.log('🔄 尝试备用CDN（cdnjs）...');
                var script = document.createElement('script');
                script.src = 'https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.9/katex.min.js';
                script.onload = function() {
                    window.katexLoaded = true;
                    console.log('✅ KaTeX 从备用CDN加载成功');
                    checkAndInit();
                };
                script.onerror = function() {
                    console.error('❌ 备用CDN也失败');
                };
                document.head.appendChild(script);
            }
        }
        
        function loadAutoRenderFallback() {
            if (window.katexRetryCount < 1) {
                window.katexRetryCount++;
                console.log('🔄 尝试备用CDN（cdnjs）...');
                var script = document.createElement('script');
                script.src = 'https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.9/contrib/auto-render.min.js';
                script.onload = function() {
                    window.autoRenderLoaded = true;
                    console.log('✅ auto-render 从备用CDN加载成功');
                    checkAndInit();
                };
                script.onerror = function() {
                    console.error('❌ 备用CDN也失败');
                };
                document.head.appendChild(script);
            }
        }
        
        function checkAndInit() {
            if (window.katexLoaded && window.autoRenderLoaded && typeof renderMathInElement !== 'undefined') {
                console.log('✅ 所有库已加载，开始初始化');
                initKaTeX();
            } else {
                console.log('⏳ 等待所有库加载... katex:', window.katexLoaded, 'autoRender:', window.autoRenderLoaded, 'renderMathInElement:', typeof renderMathInElement !== 'undefined');
            }
        }
        </script>
        <script>
        /* ========== 关键函数：初始化KaTeX渲染 ========== */
        function initKaTeX() {
            console.log("🚀 初始化KaTeX渲染系统");
            
            // 检查是否已初始化
            if (window.katexInitialized) {
                console.log("⚠️ KaTeX已初始化，跳过");
                return;
            }
            
            // 确保库已加载
            if (typeof window.katex === 'undefined' || typeof renderMathInElement === 'undefined') {
                console.error("❌ KaTeX库未完全加载");
                console.log("  katex:", typeof window.katex);
                console.log("  renderMathInElement:", typeof renderMathInElement);
                // 1秒后重试
                setTimeout(function() {
                    if (typeof renderMathInElement !== 'undefined') {
                        initKaTeX();
                    }
                }, 1000);
                return;
            }
            
            console.log("✅ KaTeX库已完全加载，开始初始化渲染");
            window.katexInitialized = true;
            
            // 立即渲染一次
            renderAllMath();
            
            // 多次渲染确保捕获动态内容
            setTimeout(renderAllMath, 200);
            setTimeout(renderAllMath, 500);
            setTimeout(renderAllMath, 1000);
            setTimeout(renderAllMath, 2000);
            
            // 定期检查
            setInterval(renderAllMath, 2000);
            
            // 启动DOM监听
            startDOMObserver();
        }
        
        /* ========== DOM变化监听 ========== */
        function startDOMObserver() {
            if (typeof MutationObserver === 'undefined') {
                console.warn("⚠️ MutationObserver不可用");
                return;
            }
            
            if (window.katexObserverStarted) {
                return; // 避免重复启动
            }
            
            window.katexObserverStarted = true;
            
            var debounceTimer;
            const observer = new MutationObserver(function(mutations) {
                // 防抖：避免过于频繁触发
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(renderAllMath, 100);
            });
            
            // 延迟启动observer确保body存在
            setTimeout(function() {
                if (document.body) {
                    observer.observe(document.body, {
                        childList: true,
                        subtree: true,
                        attributes: true,
                        attributeFilter: ['data-katex-render']
                    });
                    console.log("👁️ DOM监听已启动");
                }
            }, 500);
        }
        
        /* ========== 多种加载事件监听 ========== */
        if (document.readyState === 'loading') {
            document.addEventListener("DOMContentLoaded", function() {
                console.log("� DOMContentLoaded triggered");
                setTimeout(function() {
                    if (window.autoRenderLoaded) {
                        renderAllMath();
                    }
                }, 100);
            });
        } else {
            console.log("📄 Document already loaded");
        }
        
        window.addEventListener('load', function() {
            console.log("🌐 Window loaded");
            setTimeout(function() {
                if (window.autoRenderLoaded) {
                    renderAllMath();
                }
            }, 100);
        });
        
        /* ========== 关键函数：渲染所有LaTeX公式 ========== */
        /* ⚠️ 重要配置说明：
         * 1. 查找所有data-katex-render="true"的元素
         * 2. 使用KaTeX auto-render渲染其中的$...$和$$...$$
         * 3. 渲染完成后标记为data-katex-render="done"避免重复
         * 4. 不要修改delimiters配置（$和$$是标准LaTeX语法）
         */
        function renderAllMath() {
            if (typeof renderMathInElement === 'undefined') {
                return; // 静默失败，避免刷屏
            }
            
            try {
                // 查找所有标记为需要渲染的容器
                const targets = document.querySelectorAll('[data-katex-render="true"]');
                
                if (targets.length === 0) {
                    return; // 没有目标就不输出日志
                }
                
                let renderedCount = 0;
                console.log("🔍 找到 " + targets.length + " 个待渲染容器");
                
                targets.forEach(function(elem) {
                    if (!elem || !elem.textContent) {
                        return; // 跳过空元素
                    }
                    
                    const hasLaTeX = elem.textContent.includes('$');
                    const alreadyRendered = elem.querySelector('.katex') !== null;
                    
                    console.log("  📋 容器状态: LaTeX=" + hasLaTeX + ", 已渲染=" + alreadyRendered);
                    
                    if (hasLaTeX && !alreadyRendered) {
                        console.log("  ▶️ 开始渲染:", elem.textContent.substring(0, 50) + "...");
                        
                        try {
                            renderMathInElement(elem, {
                                delimiters: [
                                    {left: '$$', right: '$$', display: true},
                                    {left: '$', right: '$', display: false}
                                ],
                                throwOnError: false,
                                errorColor: '#cc0000',
                                strict: false,
                                trust: true
                            });
                            
                            // 检查渲染结果
                            const katexCount = elem.querySelectorAll('.katex').length;
                            console.log("  ✅ 渲染完成，生成 " + katexCount + " 个.katex元素");
                            
                            // 标记已渲染
                            elem.setAttribute('data-katex-render', 'done');
                            renderedCount++;
                        } catch (renderError) {
                            console.error("  ❌ 渲染失败:", renderError);
                        }
                    }
                });
                
                if (renderedCount > 0) {
                    console.log("✨ 本次成功渲染 " + renderedCount + " 个容器");
                }
            } catch (e) {
                console.error('❌ renderAllMath错误:', e);
            }
        }
        
        function checkRenderFailures() {
            // 查找所有带有 data-fallback 的元素
            document.querySelectorAll('[data-fallback]').forEach(function(el) {
                // 检查是否包含 KaTeX 错误或未渲染
                var hasError = el.querySelector('.katex-error');
                var hasKatex = el.querySelector('.katex');
                var text = el.textContent || el.innerText;
                
                // 如果有错误，或者没有成功渲染（仍然包含$符号），显示原文
                if (hasError || (!hasKatex && (text.includes('$') || text.includes('\\\\')))) {
                    var fallback = el.getAttribute('data-fallback');
                    if (fallback) {
                        // 解码HTML实体
                        var decoded = fallback.replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&').replace(/&quot;/g, '"');
                        el.innerHTML = '<code style="background: #f5f5f5; padding: 2px 6px; border-radius: 3px; font-family: monospace;">' + decoded + '</code>';
                        el.removeAttribute('data-fallback');
                    }
                }
            });
        }
        
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
        <style>
        /* LaTeX 公式样式 */
        .latex-display {
            display: block;
            text-align: center;
            margin: 15px 0;
            font-size: 18px;
        }
        .latex-inline {
            display: inline;
            font-size: 18px;
        }
        .katex {
            font-size: 1.1em !important;
        }
        .katex-display {
            margin: 15px 0 !important;
        }
        /* 渲染失败时的样式 */
        .katex-error {
            color: inherit !important;
            background: #f5f5f5;
            padding: 2px 6px;
            border-radius: 3px;
        }
        </style>
        '''
        
        return header
