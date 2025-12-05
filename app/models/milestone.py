"""Milestone model."""
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional


class MilestoneStage:
    """Milestone stage constants matching project lifecycle."""
    AUTHORIZED = "authorized"
    ASSIGNED_TO_VENDOR = "assigned_to_vendor"
    DESIGN_SUBMITTED = "design_submitted"
    QA_QC = "qa_qc"
    APPROVED = "approved"
    CONSTRUCTION_READY = "construction_ready"

    ALL = [AUTHORIZED, ASSIGNED_TO_VENDOR, DESIGN_SUBMITTED, QA_QC, APPROVED, CONSTRUCTION_READY]

    # Default SLA thresholds in days
    SLA_THRESHOLDS = {
        AUTHORIZED: None,  # No SLA for authorization
        ASSIGNED_TO_VENDOR: 7,
        DESIGN_SUBMITTED: None,  # Immediate
        QA_QC: 7,
        APPROVED: 3,
        CONSTRUCTION_READY: None,
    }


@dataclass
class Milestone:
    """Milestone entity representing project checkpoints."""

    project_id: str
    stage: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    expected_date: Optional[date] = None
    actual_date: Optional[date] = None
    sla_days: Optional[int] = None
    is_overdue: bool = False
    days_overdue: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "project_id": self.project_id,
            "stage": self.stage,
            "expected_date": self.expected_date.isoformat() if self.expected_date else None,
            "actual_date": self.actual_date.isoformat() if self.actual_date else None,
            "sla_days": self.sla_days,
            "is_overdue": self.is_overdue,
            "days_overdue": self.days_overdue,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_row(cls, row: dict) -> "Milestone":
        """Create Milestone from database row."""
        return cls(
            id=row["id"],
            project_id=row["project_id"],
            stage=row["stage"],
            expected_date=row.get("expected_date"),
            actual_date=row.get("actual_date"),
            sla_days=row.get("sla_days"),
            is_overdue=row.get("is_overdue", False),
            days_overdue=row.get("days_overdue", 0),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )

    def calculate_overdue(self) -> None:
        """Calculate if milestone is overdue and by how many days."""
        if self.expected_date and not self.actual_date:
            today = date.today()
            if today > self.expected_date:
                self.is_overdue = True
                self.days_overdue = (today - self.expected_date).days
            else:
                self.is_overdue = False
                self.days_overdue = 0
        elif self.actual_date:
            self.is_overdue = False
            self.days_overdue = 0
