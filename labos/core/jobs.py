"""Job model with dataset lineage hooks and lifecycle helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator  # type: ignore[import]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _validate_id(value: str, prefix: str) -> str:
    if not value or not value.startswith(prefix):
        raise ValueError(f"Job IDs must start with `{prefix}`; received {value!r}")
    if any(ch.isspace() for ch in value):
        raise ValueError("Job IDs cannot contain whitespace")
    return value


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Job(BaseModel):
    """Phase 0 job record with start/finish helpers."""

    model_config = ConfigDict(validate_assignment=True)

    id: str
    experiment_id: str
    kind: str
    status: JobStatus = JobStatus.QUEUED
    params: Dict[str, Any] = Field(default_factory=dict)
    datasets_in: List[str] = Field(default_factory=list)
    datasets_out: List[str] = Field(default_factory=list)
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=_utc_now)
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

    @field_validator("id", mode="before")
    @classmethod
    def _job_id_validator(cls, value: str) -> str:
        return _validate_id(value, "JOB-")

    @field_validator("experiment_id", mode="before")
    @classmethod
    def _exp_id_validator(cls, value: str) -> str:
        return _validate_id(value, "EXP-")

    def start(self) -> None:
        self.status = JobStatus.RUNNING
        self.started_at = _utc_now()

    def finish(self, *, success: bool, outputs: Optional[List[str]] = None, error: str | None = None) -> None:
        self.finished_at = _utc_now()
        self.status = JobStatus.COMPLETED if success else JobStatus.FAILED
        if outputs:
            self.datasets_out = list(dict.fromkeys(outputs))
        self.error_message = error

    def attach_inputs(self, dataset_ids: List[str]) -> None:
        for ds in dataset_ids:
            if ds not in self.datasets_in:
                self.datasets_in.append(ds)

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump(mode="python")

    @classmethod
    def example(cls, idx: int = 1, experiment_id: str = "EXP-001") -> "Job":
        status = JobStatus.COMPLETED if idx == 1 else JobStatus.QUEUED
        return cls(
            id=f"JOB-{idx:03d}",
            experiment_id=experiment_id,
            kind="pchem:calorimetry",
            status=status,
            params={"phase": "Phase 0 skeleton"},
            datasets_in=["DS-001"],
        )
