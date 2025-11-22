"""Experiment record with lifecycle state and job linkage."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict, Field, field_validator  # type: ignore


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


class Experiment(BaseModel):
    """Phase 0 experiment record with lightweight lineage hooks."""

    model_config = ConfigDict(validate_assignment=True)

    id: str = Field(..., description="Unique experiment identifier (e.g., EXP-001)")
    name: str
    owner: str = "local-user"
    mode: str = "Lab"
    status: ExperimentStatus = ExperimentStatus.DRAFT
    metadata: Dict[str, Any] = Field(default_factory=dict)
    jobs: List[str] = Field(default_factory=list, description="List of associated job IDs")
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)

    @field_validator("id", mode="before")
    @classmethod
    def _id_validator(cls, value: str) -> str:
        return _validate_id(value, "EXP-")

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

    def short_label(self) -> str:
        return f"{self.id} — {self.name}"

    def to_dict(self) -> Dict[str, Any]:  # backwards compatibility helper
        return self.model_dump(mode="python")

    @classmethod
    def example(cls, idx: int = 1, mode: str = "Lab") -> "Experiment":
        return cls(
            id=f"EXP-{idx:03d}",
            name=f"Example Experiment {idx}",
            owner="phase0",
            mode=mode,
            metadata={"phase": "Phase 0 skeleton"},
        )
