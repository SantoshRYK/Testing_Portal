# models/audit.py
"""
Audit log data model
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

class AuditAction(Enum):
    """Audit action enumeration"""
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    VIEW = "view"
    EXPORT = "export"
    APPROVE = "approve"
    REJECT = "reject"
    PASSWORD_RESET = "password_reset"
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    ALLOCATION_CREATED = "allocation_created"
    ALLOCATION_UPDATED = "allocation_updated"
    ALLOCATION_DELETED = "allocation_deleted"
    UAT_CREATED = "uat_created"
    UAT_UPDATED = "uat_updated"
    UAT_DELETED = "uat_deleted"
    EMAIL_SENT = "email_sent"
    CONFIG_CHANGED = "config_changed"

class AuditCategory(Enum):
    """Audit category enumeration"""
    AUTHENTICATION = "authentication"
    USER_MANAGEMENT = "user_management"
    ALLOCATION = "allocation"
    UAT = "uat"
    SYSTEM = "system"
    EMAIL = "email"

@dataclass
class AuditLog:
    """Audit log data model"""
    id: str
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    username: str = ""
    action: str = ""
    category: str = "system"
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None
    
    def to_dict(self):
        """Convert audit log to dictionary"""
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "username": self.username,
            "action": self.action,
            "category": self.category,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "details": self.details,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "success": self.success,
            "error_message": self.error_message
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create audit log from dictionary"""
        return cls(
            id=data.get("id", ""),
            timestamp=data.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            username=data.get("username", ""),
            action=data.get("action", ""),
            category=data.get("category", "system"),
            entity_type=data.get("entity_type"),
            entity_id=data.get("entity_id"),
            details=data.get("details"),
            ip_address=data.get("ip_address"),
            user_agent=data.get("user_agent"),
            success=data.get("success", True),
            error_message=data.get("error_message")
        )
    
    def get_formatted_timestamp(self):
        """Get formatted timestamp"""
        try:
            dt = datetime.strptime(self.timestamp, "%Y-%m-%d %H:%M:%S")
            return dt.strftime("%b %d, %Y at %I:%M %p")
        except:
            return self.timestamp
    
    def get_action_emoji(self):
        """Get emoji for action"""
        action_emojis = {
            "login": "🔐",
            "logout": "🚪",
            "login_failed": "❌",
            "create": "➕",
            "update": "✏️",
            "delete": "🗑️",
            "view": "👁️",
            "export": "📥",
            "approve": "✅",
            "reject": "❌",
            "password_reset": "🔑",
            "email_sent": "📧"
        }
        return action_emojis.get(self.action, "📝")