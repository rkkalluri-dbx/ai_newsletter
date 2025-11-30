"""AuditLog model."""
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


class AuditAction:
    """Audit action type constants."""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    STATUS_CHANGE = "status_change"
    REVISION_ADDED = "revision_added"

    ALL = [CREATE, UPDATE, DELETE, STATUS_CHANGE, REVISION_ADDED]


@dataclass
class AuditLog:
    """AuditLog entity for tracking changes to projects."""

    project_id: str
    action: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    field_name: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    changes: Optional[str] = None  # JSON string for multiple field changes
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "project_id": self.project_id,
            "action": self.action,
            "field_name": self.field_name,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "changes": self.changes,
            "user_id": self.user_id,
            "user_email": self.user_email,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_row(cls, row: dict) -> "AuditLog":
        """Create AuditLog from database row."""
        return cls(
            id=row["id"],
            project_id=row["project_id"],
            action=row["action"],
            field_name=row.get("field_name"),
            old_value=row.get("old_value"),
            new_value=row.get("new_value"),
            changes=row.get("changes"),
            user_id=row.get("user_id"),
            user_email=row.get("user_email"),
            created_at=row.get("created_at"),
        )
