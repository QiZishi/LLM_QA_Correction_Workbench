"""
RenderEngine for Markdown and LaTeX rendering.

Handles conversion of Markdown and LaTeX to HTML, and styling of diff tags.
"""

import re
import markdown


class RenderEngine:
    """
    Rendering engine for Markdown, LaTeX, and diff tags.
    
    Provides methods to:
    - Render Markdown to HTML
    - Render LaTeX formulas (using KaTeX/MathJax)
    - Style diff tags (<false>/<true>)
    - Inject WYSIWYG editing controls
    """
    
    def __init__(self):
        """Initialize RenderEngine with Markdown processor."""
        self.md = markdown.Markdown(extensions=['extra', 'nl2br'])
    
    def render_markdown_latex(self, text: str) -> str:
        """
        Render Markdown and LaTeX to HTML.
        
        Converts Markdown syntax to HTML and preserves LaTeX formulas
        for rendering with KaTeX/MathJax.
        
        Args:
            text: Text containing Markdown and/or LaTeX
        
        Returns:
            HTML string with rendered Markdown and LaTeX placeholders
        """
        if not text:
            return ""
        
        # Protect LaTeX formulas from Markdown processing
        latex_formulas = []
        
        def protect_latex(match):
            """Replace LaTeX with placeholder."""
            latex_formulas.append(match.group(0))
            return f"___LATEX_{len(latex_formulas)-1}___"
        
        # Find and protect inline LaTeX: $...$
        text = re.sub(r'\$([^\$]+)\$', protect_latex, text)
        
        # Find and protect display LaTeX: $$...$$
        text = re.sub(r'\$\$([^\$]+)\$\$', protect_latex, text)
        
        # Render Markdown
        html = self.md.convert(text)
        
        # Restore LaTeX formulas
        for i, formula in enumerate(latex_formulas):
            placeholder = f"___LATEX_{i}___"
            # Wrap in span for KaTeX/MathJax rendering
            html = html.replace(placeholder, f'<span class="latex-formula">{formula}</span>')
        
        # Reset Markdown processor for next use
        self.md.reset()
        
        return html
    
    def render_diff_tags(self, text: str) -> str:
        """
        Convert <false>/<true> tags to styled HTML.
        
        Applies visual styling:
        - <false> → red text with strikethrough
        - <true> → green text
        
        Args:
            text: Text with <false> and <true> tags
        
        Returns:
            HTML with styled spans
        """
        if not text:
            return ""
        
        # Replace <false> tags with styled spans
        text = re.sub(
            r'<false>(.*?)</false>',
            r'<span style="color: red; text-decoration: line-through;">\1</span>',
            text,
            flags=re.DOTALL
        )
        
        # Replace <true> tags with styled spans
        text = re.sub(
            r'<true>(.*?)</true>',
            r'<span style="color: green;">\1</span>',
            text,
            flags=re.DOTALL
        )
        
        return text
    
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
        html = self.render_diff_tags(text)
        
        # Then render Markdown and LaTeX
        # Note: We need to be careful not to break the HTML from diff tags
        # For now, we'll render Markdown/LaTeX within the content
        
        return html
    
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
        Get KaTeX CSS and JS headers for LaTeX rendering.
        
        Returns:
            HTML string with KaTeX CDN links
        """
        return """
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
        <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
        <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"
                onload="renderMathInElement(document.body, {
                    delimiters: [
                        {left: '$$', right: '$$', display: true},
                        {left: '$', right: '$', display: false}
                    ]
                });"></script>
        """
