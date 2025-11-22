"""Shared enums and dataclasses."""

from __future__ import annotations

from dataclasses import dataclass, asdict, field
from enum import Enum
from typing import Any, Dict, List, Mapping, Optional, TYPE_CHECKING
from uuid import uuid4

from .utils import utc_now
from .signature import Signature

if TYPE_CHECKING:  # pragma: no cover - structure only
    from ..audit import AuditEvent as RuntimeAuditEvent


class ExperimentStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DatasetType(str, Enum):
    REFERENCE = "reference"
    EXPERIMENTAL = "experimental"
    TRAINING = "training"
    INFERENCE = "inference"


@dataclass(slots=True)
class BaseRecord:
    record_id: str
    created_at: str
    updated_at: str
    audit_trail: List[str] = field(default_factory=list)
    last_audit_event_id: Optional[str] = None
    signature: Optional[Signature] = field(default=None, repr=False)

    @classmethod
    def new_id(cls) -> str:
        return str(uuid4())

    def touch(self) -> None:
        self.updated_at = utc_now()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def attach_audit_event(self, event: str | "RuntimeAuditEvent") -> None:
        """Track audit event identifiers for ALCOA+ provenance."""

        event_id = event.event_id if hasattr(event, "event_id") else str(event)
        if not event_id:
            return
        self.last_audit_event_id = event_id
        if event_id not in self.audit_trail:
            self.audit_trail.append(event_id)

    def apply_signature(self, signature: Signature) -> None:
        """Attach a stub signature placeholder and refresh updated_at."""

        self.signature = signature
        self.attach_audit_event(signature.stub_token)
        self.touch()


@dataclass(slots=True)
class MetadataRecord(BaseRecord):
    metadata: Mapping[str, Any]
