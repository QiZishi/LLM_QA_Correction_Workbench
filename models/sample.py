"""
Sample data model for LLM-QA Correction Workbench.

Represents a single question-answer data record with tracking fields
for the two-phase correction workflow.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Sample:
    """
    Represents a single question-answer data record.
    
    Attributes:
        id: Unique identifier (CSV row index)
        instruction: Question text
        output: Answer text
        chunk: Reference content
        status: Sample status (unprocessed/corrected/discarded)
        original_instruction: Original question for diff comparison
        original_output: Original answer for diff comparison
        edited_instruction: Phase 1 edited question
        edited_output: Phase 1 edited answer
        final_instruction: Phase 2 final confirmed question
        final_output: Phase 2 final confirmed answer (with tags)
    """
    
    id: str
    instruction: str
    output: str
    chunk: str
    status: str = "unprocessed"
    original_instruction: str = ""
    original_output: str = ""
    edited_instruction: str = ""
    edited_output: str = ""
    final_instruction: str = ""
    final_output: str = ""
    
    def __post_init__(self):
        """Initialize original fields if not provided."""
        if not self.original_instruction:
            self.original_instruction = self.instruction
        if not self.original_output:
            self.original_output = self.output
