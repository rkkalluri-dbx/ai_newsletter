"""Alert model."""
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


class AlertType:
    """Alert type constants."""
    MILESTONE_OVERDUE = "milestone_overdue"
    MILESTONE_APPROACHING = "milestone_approaching"
    STATUS_CHANGE = "status_change"
    REVISION_ADDED = "revision_added"

    ALL = [MILESTONE_OVERDUE, MILESTONE_APPROACHING, STATUS_CHANGE, REVISION_ADDED]


class AlertSeverity:
    """Alert severity constants."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

    ALL = [INFO, WARNING, CRITICAL]


@dataclass
class Alert:
    """Alert entity for notifications about project issues."""

    project_id: str
    alert_type: str
    message: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    severity: str = AlertSeverity.INFO
    is_acknowledged: bool = False
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self, include_project: bool = False) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "project_id": self.project_id,
            "alert_type": self.alert_type,
            "message": self.message,
            "severity": self.severity,
            "is_acknowledged": self.is_acknowledged,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "acknowledged_by": self.acknowledged_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_row(cls, row: dict) -> "Alert":
        """Create Alert from database row."""
        return cls(
            id=row["id"],
            project_id=row["project_id"],
            alert_type=row["alert_type"],
            message=row["message"],
            severity=row.get("severity", AlertSeverity.INFO),
            is_acknowledged=row.get("is_acknowledged", False),
            acknowledged_at=row.get("acknowledged_at"),
            acknowledged_by=row.get("acknowledged_by"),
            created_at=row.get("created_at"),
        )

    def acknowledge(self, user_id: str) -> None:
        """Mark alert as acknowledged."""
        self.is_acknowledged = True
        self.acknowledged_at = datetime.utcnow()
        self.acknowledged_by = user_id
