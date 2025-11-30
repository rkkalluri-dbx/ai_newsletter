"""Vendor model."""
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Vendor:
    """Vendor entity representing external contractors."""

    name: str
    code: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "vendor_id": self.id,  # Alias for frontend compatibility
            "name": self.name,
            "vendor_name": self.name,  # Alias for frontend compatibility
            "code": self.code,
            "contact_name": self.contact_name,
            "contact_email": self.contact_email,
            "contact_phone": None,  # Not in DB but expected by frontend
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_row(cls, row: dict) -> "Vendor":
        """Create Vendor from database row."""
        return cls(
            id=row["id"],
            name=row["name"],
            code=row["code"],
            contact_name=row.get("contact_name"),
            contact_email=row.get("contact_email"),
            is_active=row.get("is_active", True),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )
