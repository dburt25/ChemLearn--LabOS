"""Job model with dataset lineage hooks and lifecycle helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


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

def _params_factory() -> Dict[str, Any]:
    return {}


def _dataset_list_factory() -> List[str]:
    return []

@dataclass(slots=True)
class Job:
    """Phase 0 job record with start/finish helpers."""

    id: str
    experiment_id: str
    kind: str
    status: JobStatus = JobStatus.QUEUED
    params: Dict[str, Any] = field(default_factory=_params_factory)
    datasets_in: List[str] = field(default_factory=_dataset_list_factory)
    datasets_out: List[str] = field(default_factory=_dataset_list_factory)
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=_utc_now)
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        self.id = _validate_id(self.id, "JOB-")
        self.experiment_id = _validate_id(self.experiment_id, "EXP-")

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
        return asdict(self)

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
