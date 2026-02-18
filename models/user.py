# models/user.py
"""
User data model
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum

class UserRole(Enum):
    """User role enumeration"""
    SUPERUSER = "superuser"
    MANAGER = "manager"
    ADMIN = "admin"
    USER = "user"
    AUDIT_REVIEWER = "audit_reviewer"  # ✅ NEW: Added audit reviewer role

class UserStatus(Enum):
    """User status enumeration"""
    ACTIVE = "active"
    PENDING = "pending"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"

@dataclass
class User:
    """User data model"""
    username: str
    password: str  # Hashed password
    email: str
    role: str = "user"
    status: str = "active"
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    created_by: Optional[str] = None
    approved_by: Optional[str] = None
    updated_at: Optional[str] = None
    updated_by: Optional[str] = None
    password_reset_at: Optional[str] = None
    password_reset_by: Optional[str] = None
    last_login: Optional[str] = None
    
    # ✅ NEW: Audit Reviewer fields
    is_audit_reviewer: bool = False
    audit_reviewer_requested: bool = False
    audit_reviewer_justification: Optional[str] = None
    audit_reviewer_approved_by: Optional[str] = None
    audit_reviewer_approved_at: Optional[str] = None
    
    def to_dict(self):
        """Convert user to dictionary"""
        return {
            "username": self.username,
            "password": self.password,
            "email": self.email,
            "role": self.role,
            "status": self.status,
            "created_at": self.created_at,
            "created_by": self.created_by,
            "approved_by": self.approved_by,
            "updated_at": self.updated_at,
            "updated_by": self.updated_by,
            "password_reset_at": self.password_reset_at,
            "password_reset_by": self.password_reset_by,
            "last_login": self.last_login,
            # ✅ NEW: Include audit reviewer fields in dictionary
            "is_audit_reviewer": self.is_audit_reviewer,
            "audit_reviewer_requested": self.audit_reviewer_requested,
            "audit_reviewer_justification": self.audit_reviewer_justification,
            "audit_reviewer_approved_by": self.audit_reviewer_approved_by,
            "audit_reviewer_approved_at": self.audit_reviewer_approved_at
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create user from dictionary"""
        return cls(
            username=data.get("username", ""),
            password=data.get("password", ""),
            email=data.get("email", ""),
            role=data.get("role", "user"),
            status=data.get("status", "active"),
            created_at=data.get("created_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            created_by=data.get("created_by"),
            approved_by=data.get("approved_by"),
            updated_at=data.get("updated_at"),
            updated_by=data.get("updated_by"),
            password_reset_at=data.get("password_reset_at"),
            password_reset_by=data.get("password_reset_by"),
            last_login=data.get("last_login"),
            # ✅ NEW: Load audit reviewer fields from dictionary
            is_audit_reviewer=data.get("is_audit_reviewer", False),
            audit_reviewer_requested=data.get("audit_reviewer_requested", False),
            audit_reviewer_justification=data.get("audit_reviewer_justification"),
            audit_reviewer_approved_by=data.get("audit_reviewer_approved_by"),
            audit_reviewer_approved_at=data.get("audit_reviewer_approved_at")
        )
    
    def is_active(self):
        """Check if user is active"""
        return self.status == "active"
    
    def is_admin(self):
        """Check if user has admin privileges"""
        return self.role in ["superuser", "admin", "manager"]
    
    def can_manage_users(self):
        """Check if user can manage other users"""
        return self.role in ["superuser", "manager"]
    
    def can_approve_requests(self):
        """Check if user can approve requests"""
        return self.role == "superuser"
    
    # ✅ NEW: Method to check if user is audit reviewer
    def is_audit_reviewer_user(self):
        """Check if user has audit reviewer access"""
        return self.is_audit_reviewer

@dataclass
class PendingUser:
    """Pending user registration model"""
    username: str
    password: str  # Hashed
    email: str
    requested_role: str = "user"
    status: str = "pending"
    requested_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    reason: Optional[str] = None
    
    # ✅ NEW: Audit Reviewer request fields for pending users
    audit_reviewer_requested: bool = False
    audit_reviewer_justification: Optional[str] = None
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "username": self.username,
            "password": self.password,
            "email": self.email,
            "requested_role": self.requested_role,
            "status": self.status,
            "requested_at": self.requested_at,
            "reason": self.reason,
            # ✅ NEW: Include audit reviewer request in dictionary
            "audit_reviewer_requested": self.audit_reviewer_requested,
            "audit_reviewer_justification": self.audit_reviewer_justification
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create from dictionary"""
        return cls(
            username=data.get("username", ""),
            password=data.get("password", ""),
            email=data.get("email", ""),
            requested_role=data.get("requested_role", "user"),
            status=data.get("status", "pending"),
            requested_at=data.get("requested_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            reason=data.get("reason"),
            # ✅ NEW: Load audit reviewer request from dictionary
            audit_reviewer_requested=data.get("audit_reviewer_requested", False),
            audit_reviewer_justification=data.get("audit_reviewer_justification")
        )

@dataclass
class PasswordResetRequest:
    """Password reset request model"""
    id: str
    username: str
    email: str
    new_password: str  # Hashed
    reason: str
    status: str = "pending"
    requested_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    rejected_by: Optional[str] = None
    rejected_at: Optional[str] = None
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "new_password": self.new_password,
            "reason": self.reason,
            "status": self.status,
            "requested_at": self.requested_at,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at,
            "rejected_by": self.rejected_by,
            "rejected_at": self.rejected_at
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create from dictionary"""
        return cls(
            id=data.get("id", ""),
            username=data.get("username", ""),
            email=data.get("email", ""),
            new_password=data.get("new_password", ""),
            reason=data.get("reason", ""),
            status=data.get("status", "pending"),
            requested_at=data.get("requested_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            approved_by=data.get("approved_by"),
            approved_at=data.get("approved_at"),
            rejected_by=data.get("rejected_by"),
            rejected_at=data.get("rejected_at")
        )