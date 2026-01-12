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
        
        Optimized Algorithm:
        - Uses intelligent tokenization for better semantic boundaries
        - Merges consecutive tags to reduce fragmentation
        - Handles whitespace intelligently to avoid noise
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
        
        # Split into semantic tokens for better comparison
        original_tokens = self._smart_tokenize(original)
        modified_tokens = self._smart_tokenize(modified)
        
        # Use SequenceMatcher for comparison
        matcher = difflib.SequenceMatcher(None, original_tokens, modified_tokens)
        
        # Build result with tags
        result_parts = []
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                # Unchanged content
                result_parts.append(''.join(original_tokens[i1:i2]))
            elif tag == 'delete':
                # Deleted content
                deleted_text = ''.join(original_tokens[i1:i2])
                result_parts.append(('false', deleted_text))
            elif tag == 'insert':
                # Added content
                inserted_text = ''.join(modified_tokens[j1:j2])
                result_parts.append(('true', inserted_text))
            elif tag == 'replace':
                # Replaced content (delete + insert)
                deleted_text = ''.join(original_tokens[i1:i2])
                inserted_text = ''.join(modified_tokens[j1:j2])
                result_parts.append(('false', deleted_text))
                result_parts.append(('true', inserted_text))
        
        # Merge consecutive tags and build final result
        result = self._merge_and_build_result(result_parts)
        
        # Validate and fix tags
        result = self._validate_and_fix_tags(result)
        
        return result
    
    def _smart_tokenize(self, text: str) -> List[str]:
        """
        智能分词，保持语义边界完整。
        
        改进策略：
        1. 中文字符单独成词
        2. 英文单词保持完整（包括连字符）
        3. 数字和单位保持在一起
        4. 标点符号单独处理
        5. LaTeX公式保持完整
        6. 空格作为独立token但可以被智能合并
        
        Args:
            text: Text to tokenize
        
        Returns:
            List of semantic tokens
        """
        tokens = []
        i = 0
        n = len(text)
        
        while i < n:
            # 处理LaTeX公式（$...$或$$...$$）
            if text[i] == '$':
                if i + 1 < n and text[i + 1] == '$':
                    # 双$公式
                    end = text.find('$$', i + 2)
                    if end != -1:
                        tokens.append(text[i:end + 2])
                        i = end + 2
                        continue
                else:
                    # 单$公式
                    end = text.find('$', i + 1)
                    if end != -1:
                        tokens.append(text[i:end + 1])
                        i = end + 1
                        continue
            
            # 处理中文字符（单字成词）
            if '\u4e00' <= text[i] <= '\u9fff':
                tokens.append(text[i])
                i += 1
                continue
            
            # 处理英文单词（包括连字符和撇号）
            if text[i].isalpha():
                j = i
                while j < n and (text[j].isalnum() or text[j] in "-'"):
                    j += 1
                tokens.append(text[i:j])
                i = j
                continue
            
            # 处理数字（包括小数点）
            if text[i].isdigit():
                j = i
                while j < n and (text[j].isdigit() or text[j] == '.'):
                    j += 1
                # 检查是否有单位紧跟
                if j < n and text[j].isalpha():
                    while j < n and text[j].isalpha():
                        j += 1
                tokens.append(text[i:j])
                i = j
                continue
            
            # 处理空格（连续空格作为一个token）
            if text[i].isspace():
                j = i
                while j < n and text[j].isspace():
                    j += 1
                tokens.append(text[i:j])
                i = j
                continue
            
            # 处理标点和其他字符
            tokens.append(text[i])
            i += 1
        
        return tokens
    
    def _merge_and_build_result(self, parts: List) -> str:
        """
        合并连续的相同类型标签，减少碎片化。
        
        优化策略：
        1. 合并连续的<false>标签
        2. 合并连续的<true>标签
        3. 清理不必要的空格差异
        4. 优化标签边界
        
        Args:
            parts: List of tuples (tag_type, content) or strings
        
        Returns:
            Final result string with optimized tags
        """
        if not parts:
            return ""
        
        merged = []
        current_tag = None
        current_content = []
        
        for part in parts:
            if isinstance(part, tuple):
                tag_type, content = part
                
                # 跳过仅包含空格的差异（通常不重要）
                if content.strip() == '':
                    # 如果是纯空格，保留但不标记
                    if current_tag:
                        merged.append((current_tag, ''.join(current_content)))
                        current_tag = None
                        current_content = []
                    merged.append(content)
                    continue
                
                # 合并相同类型的连续标签
                if tag_type == current_tag:
                    current_content.append(content)
                else:
                    # 输出之前累积的内容
                    if current_tag:
                        merged.append((current_tag, ''.join(current_content)))
                    # 开始新的标签
                    current_tag = tag_type
                    current_content = [content]
            else:
                # 普通字符串（未改变的内容）
                if current_tag:
                    merged.append((current_tag, ''.join(current_content)))
                    current_tag = None
                    current_content = []
                merged.append(part)
        
        # 输出最后累积的内容
        if current_tag:
            merged.append((current_tag, ''.join(current_content)))
        
        # 构建最终结果
        result_parts = []
        for item in merged:
            if isinstance(item, tuple):
                tag_type, content = item
                result_parts.append(f"<{tag_type}>{content}</{tag_type}>")
            else:
                result_parts.append(item)
        
        return ''.join(result_parts)
    
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
