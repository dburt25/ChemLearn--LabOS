"""Experiment record with lifecycle state and job linkage."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _validate_id(value: str, prefix: str) -> str:
    if not value or not value.startswith(prefix):
        raise ValueError(f"Experiment IDs must start with `{prefix}`; received {value!r}")
    if any(ch.isspace() for ch in value):
        raise ValueError("Experiment IDs cannot contain whitespace")
    return value


class ExperimentStatus(str, Enum):
    DRAFT = "draft"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ExperimentMode(str, Enum):
    LEARNER = "Learner"
    LAB = "Lab"
    BUILDER = "Builder"


def _metadata_factory() -> Dict[str, Any]:
    return {}


def _job_list_factory() -> List[str]:
    return []

@dataclass(slots=True)
class Experiment:
    """Phase 0 experiment record with lightweight lineage hooks."""

    id: str
    name: str
    owner: str = "local-user"
    mode: str = ExperimentMode.LAB
    status: ExperimentStatus = ExperimentStatus.DRAFT
    metadata: Dict[str, Any] = field(default_factory=_metadata_factory)
    jobs: List[str] = field(default_factory=_job_list_factory)
    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = field(default_factory=_utc_now)

    def __post_init__(self) -> None:
        self.id = _validate_id(self.id, "EXP-")
        if isinstance(self.status, str):
            self.status = ExperimentStatus(self.status)
        if isinstance(self.mode, str):
            self.mode = ExperimentMode(self.mode)

    def add_job(self, job_id: str) -> None:
        if job_id in self.jobs:
            return
        self.jobs.append(job_id)
        self.updated_at = _utc_now()

    def mark_running(self) -> None:
        self.status = ExperimentStatus.RUNNING
        self.updated_at = _utc_now()

    def mark_completed(self) -> None:
        self.status = ExperimentStatus.COMPLETED
        self.updated_at = _utc_now()

    def mark_failed(self) -> None:
        self.status = ExperimentStatus.FAILED
        self.updated_at = _utc_now()

    def is_finished(self) -> bool:
        return self.status in {ExperimentStatus.COMPLETED, ExperimentStatus.FAILED}

    def short_label(self) -> str:
        return f"{self.id} — {self.name}"

    def to_dict(self) -> Dict[str, Any]:  # backwards compatibility helper
        data = asdict(self)
        data["status"] = self.status.value
        data["mode"] = self.mode.value
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        return data

    @classmethod
    def example(cls, idx: int = 1, mode: str = "Lab") -> "Experiment":
        return cls(
            id=f"EXP-{idx:03d}",
            name=f"Example Experiment {idx}",
            owner="phase0",
            mode=mode,
            metadata={"phase": "Phase 0 skeleton"},
        )
