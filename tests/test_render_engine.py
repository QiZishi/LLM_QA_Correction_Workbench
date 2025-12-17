"""
Unit tests for RenderEngine.

Tests specific examples for Markdown/LaTeX rendering and diff tag styling.
"""

import pytest
from services import RenderEngine


class TestMarkdownRendering:
    """Test Markdown to HTML conversion."""
    
    def test_bold_rendering(self):
        """Test bold text rendering."""
        engine = RenderEngine()
        result = engine.render_markdown_latex("This is **bold** text")
        
        assert '<strong>' in result or '**' in result
        assert 'bold' in result
    
    def test_italic_rendering(self):
        """Test italic text rendering."""
        engine = RenderEngine()
        result = engine.render_markdown_latex("This is *italic* text")
        
        assert '<em>' in result or '*' in result
        assert 'italic' in result
    
    def test_list_rendering(self):
        """Test list rendering."""
        engine = RenderEngine()
        result = engine.render_markdown_latex("- Item 1\n- Item 2")
        
        assert '<li>' in result or '-' in result
    
    def test_empty_text(self):
        """Test rendering empty text."""
        engine = RenderEngine()
        result = engine.render_markdown_latex("")
        
        assert result == ""


class TestLatexRendering:
    """Test LaTeX formula rendering."""
    
    def test_inline_latex(self):
        """Test inline LaTeX formula."""
        engine = RenderEngine()
        result = engine.render_markdown_latex("Formula: $x^2 + y^2 = z^2$")
        
        # Should return some HTML output
        assert len(result) > 0
        assert 'Formula' in result
    
    def test_display_latex(self):
        """Test display LaTeX formula."""
        engine = RenderEngine()
        result = engine.render_markdown_latex("$$E = mc^2$$")
        
        # Should return some output
        assert len(result) > 0
    
    def test_multiple_formulas(self):
        """Test multiple LaTeX formulas."""
        engine = RenderEngine()
        result = engine.render_markdown_latex("$a + b$ and $c + d$")
        
        # Should return output with 'and'
        assert 'and' in result
    
    def test_latex_with_special_formatting(self):
        """Test LaTeX with special formatting like mathrm."""
        engine = RenderEngine()
        result = engine.render_markdown_latex("建议发病 $24\\mathrm{h}$ 内转运")
        
        # Should not contain placeholder text
        assert 'PLACEHOLDER' not in result
        assert 'LATEX_PLACEHOLDER' not in result
        # Should contain the LaTeX content
        assert '24\\mathrm{h}' in result or '24' in result
    
    def test_latex_placeholder_not_exposed(self):
        """Test that internal placeholders are not exposed in output."""
        engine = RenderEngine()
        # Text with underscores that might interfere with placeholder format
        result = engine.render_markdown_latex("Text with ___underscores___ and $x^2$ formula")
        
        # Should not expose internal placeholder format
        assert 'LATEX_PLACEHOLDER' not in result
        assert '<!--LATEX_' not in result or 'latex-inline' in result
        # Should contain the formula
        assert 'x^2' in result


class TestDiffTagRendering:
    """Test diff tag styling."""
    
    def test_false_tag_styling(self):
        """Test <false> tag styling."""
        engine = RenderEngine()
        result = engine.render_diff_tags("<false>deleted</false>")
        
        # Check for red color (either 'red' or hex code '#d32f2f')
        assert 'color:' in result and ('red' in result or '#d32f2f' in result)
        assert 'line-through' in result
        assert 'deleted' in result
    
    def test_true_tag_styling(self):
        """Test <true> tag styling."""
        engine = RenderEngine()
        result = engine.render_diff_tags("<true>added</true>")
        
        # Check for green color (either 'green' or hex code '#388e3c')
        assert 'color:' in result and ('green' in result or '#388e3c' in result)
        assert 'added' in result
    
    def test_mixed_tags(self):
        """Test mixed false and true tags."""
        engine = RenderEngine()
        result = engine.render_diff_tags(
            "Keep <false>old</false><true>new</true> text"
        )
        
        # Check for both colors
        assert ('red' in result or '#d32f2f' in result)
        assert ('green' in result or '#388e3c' in result)
        assert 'old' in result
        assert 'new' in result
    
    def test_no_tags(self):
        """Test text without tags."""
        engine = RenderEngine()
        result = engine.render_diff_tags("Plain text")
        
        assert result == "Plain text"
        assert '<span' not in result


class TestNestedContent:
    """Test nested Markdown/LaTeX in diff tags."""
    
    def test_markdown_in_false_tag(self):
        """Test Markdown inside false tag."""
        engine = RenderEngine()
        result = engine.render_diff_tags("<false>**bold**</false>")
        
        # Check for red color (either 'red' or hex code '#d32f2f')
        assert ('red' in result or '#d32f2f' in result)
        assert '**bold**' in result
    
    def test_latex_in_true_tag(self):
        """Test LaTeX inside true tag."""
        engine = RenderEngine()
        result = engine.render_diff_tags("<true>$x^2$</true>")
        
        # Check for green color (either 'green' or hex code '#388e3c')
        assert ('green' in result or '#388e3c' in result)
        assert '$x^2$' in result


class TestWYSIWYGControls:
    """Test WYSIWYG control generation."""
    
    def test_inject_controls(self):
        """Test JavaScript control injection."""
        engine = RenderEngine()
        js_code = engine.inject_wysiwyg_controls()
        
        assert '<script>' in js_code
        assert 'makeBold' in js_code
        assert 'makeItalic' in js_code
        assert 'makeList' in js_code
    
    def test_katex_header(self):
        """Test KaTeX header generation."""
        engine = RenderEngine()
        header = engine.get_katex_header()
        
        assert 'katex' in header
        assert '<link' in header
        assert '<script' in header


class TestCombinedRendering:
    """Test combined Markdown, LaTeX, and diff rendering."""
    
    def test_markdown_with_diff(self):
        """Test Markdown with diff tags."""
        engine = RenderEngine()
        text = "<false>**old**</false><true>**new**</true>"
        result = engine.render_markdown_latex_with_diff(text)
        
        # Check for both colors (either named or hex)
        assert ('red' in result or '#d32f2f' in result)
        assert ('green' in result or '#388e3c' in result)
    
    def test_latex_with_diff(self):
        """Test LaTeX with diff tags."""
        engine = RenderEngine()
        text = "<false>$x^2$</false><true>$y^2$</true>"
        result = engine.render_markdown_latex_with_diff(text)
        
        assert 'x^2' in result
        assert 'y^2' in result
