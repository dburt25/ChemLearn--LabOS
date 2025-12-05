"""Experiment domain model and registry."""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import Any, Iterable, Mapping, Optional, Sequence

from .audit import AuditLogger
from .config import LabOSConfig
from .core.errors import ValidationError
from .core.types import BaseRecord, ExperimentStatus
from .core.utils import utc_now
from .storage import JSONFileStore


@dataclass(slots=True)
class Experiment(BaseRecord):
    user_id: str = "unknown"
    title: str = "untitled"
    purpose: str = ""
    status: ExperimentStatus = ExperimentStatus.DRAFT
    inputs: Mapping[str, str] = field(default_factory=dict)
    outputs: Mapping[str, str] = field(default_factory=dict)
    tags: Sequence[str] = field(default_factory=tuple)

    @classmethod
    def create(
        cls,
        user_id: str,
        title: str,
        purpose: str,
        status: ExperimentStatus = ExperimentStatus.DRAFT,
        inputs: Optional[Mapping[str, str]] = None,
        outputs: Optional[Mapping[str, str]] = None,
        tags: Optional[Sequence[str]] = None,
    ) -> "Experiment":
        now = utc_now()
        return cls(
            record_id=BaseRecord.new_id(),
            created_at=now,
            updated_at=now,
            user_id=user_id,
            title=title,
            purpose=purpose,
            status=status,
            inputs=dict(inputs or {}),
            outputs=dict(outputs or {}),
            tags=tuple(tags or ()),
        )

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any], fallback_id: Optional[str] = None) -> "Experiment":
        """Convert legacy/partial payloads into the canonical Experiment shape."""

        data: dict[str, Any] = dict(payload)

        record_id = data.get("record_id") or data.get("id") or fallback_id or BaseRecord.new_id()
        data["record_id"] = record_id

        created_at = data.get("created_at") or data.get("createdAt")
        if not created_at:
            created_at = utc_now()
        data["created_at"] = created_at

        updated_at = data.get("updated_at") or data.get("updatedAt") or created_at
        data["updated_at"] = updated_at

        data["audit_trail"] = list(data.get("audit_trail") or [])
        data.setdefault("last_audit_event_id", data.get("last_audit_event_id"))
        data.setdefault("signature", data.get("signature"))

        data["user_id"] = data.get("user_id") or data.get("owner") or "unknown"
        data["title"] = data.get("title") or data.get("name") or "untitled"
        data["purpose"] = data.get("purpose") or data.get("description") or ""

        status = data.get("status", ExperimentStatus.DRAFT)
        if isinstance(status, str):
            try:
                data["status"] = ExperimentStatus(status)
            except ValueError:
                try:
                    data["status"] = ExperimentStatus(status.lower())
                except ValueError:
                    data["status"] = ExperimentStatus.DRAFT
        elif not isinstance(status, ExperimentStatus):
            data["status"] = ExperimentStatus.DRAFT

        inputs = data.get("inputs")
        if not isinstance(inputs, Mapping):
            metadata = data.get("metadata") if isinstance(data.get("metadata"), Mapping) else {}
            inputs = metadata or {}
        data["inputs"] = dict(inputs or {})

        outputs = data.get("outputs")
        if not isinstance(outputs, Mapping):
            outputs = {}
        data["outputs"] = dict(outputs or {})

        tags = data.get("tags")
        if isinstance(tags, Sequence) and not isinstance(tags, (str, bytes)):
            data["tags"] = tuple(tags)
        else:
            data["tags"] = tuple()

        allowed_fields = {field.name for field in fields(cls)}
        cleaned = {key: value for key, value in data.items() if key in allowed_fields}
        return cls(**cleaned)


class ExperimentRegistry:
    def __init__(self, config: LabOSConfig, audit: AuditLogger) -> None:
        self.store = JSONFileStore(config.experiments_dir)
        self.audit = audit

    def add(self, experiment: Experiment) -> Experiment:
        if not experiment.title:
            raise ValidationError("Experiment title is required")
        self.store.save(experiment.record_id, experiment.to_dict())
        event = self.audit.record(
            event_type="experiment.created",
            actor=experiment.user_id,
            payload={"experiment_id": experiment.record_id, "status": experiment.status.value},
        )
        experiment.attach_audit_event(event)
        return experiment

    def update_status(self, experiment_id: str, status: ExperimentStatus) -> Experiment:
        experiment = self.get(experiment_id)
        experiment.status = status
        experiment.touch()
        self.store.save(experiment.record_id, experiment.to_dict())
        event = self.audit.record(
            event_type="experiment.status",
            actor="labos.core",
            payload={"experiment_id": experiment.record_id, "status": status.value},
        )
        experiment.attach_audit_event(event)
        return experiment

    def get(self, experiment_id: str) -> Experiment:
        payload = self.store.load(experiment_id)
        return Experiment.from_dict(payload, fallback_id=experiment_id)

    def list_ids(self) -> Iterable[str]:
        return self.store.list_ids()
