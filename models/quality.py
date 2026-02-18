"""
Trial Quality Matrix Data Model
"""
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Dict

@dataclass
class QualityRecord:
    """Trial Quality Matrix Record"""
    record_id: str
    trial_id: str
    phase: str
    no_of_uat_plans: str
    no_of_rounds: int
    type_of_requirement: str
    current_round: int
    
    # UAT Metrics
    total_requirements: int
    total_failures: int
    
    # Failure Reasons
    spec_issue: int
    mock_crf_issue: int
    programming_issue: int
    scripting_issue: int
    
    # Additional Fields
    documentation_issues: str
    timeline_adherence: str
    system_deployment_delays: str
    
    # Metadata
    created_by: str
    created_at: str
    updated_at: str
    status: str  # "Active", "Completed", "On Hold"
    
    def __post_init__(self):
        """Calculate defect density after initialization"""
        self.defect_density = self.calculate_defect_density()
    
    def calculate_defect_density(self) -> float:
        """Calculate defect density: (Total Failures / Total Requirements) * 100"""
        if self.total_requirements == 0:
            return 0.0
        return round((self.total_failures / self.total_requirements) * 100, 2)
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        data = asdict(self)
        data['defect_density'] = self.defect_density
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'QualityRecord':
        """Create from dictionary"""
        # Remove defect_density if present (it will be recalculated)
        data_copy = data.copy()
        data_copy.pop('defect_density', None)
        return cls(**data_copy)
    
    def validate(self) -> tuple[bool, str]:
        """Validate record data"""
        # Check if failures exceed requirements
        if self.total_failures > self.total_requirements:
            return False, "Total failures cannot exceed total requirements"
        
        # Check if sum of failure reasons exceeds total failures
        failure_sum = (self.spec_issue + self.mock_crf_issue + 
                      self.programming_issue + self.scripting_issue)
        
        if failure_sum > self.total_failures:
            return False, "Sum of failure reasons cannot exceed total failures"
        
        # Check if current round exceeds total rounds
        if self.current_round > self.no_of_rounds:
            return False, "Current round cannot exceed total rounds"
        
        # Check if rounds is positive
        if self.no_of_rounds <= 0:
            return False, "Number of rounds must be positive"
        
        # Check current round is positive
        if self.current_round <= 0:
            return False, "Current round must be positive"
        
        # Check requirements is positive
        if self.total_requirements <= 0:
            return False, "Total requirements must be positive"
        
        return True, "Valid"