"""
ExportManager for JSON data export.

Handles conversion of corrected samples to various JSON formats and file generation.
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Any
from models import Sample


class ExportManager:
    """
    Manages export of corrected samples to JSON files.
    
    Supports multiple export formats:
    - messages: OpenAI-style messages format (default)
    - alpaca: Alpaca instruction format
    - sharegpt: ShareGPT conversation format
    - query-response: Simple query-response pairs
    """
    
    def __init__(self, format: str = "messages"):
        """
        Initialize ExportManager.
        
        Args:
            format: Export format (messages/alpaca/sharegpt/query-response)
        
        Raises:
            ValueError: If format is not supported
        """
        valid_formats = ["messages", "alpaca", "sharegpt", "query-response"]
        if format not in valid_formats:
            raise ValueError(
                f"Invalid format: {format}. Must be one of {valid_formats}"
            )
        
        self.format = format
        self.corrected_samples: List[Sample] = []
    
    def add_sample(self, sample: Sample):
        """
        Add a corrected sample to the export queue.
        
        Args:
            sample: Sample object to add
        
        Raises:
            ValueError: If sample status is not 'corrected'
        """
        if sample.status != "corrected":
            raise ValueError(
                f"Only corrected samples can be exported. "
                f"Sample {sample.id} has status: {sample.status}"
            )
        
        self.corrected_samples.append(sample)
    
    def export_to_json(self, original_filename: str) -> str:
        """
        Generate JSON export file.
        
        Args:
            original_filename: Original CSV filename (without extension)
        
        Returns:
            Path to generated JSON file
        
        Raises:
            ValueError: If no corrected samples to export
            PermissionError: If cannot write to file
        """
        if not self.corrected_samples:
            raise ValueError("没有已校正的样本可导出")
        
        # Generate filename: {original_name}_{timestamp}_{count}.json
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        count = len(self.corrected_samples)
        
        # Remove extension from original filename if present
        base_name = os.path.splitext(original_filename)[0]
        output_filename = f"{base_name}_{timestamp}_{count}.json"
        
        # Convert samples to selected format
        data = []
        for sample in self.corrected_samples:
            if self.format == "messages":
                data.append(self.format_messages(sample))
            elif self.format == "alpaca":
                data.append(self.format_alpaca(sample))
            elif self.format == "sharegpt":
                data.append(self.format_sharegpt(sample))
            elif self.format == "query-response":
                data.append(self.format_query_response(sample))
        
        # Write to file
        try:
            with open(output_filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except PermissionError:
            raise PermissionError(f"无法写入文件: {output_filename}")
        except Exception as e:
            raise ValueError(f"数据序列化失败: {str(e)}")
        
        return output_filename
    
    def format_messages(self, sample: Sample) -> Dict[str, Any]:
        """
        Convert sample to Messages format (OpenAI-style).
        
        Format:
        {
            "id": "0",
            "messages": [
                {"role": "user", "content": "..."},
                {"role": "assistant", "content": "..."}
            ],
            "origin_chunk": "...",
            "status": "corrected"
        }
        
        Args:
            sample: Sample to convert
        
        Returns:
            Dictionary in Messages format
        """
        return {
            "id": sample.id,
            "messages": [
                {
                    "role": "user",
                    "content": sample.final_instruction or sample.edited_instruction or sample.instruction
                },
                {
                    "role": "assistant",
                    "content": sample.final_output or sample.edited_output or sample.output
                }
            ],
            "origin_chunk": sample.chunk,
            "status": sample.status
        }
    
    def format_alpaca(self, sample: Sample) -> Dict[str, Any]:
        """
        Convert sample to Alpaca format.
        
        Format:
        {
            "instruction": "...",
            "input": "",
            "output": "...",
            "id": "0"
        }
        
        Args:
            sample: Sample to convert
        
        Returns:
            Dictionary in Alpaca format
        """
        return {
            "instruction": sample.final_instruction or sample.edited_instruction or sample.instruction,
            "input": "",
            "output": sample.final_output or sample.edited_output or sample.output,
            "id": sample.id
        }
    
    def format_sharegpt(self, sample: Sample) -> Dict[str, Any]:
        """
        Convert sample to ShareGPT format.
        
        Format:
        {
            "conversations": [
                {"from": "human", "value": "..."},
                {"from": "gpt", "value": "..."}
            ],
            "id": "0"
        }
        
        Args:
            sample: Sample to convert
        
        Returns:
            Dictionary in ShareGPT format
        """
        return {
            "conversations": [
                {
                    "from": "human",
                    "value": sample.final_instruction or sample.edited_instruction or sample.instruction
                },
                {
                    "from": "gpt",
                    "value": sample.final_output or sample.edited_output or sample.output
                }
            ],
            "id": sample.id
        }
    
    def format_query_response(self, sample: Sample) -> Dict[str, Any]:
        """
        Convert sample to Query-Response format.
        
        Format:
        {
            "query": "...",
            "response": "...",
            "id": "0"
        }
        
        Args:
            sample: Sample to convert
        
        Returns:
            Dictionary in Query-Response format
        """
        return {
            "query": sample.final_instruction or sample.edited_instruction or sample.instruction,
            "response": sample.final_output or sample.edited_output or sample.output,
            "id": sample.id
        }
    
    def clear(self):
        """Clear all corrected samples from the export queue."""
        self.corrected_samples.clear()
    
    def get_sample_count(self) -> int:
        """Get the number of samples in the export queue."""
        return len(self.corrected_samples)
