# models/change_request.py
"""
Change Request data model
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any

@dataclass
class ChangeRequest:
    """Change Request data model"""
    id: str
    trial_name: str
    cr_no: str
    category: str
    form_event_name: str = ""
    item_rule_name: str = ""
    requirements: str = ""
    version_changes: str = ""
    protocol_amendment: str = ""
    retrospective_case_book: str = ""
    cdb_impact: str = "No"
    item_def_impact: str = "No"
    datacore_impact: str = "No"
    comments: str = ""
    current_version: str = ""
    impacted_e2b_vsec: str = "No"
    impacted_rtsm: str = "No"
    rtsm_comments: str = ""
    created_by: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    updated_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    updated_by: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "trial_name": self.trial_name,
            "cr_no": self.cr_no,
            "category": self.category,
            "form_event_name": self.form_event_name,
            "item_rule_name": self.item_rule_name,
            "requirements": self.requirements,
            "version_changes": self.version_changes,
            "protocol_amendment": self.protocol_amendment,
            "retrospective_case_book": self.retrospective_case_book,
            "cdb_impact": self.cdb_impact,
            "item_def_impact": self.item_def_impact,
            "datacore_impact": self.datacore_impact,
            "comments": self.comments,
            "current_version": self.current_version,
            "impacted_e2b_vsec": self.impacted_e2b_vsec,
            "impacted_rtsm": self.impacted_rtsm,
            "rtsm_comments": self.rtsm_comments,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "updated_by": self.updated_by
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create from dictionary"""
        return cls(
            id=data.get("id", ""),
            trial_name=data.get("trial_name", ""),
            cr_no=data.get("cr_no", ""),
            category=data.get("category", ""),
            form_event_name=data.get("form_event_name", ""),
            item_rule_name=data.get("item_rule_name", ""),
            requirements=data.get("requirements", ""),
            version_changes=data.get("version_changes", ""),
            protocol_amendment=data.get("protocol_amendment", ""),
            retrospective_case_book=data.get("retrospective_case_book", ""),
            cdb_impact=data.get("cdb_impact", "No"),
            item_def_impact=data.get("item_def_impact", "No"),
            datacore_impact=data.get("datacore_impact", "No"),
            comments=data.get("comments", ""),
            current_version=data.get("current_version", ""),
            impacted_e2b_vsec=data.get("impacted_e2b_vsec", "No"),
            impacted_rtsm=data.get("impacted_rtsm", "No"),
            rtsm_comments=data.get("rtsm_comments", ""),
            created_by=data.get("created_by", ""),
            created_at=data.get("created_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            updated_at=data.get("updated_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            updated_by=data.get("updated_by")
        )
    
    def get_category_emoji(self) -> str:
        """Get emoji for category"""
        if "Rule" in self.category:
            return "📋"
        elif "Form" in self.category:
            return "📝"
        return "🔄"