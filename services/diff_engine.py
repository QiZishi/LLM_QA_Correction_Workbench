"""
DiffEngine for text comparison and difference marking.

Implements text diff algorithm to generate <false>/<true> tags for
deleted and added content.
"""

import difflib
import re
from typing import List, Tuple
from utils.performance import monitor_performance


class DiffEngine:
    """
    Text difference engine for comparing original and modified text.
    
    Uses word-level comparison to generate human-readable diffs with
    <false> tags for deletions and <true> tags for additions.
    """
    
    def __init__(self):
        """Initialize DiffEngine."""
        pass
    
    @monitor_performance("compute_diff")
    def compute_diff(self, original: str, modified: str) -> str:
        """
        Compare two texts and return result with diff tags.
        
        Algorithm:
        - Uses difflib.SequenceMatcher for word-level comparison
        - Deleted content wrapped in <false>...</false>
        - Added content wrapped in <true>...</true>
        - Unchanged content preserved as-is
        
        Args:
            original: Original text
            modified: Modified text
        
        Returns:
            Text with <false> and <true> tags marking differences
        
        Raises:
            ValueError: If text is too long (> 100K characters)
            TimeoutError: If computation takes too long
        """
        # Validate input lengths
        if len(original) > 100000 or len(modified) > 100000:
            raise ValueError("文本过长，请分段处理（最大 100,000 字符）")
        
        # Handle empty strings
        if not original and not modified:
            return ""
        if not original and modified:
            return f"<true>{modified}</true>"
        if original and not modified:
            return f"<false>{original}</false>"
        
        # Split into words for word-level comparison
        original_words = self._split_into_words(original)
        modified_words = self._split_into_words(modified)
        
        # Use SequenceMatcher for comparison
        matcher = difflib.SequenceMatcher(None, original_words, modified_words)
        
        # Build result with tags
        result_parts = []
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                # Unchanged content
                result_parts.append(''.join(original_words[i1:i2]))
            elif tag == 'delete':
                # Deleted content
                deleted_text = ''.join(original_words[i1:i2])
                result_parts.append(f"<false>{deleted_text}</false>")
            elif tag == 'insert':
                # Added content
                inserted_text = ''.join(modified_words[j1:j2])
                result_parts.append(f"<true>{inserted_text}</true>")
            elif tag == 'replace':
                # Replaced content (delete + insert)
                deleted_text = ''.join(original_words[i1:i2])
                inserted_text = ''.join(modified_words[j1:j2])
                result_parts.append(f"<false>{deleted_text}</false><true>{inserted_text}</true>")
        
        result = ''.join(result_parts)
        
        # Validate and fix tags
        result = self._validate_and_fix_tags(result)
        
        return result
    
    def _split_into_words(self, text: str) -> List[str]:
        """
        Split text into words while preserving whitespace and punctuation.
        
        This ensures better readability in diffs by keeping word boundaries.
        
        Args:
            text: Text to split
        
        Returns:
            List of words with attached whitespace/punctuation
        """
        # Split on word boundaries but keep delimiters
        # Pattern: match word characters or non-word characters
        pattern = r'(\w+|\W+)'
        words = re.findall(pattern, text)
        return words
    
    def validate_tags(self, text: str) -> bool:
        """
        Validate that all <false> and <true> tags are properly closed.
        
        Args:
            text: Text to validate
        
        Returns:
            True if all tags are properly closed, False otherwise
        """
        # Count opening and closing tags
        false_open = text.count('<false>')
        false_close = text.count('</false>')
        true_open = text.count('<true>')
        true_close = text.count('</true>')
        
        return (false_open == false_close) and (true_open == true_close)
    
    def _validate_and_fix_tags(self, text: str) -> str:
        """
        Validate and auto-fix malformed tags.
        
        Args:
            text: Text with potential malformed tags
        
        Returns:
            Text with fixed tags
        """
        if self.validate_tags(text):
            return text
        
        # Simple fix: ensure tags are balanced
        # Count tags
        false_open = text.count('<false>')
        false_close = text.count('</false>')
        true_open = text.count('<true>')
        true_close = text.count('</true>')
        
        # Add missing closing tags at the end
        if false_open > false_close:
            text += '</false>' * (false_open - false_close)
        if true_open > true_close:
            text += '</true>' * (true_open - true_close)
        
        return text
    
    def strip_tags(self, text: str) -> str:
        """
        Remove all <false> and <true> tags from text.
        
        Args:
            text: Text with tags
        
        Returns:
            Plain text without tags
        """
        # Remove false tags
        text = re.sub(r'<false>(.*?)</false>', r'\1', text)
        # Remove true tags
        text = re.sub(r'<true>(.*?)</true>', r'\1', text)
        # Remove any remaining unclosed tags
        text = re.sub(r'</?false>', '', text)
        text = re.sub(r'</?true>', '', text)
        
        return text
