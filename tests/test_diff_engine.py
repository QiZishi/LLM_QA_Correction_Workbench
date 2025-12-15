"""
Unit tests for DiffEngine.

Tests specific examples, edge cases, and error conditions.
"""

import pytest
from services import DiffEngine


class TestDiffEngineBasic:
    """Test basic diff functionality."""
    
    def test_identical_text(self):
        """Test diff of identical text."""
        engine = DiffEngine()
        result = engine.compute_diff("Hello world", "Hello world")
        
        assert result == "Hello world"
        assert '<false>' not in result
        assert '<true>' not in result
    
    def test_simple_deletion(self):
        """Test simple deletion."""
        engine = DiffEngine()
        result = engine.compute_diff("Hello world", "Hello")
        
        assert '<false>' in result
        assert 'world' in result
    
    def test_simple_addition(self):
        """Test simple addition."""
        engine = DiffEngine()
        result = engine.compute_diff("Hello", "Hello world")
        
        assert '<true>' in result
        assert 'world' in result
    
    def test_replacement(self):
        """Test text replacement."""
        engine = DiffEngine()
        result = engine.compute_diff("Hello world", "Hello universe")
        
        assert '<false>' in result
        assert '<true>' in result
        assert 'world' in result
        assert 'universe' in result


class TestDiffEngineEdgeCases:
    """Test edge cases."""
    
    def test_empty_strings(self):
        """Test with empty strings."""
        engine = DiffEngine()
        
        # Both empty
        assert engine.compute_diff("", "") == ""
        
        # Original empty
        result = engine.compute_diff("", "Hello")
        assert result == "<true>Hello</true>"
        
        # Modified empty
        result = engine.compute_diff("Hello", "")
        assert result == "<false>Hello</false>"
    
    def test_whitespace_only(self):
        """Test with whitespace."""
        engine = DiffEngine()
        result = engine.compute_diff("   ", "   ")
        
        assert result == "   "
    
    def test_long_text_error(self):
        """Test error handling for very long text."""
        engine = DiffEngine()
        long_text = "a" * 100001
        
        with pytest.raises(ValueError, match="文本过长"):
            engine.compute_diff(long_text, "short")
    
    def test_markdown_preservation(self):
        """Test that Markdown syntax is preserved."""
        engine = DiffEngine()
        original = "This is **bold** text"
        modified = "This is **bold** and *italic* text"
        
        result = engine.compute_diff(original, modified)
        
        # Markdown markers should be preserved
        assert '**bold**' in result
        assert '*italic*' in result
    
    def test_latex_preservation(self):
        """Test that LaTeX syntax is preserved."""
        engine = DiffEngine()
        original = "The formula is $x^2 + y^2 = z^2$"
        modified = "The formula is $x^2 + y^2 = z^2$ and $E = mc^2$"
        
        result = engine.compute_diff(original, modified)
        
        # LaTeX content should be preserved (may have tags around parts)
        assert 'x^2' in result
        assert 'y^2' in result
        assert 'z^2' in result
        assert 'E = mc^2' in result
        assert engine.validate_tags(result)


class TestTagValidation:
    """Test tag validation functionality."""
    
    def test_validate_balanced_tags(self):
        """Test validation of balanced tags."""
        engine = DiffEngine()
        
        # Balanced tags
        assert engine.validate_tags("<false>deleted</false><true>added</true>")
        assert engine.validate_tags("no tags here")
        assert engine.validate_tags("")
    
    def test_validate_unbalanced_tags(self):
        """Test validation of unbalanced tags."""
        engine = DiffEngine()
        
        # Unbalanced tags
        assert not engine.validate_tags("<false>deleted")
        assert not engine.validate_tags("<true>added")
        assert not engine.validate_tags("<false>deleted</false><true>added")
    
    def test_auto_fix_tags(self):
        """Test automatic tag fixing."""
        engine = DiffEngine()
        
        # The _validate_and_fix_tags method should fix unbalanced tags
        fixed = engine._validate_and_fix_tags("<false>deleted<true>added</true>")
        assert engine.validate_tags(fixed)


class TestStripTags:
    """Test tag stripping functionality."""
    
    def test_strip_false_tags(self):
        """Test stripping false tags."""
        engine = DiffEngine()
        result = engine.strip_tags("<false>deleted</false> text")
        
        assert result == "deleted text"
        assert '<false>' not in result
    
    def test_strip_true_tags(self):
        """Test stripping true tags."""
        engine = DiffEngine()
        result = engine.strip_tags("text <true>added</true>")
        
        assert result == "text added"
        assert '<true>' not in result
    
    def test_strip_mixed_tags(self):
        """Test stripping mixed tags."""
        engine = DiffEngine()
        result = engine.strip_tags(
            "<false>old</false> middle <true>new</true>"
        )
        
        assert result == "old middle new"
        assert '<false>' not in result
        assert '<true>' not in result
    
    def test_strip_nested_content(self):
        """Test stripping tags with nested content."""
        engine = DiffEngine()
        result = engine.strip_tags(
            "<false>This is **bold** text</false>"
        )
        
        # Markdown should be preserved
        assert result == "This is **bold** text"
        assert '**bold**' in result


class TestWordLevelDiff:
    """Test word-level diff behavior."""
    
    def test_word_boundary_preservation(self):
        """Test that word boundaries are preserved."""
        engine = DiffEngine()
        result = engine.compute_diff(
            "The quick brown fox",
            "The fast brown fox"
        )
        
        # Should detect word-level change
        assert 'quick' in result or 'fast' in result
    
    def test_punctuation_handling(self):
        """Test handling of punctuation."""
        engine = DiffEngine()
        result = engine.compute_diff(
            "Hello, world!",
            "Hello world"
        )
        
        # Punctuation changes should be detected
        assert engine.validate_tags(result)
    
    def test_multiline_text(self):
        """Test handling of multiline text."""
        engine = DiffEngine()
        original = "Line 1\nLine 2\nLine 3"
        modified = "Line 1\nModified Line 2\nLine 3"
        
        result = engine.compute_diff(original, modified)
        
        # Should handle newlines correctly
        assert '\n' in result
        assert engine.validate_tags(result)


class TestChineseText:
    """Test handling of Chinese text."""
    
    def test_chinese_diff(self):
        """Test diff with Chinese characters."""
        engine = DiffEngine()
        result = engine.compute_diff(
            "这是原始文本",
            "这是修改后的文本"
        )
        
        # Should handle Chinese characters
        assert '原始' in result or '修改后的' in result
        assert engine.validate_tags(result)
    
    def test_mixed_language(self):
        """Test diff with mixed Chinese and English."""
        engine = DiffEngine()
        result = engine.compute_diff(
            "这是 English 文本",
            "这是 Modified English 文本"
        )
        
        assert engine.validate_tags(result)
