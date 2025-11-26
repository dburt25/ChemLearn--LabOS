# labos/core/audit.py

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4


logger = logging.getLogger(__name__)


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
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    details: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("AuditEvent id is required")
        if any(ch.isspace() for ch in self.id):
            raise ValueError("AuditEvent id cannot include whitespace")

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
    def from_dict(cls, payload: Dict[str, Any]) -> "AuditEvent | None":
        required = {"id", "actor", "action", "target", "created_at"}
        missing = sorted(required - payload.keys())
        if missing:
            logger.warning("Skipping audit payload missing keys: %s", ", ".join(missing))
            return None

        try:
            created_at_raw = payload["created_at"]
            created_at = created_at_raw if isinstance(created_at_raw, datetime) else datetime.fromisoformat(str(created_at_raw))
        except Exception as exc:
            logger.warning("Skipping audit %s due to timestamp error: %s", payload.get("id", "<unknown>"), exc)
            return None

        try:
            return cls(
                id=str(payload["id"]),
                actor=str(payload["actor"]),
                action=str(payload["action"]),
                target=str(payload["target"]),
                created_at=created_at,
                details=dict(payload.get("details") or {}),
            )
        except Exception as exc:
            logger.warning("Skipping audit %s due to validation error: %s", payload.get("id", "<unknown>"), exc)
            return None

    @classmethod
    def example(cls, idx: int = 1) -> "AuditEvent":
        return cls(
            id=f"AUD-{idx:03d}",
            actor="phase0-system",
            action="init",
            target="LabOS",
            details={"phase": "Phase 0 skeleton"},
        )


def record_event(actor: str, action: str, target: str, details: Optional[Dict[str, Any]] = None) -> AuditEvent:
    """Create a simple audit event with a generated identifier."""

    event_id = f"AUD-{uuid4()}"
    return AuditEvent(
        id=event_id,
        actor=actor,
        action=action,
        target=target,
        details=details or {},
    )
