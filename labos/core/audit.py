# labos/core/audit.py

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict


@dataclass
class AuditEvent:
    """
    Minimal audit event.

    This is where ALCOA+ eventually lands:
    - Who did what, when, and why
    - Original vs new values
    - Link to experiment/job/dataset/module

    Phase 0:
    - Just enough structure to display in the UI and to remind us that
      every serious operation should emit an AuditEvent.
    """

    id: str
    actor: str
    action: str
    target: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "actor": self.actor,
            "action": self.action,
            "target": self.target,
            "created_at": self.created_at.isoformat(),
            "details": self.details,
        }

    @classmethod
    def example(cls, idx: int = 1) -> "AuditEvent":
        return cls(
            id=f"AUD-{idx:03d}",
            actor="phase0-system",
            action="init",
            target="LabOS",
            details={"phase": "Phase 0 skeleton"},
        )
