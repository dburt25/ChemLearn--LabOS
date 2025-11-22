"""Experiment domain model and registry."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping, Optional, Sequence

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
        return Experiment(**self.store.load(experiment_id))

    def list_ids(self) -> Iterable[str]:
        return self.store.list_ids()
