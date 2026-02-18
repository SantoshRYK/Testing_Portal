# models/allocation.py
"""
Allocation data model
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum

class AllocationStatus(Enum):
    """Allocation status enumeration"""
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"

class TrialCategory(Enum):
    """Trial category enumeration"""
    BUILD = "Build"
    CHANGE_REQUEST = "Change Request"

class System(Enum):
    """System enumeration"""
    INFORM = "INFORM"
    VEEVA = "VEEVA"
    ECOA = "eCOA"
    EPID = "ePID"
    CGM = "CGM"
    OTHERS = "Others"

class TherapeuticArea(Enum):
    """Therapeutic area enumeration"""
    DIABETIC = "Diabetic"
    OBESITY = "Obesity"
    CKAD = "CKAD (Chronic Kidney Allograft Dysfunction)"
    CAGRISEMA = "CagriSema & OLD-D"
    PHASE1_NIS = "Phase 1 & NIS"
    RARE_DISEASE = "Rare Disease"
    OTHERS = "Others"

@dataclass
class Allocation:
    """Allocation data model"""
    id: str
    test_engineer_name: str
    trial_id: str
    system: str
    trial_category: str
    therapeutic_area: str
    role: str
    activity: str
    start_date: str
    end_date: str
    created_by: str
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    trial_category_type: Optional[str] = None
    therapeutic_area_type: Optional[str] = None
    updated_at: Optional[str] = None
    updated_by: Optional[str] = None
    status: str = "active"
    notes: Optional[str] = None
    
    def to_dict(self):
        """Convert allocation to dictionary"""
        return {
            "id": self.id,
            "test_engineer_name": self.test_engineer_name,
            "trial_id": self.trial_id,
            "system": self.system,
            "trial_category": self.trial_category,
            "trial_category_type": self.trial_category_type,
            "therapeutic_area": self.therapeutic_area,
            "therapeutic_area_type": self.therapeutic_area_type,
            "role": self.role,
            "activity": self.activity,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "updated_by": self.updated_by,
            "status": self.status,
            "notes": self.notes
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create allocation from dictionary"""
        return cls(
            id=data.get("id", ""),
            test_engineer_name=data.get("test_engineer_name", ""),
            trial_id=data.get("trial_id", ""),
            system=data.get("system", ""),
            trial_category=data.get("trial_category", ""),
            therapeutic_area=data.get("therapeutic_area", ""),
            role=data.get("role", ""),
            activity=data.get("activity", ""),
            start_date=data.get("start_date", ""),
            end_date=data.get("end_date", ""),
            created_by=data.get("created_by", ""),
            created_at=data.get("created_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            trial_category_type=data.get("trial_category_type"),
            therapeutic_area_type=data.get("therapeutic_area_type"),
            updated_at=data.get("updated_at"),
            updated_by=data.get("updated_by"),
            status=data.get("status", "active"),
            notes=data.get("notes")
        )
    
    def is_active(self):
        """Check if allocation is active"""
        try:
            end_date = datetime.strptime(self.end_date, "%Y-%m-%d")
            return end_date >= datetime.now() and self.status == "active"
        except:
            return False
    
    def get_duration_days(self):
        """Get duration in days"""
        try:
            start = datetime.strptime(self.start_date, "%Y-%m-%d")
            end = datetime.strptime(self.end_date, "%Y-%m-%d")
            return (end - start).days
        except:
            return 0
    
    def is_overdue(self):
        """Check if allocation is overdue"""
        try:
            end_date = datetime.strptime(self.end_date, "%Y-%m-%d")
            return end_date < datetime.now() and self.status == "active"
        except:
            return False