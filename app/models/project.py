"""Project model."""
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional


class ProjectStatus:
    """Project lifecycle status constants."""
    AUTHORIZED = "authorized"
    ASSIGNED_TO_VENDOR = "assigned_to_vendor"
    DESIGN_SUBMITTED = "design_submitted"
    QA_QC = "qa_qc"
    APPROVED = "approved"
    CONSTRUCTION_READY = "construction_ready"

    ALL = [AUTHORIZED, ASSIGNED_TO_VENDOR, DESIGN_SUBMITTED, QA_QC, APPROVED, CONSTRUCTION_READY]


class Priority:
    """Priority level constants."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"

    ALL = [LOW, NORMAL, HIGH, CRITICAL]


@dataclass
class Project:
    """Project entity representing capital projects."""

    work_order_number: str
    vendor_id: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: Optional[str] = None
    region: Optional[str] = None
    status: str = ProjectStatus.AUTHORIZED
    priority: str = Priority.NORMAL
    authorized_date: Optional[date] = None
    sent_to_vendor_date: Optional[date] = None
    received_from_vendor_date: Optional[date] = None
    target_completion_date: Optional[date] = None
    actual_completion_date: Optional[date] = None
    revision_count: int = 0
    version: int = 1
    budget: float = 0.0
    actual_spend: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def _calculate_progress(self) -> int:
        """Calculate progress percentage based on status."""
        progress_map = {
            ProjectStatus.AUTHORIZED: 0,
            ProjectStatus.ASSIGNED_TO_VENDOR: 20,
            ProjectStatus.DESIGN_SUBMITTED: 40,
            ProjectStatus.QA_QC: 60,
            ProjectStatus.APPROVED: 80,
            ProjectStatus.CONSTRUCTION_READY: 100,
        }
        return progress_map.get(self.status, 0)

    def to_dict(self, include_vendor: bool = False) -> dict:
        """Convert to dictionary."""
        data = {
            "id": self.id,
            "project_id": self.id,  # Alias for frontend compatibility
            "project_name": self.work_order_number,  # Alias for frontend compatibility
            "work_order_number": self.work_order_number,
            "vendor_id": self.vendor_id,
            "description": self.description,
            "region": self.region,
            "status": self.status,
            "priority": self.priority,
            "start_date": self.authorized_date.isoformat() if self.authorized_date else None,  # Alias
            "authorized_date": self.authorized_date.isoformat() if self.authorized_date else None,
            "sent_to_vendor_date": self.sent_to_vendor_date.isoformat() if self.sent_to_vendor_date else None,
            "received_from_vendor_date": self.received_from_vendor_date.isoformat() if self.received_from_vendor_date else None,
            "target_completion_date": self.target_completion_date.isoformat() if self.target_completion_date else None,
            "actual_completion_date": self.actual_completion_date.isoformat() if self.actual_completion_date else None,
            "revision_count": self.revision_count,
            "version": self.version,
            "budget": float(self.budget) if self.budget else 0,
            "actual_spend": float(self.actual_spend) if self.actual_spend else 0,
            "progress_percentage": self._calculate_progress(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        return data

    @classmethod
    def from_row(cls, row: dict) -> "Project":
        """Create Project from database row."""
        return cls(
            id=row["id"],
            work_order_number=row["work_order_number"],
            vendor_id=row["vendor_id"],
            description=row.get("description"),
            region=row.get("region"),
            status=row.get("status", ProjectStatus.AUTHORIZED),
            priority=row.get("priority", Priority.NORMAL),
            authorized_date=row.get("authorized_date"),
            sent_to_vendor_date=row.get("sent_to_vendor_date"),
            received_from_vendor_date=row.get("received_from_vendor_date"),
            target_completion_date=row.get("target_completion_date"),
            actual_completion_date=row.get("actual_completion_date"),
            revision_count=row.get("revision_count", 0),
            version=row.get("version", 1),
            budget=float(row.get("budget") or 0),
            actual_spend=float(row.get("actual_spend") or 0),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )
