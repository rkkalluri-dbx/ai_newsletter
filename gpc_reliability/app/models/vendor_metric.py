"""VendorMetric model."""
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class VendorMetric:
    """VendorMetric entity for tracking vendor performance metrics."""

    vendor_id: str
    period_start: datetime
    period_end: datetime
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    total_projects: int = 0
    completed_projects: int = 0
    active_projects: int = 0
    overdue_projects: int = 0
    on_time_rate: float = 0.0
    avg_cycle_time_days: Optional[float] = None
    revision_rate: float = 0.0
    sla_compliance_rate: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self, include_vendor: bool = False) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "vendor_id": self.vendor_id,
            "period_start": self.period_start.isoformat() if self.period_start else None,
            "period_end": self.period_end.isoformat() if self.period_end else None,
            "total_projects": self.total_projects,
            "completed_projects": self.completed_projects,
            "active_projects": self.active_projects,
            "overdue_projects": self.overdue_projects,
            "on_time_rate": self.on_time_rate,
            "avg_cycle_time_days": self.avg_cycle_time_days,
            "revision_rate": self.revision_rate,
            "sla_compliance_rate": self.sla_compliance_rate,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_row(cls, row: dict) -> "VendorMetric":
        """Create VendorMetric from database row."""
        return cls(
            id=row["id"],
            vendor_id=row["vendor_id"],
            period_start=row["period_start"],
            period_end=row["period_end"],
            total_projects=row.get("total_projects", 0),
            completed_projects=row.get("completed_projects", 0),
            active_projects=row.get("active_projects", 0),
            overdue_projects=row.get("overdue_projects", 0),
            on_time_rate=row.get("on_time_rate", 0.0),
            avg_cycle_time_days=row.get("avg_cycle_time_days"),
            revision_rate=row.get("revision_rate", 0.0),
            sla_compliance_rate=row.get("sla_compliance_rate", 0.0),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )
