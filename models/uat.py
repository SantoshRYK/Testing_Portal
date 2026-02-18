# models/uat.py
"""
UAT (User Acceptance Testing) data model
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum

class UATStatus(Enum):
    """UAT status enumeration"""
    NOT_STARTED = "Not Started"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    ON_HOLD = "On Hold"
    CANCELLED = "Cancelled"

class UATResult(Enum):
    """UAT result enumeration"""
    PENDING = "Pending"
    PASS = "Pass"
    FAIL = "Fail"
    PARTIAL_PASS = "Partial Pass"

@dataclass
class UATRecord:
    """UAT record data model"""
    id: str
    trial_id: str
    uat_round: str
    category: str
    planned_start_date: str
    planned_end_date: str
    status: str
    result: str
    created_by: str
    record_type: str = "uat"
    category_type: Optional[str] = None
    actual_start_date: Optional[str] = None
    actual_end_date: Optional[str] = None
    email_body: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    updated_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    updated_by: Optional[str] = None
    notes: Optional[str] = None
    attachments: Optional[list] = None
    
    def to_dict(self):
        """Convert UAT record to dictionary"""
        return {
            "id": self.id,
            "record_type": self.record_type,
            "trial_id": self.trial_id,
            "uat_round": self.uat_round,
            "category": self.category,
            "category_type": self.category_type,
            "planned_start_date": self.planned_start_date,
            "planned_end_date": self.planned_end_date,
            "actual_start_date": self.actual_start_date,
            "actual_end_date": self.actual_end_date,
            "status": self.status,
            "result": self.result,
            "email_body": self.email_body,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "updated_by": self.updated_by,
            "notes": self.notes,
            "attachments": self.attachments
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create UAT record from dictionary"""
        return cls(
            id=data.get("id", ""),
            trial_id=data.get("trial_id", ""),
            uat_round=data.get("uat_round", ""),
            category=data.get("category", ""),
            planned_start_date=data.get("planned_start_date", ""),
            planned_end_date=data.get("planned_end_date", ""),
            status=data.get("status", "Not Started"),
            result=data.get("result", "Pending"),
            created_by=data.get("created_by", ""),
            record_type=data.get("record_type", "uat"),
            category_type=data.get("category_type"),
            actual_start_date=data.get("actual_start_date"),
            actual_end_date=data.get("actual_end_date"),
            email_body=data.get("email_body"),
            created_at=data.get("created_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            updated_at=data.get("updated_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            updated_by=data.get("updated_by"),
            notes=data.get("notes"),
            attachments=data.get("attachments")
        )
    
    def is_completed(self):
        """Check if UAT is completed"""
        return self.status == "Completed"
    
    def is_passed(self):
        """Check if UAT passed"""
        return self.result == "Pass"
    
    def get_planned_duration(self):
        """Get planned duration in days"""
        try:
            start = datetime.strptime(self.planned_start_date, "%Y-%m-%d")
            end = datetime.strptime(self.planned_end_date, "%Y-%m-%d")
            return (end - start).days
        except:
            return 0
    
    def get_actual_duration(self):
        """Get actual duration in days"""
        if self.actual_start_date and self.actual_end_date:
            try:
                start = datetime.strptime(self.actual_start_date, "%Y-%m-%d")
                end = datetime.strptime(self.actual_end_date, "%Y-%m-%d")
                return (end - start).days
            except:
                return None
        return None
    
    def is_delayed(self):
        """Check if UAT is delayed"""
        if self.actual_end_date and self.planned_end_date:
            try:
                actual = datetime.strptime(self.actual_end_date, "%Y-%m-%d")
                planned = datetime.strptime(self.planned_end_date, "%Y-%m-%d")
                return actual > planned
            except:
                return False
        return False