"""
Application state model for LLM-QA Correction Workbench.

Manages the global state of the application including current sample,
loaded samples, and configuration settings.
"""

from dataclasses import dataclass, field
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from services.data_manager import DataManager
    from services.export_manager import ExportManager

from .sample import Sample


@dataclass
class ApplicationState:
    """
    Global application state container.
    
    Attributes:
        current_index: Index of currently displayed sample
        samples: List of loaded samples
        data_manager: DataManager instance for CSV operations
        export_manager: ExportManager instance for JSON export
        phase: Current workflow phase (1=editing, 2=diff confirmation)
        batch_size: Number of samples to load per batch
        export_format: Selected export format (messages/alpaca/sharegpt/query-response)
        csv_path: Path to the loaded CSV file
    """
    
    current_index: int = 0
    samples: List[Sample] = field(default_factory=list)
    data_manager: Optional[object] = None  # DataManager
    export_manager: Optional[object] = None  # ExportManager
    phase: int = 1
    batch_size: int = 50
    export_format: str = "messages"
    csv_path: str = ""
    
    def get_current_sample(self) -> Optional[Sample]:
        """Get the currently displayed sample."""
        if 0 <= self.current_index < len(self.samples):
            return self.samples[self.current_index]
        return None
    
    def get_corrected_count(self) -> int:
        """Count samples with 'corrected' status."""
        return sum(1 for sample in self.samples if sample.status == "corrected")
    
    def get_discarded_count(self) -> int:
        """Count samples with 'discarded' status."""
        return sum(1 for sample in self.samples if sample.status == "discarded")
    
    def get_processed_count(self) -> int:
        """Count all processed samples (corrected + discarded)."""
        return self.get_corrected_count() + self.get_discarded_count()
    
    def get_total_loaded(self) -> int:
        """Get total number of loaded samples."""
        return len(self.samples)
