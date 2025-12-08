"""Job model with dataset lineage hooks and lifecycle helpers."""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Mapping, Optional, Sequence


logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    raise ValueError(f"Unsupported datetime value: {value!r}")


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
    """Phase 0 job record with start/finish helpers and retry support."""

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
    max_retries: int = 3
    retry_count: int = 0

    def __post_init__(self) -> None:
        self.id = _validate_id(self.id, "JOB-")
        self.experiment_id = _validate_id(self.experiment_id, "EXP-")
        if isinstance(self.status, str):
            self.status = JobStatus(self.status)

    def start(self) -> None:
        self.status = JobStatus.RUNNING
        self.started_at = _utc_now()

    def finish(self, *, success: bool, outputs: Optional[List[str]] = None, error: str | None = None) -> None:
        self.finished_at = _utc_now()
        self.status = JobStatus.COMPLETED if success else JobStatus.FAILED
        if outputs:
            self.datasets_out = list(dict.fromkeys(outputs))
        self.error_message = error

    def is_finished(self) -> bool:
        return self.status in {JobStatus.COMPLETED, JobStatus.FAILED}

    def mark_started(self) -> None:
        """Alias for `start` to align with lifecycle language."""

        self.start()

    def mark_finished(self, *, success: bool, outputs: Optional[List[str]] = None, error: str | None = None) -> None:
        """Alias for `finish` with clearer naming."""

        self.finish(success=success, outputs=outputs, error=error)

    def attach_inputs(self, dataset_ids: List[str]) -> None:
        for ds in dataset_ids:
            if ds not in self.datasets_in:
                self.datasets_in.append(ds)

    def can_retry(self) -> bool:
        """Check if job can be retried."""
        return self.retry_count < self.max_retries and self.status == JobStatus.FAILED

    def retry(self) -> None:
        """Retry a failed job.
        
        Raises:
            ValueError: If job cannot be retried (not failed or max retries exceeded)
        """
        if self.status != JobStatus.FAILED:
            raise ValueError(f"Cannot retry job in status {self.status.value}. Only FAILED jobs can be retried.")
        
        if self.retry_count >= self.max_retries:
            raise ValueError(f"Max retries ({self.max_retries}) exceeded for job {self.id}")
        
        self.retry_count += 1
        self.status = JobStatus.QUEUED
        self.error_message = None
        self.started_at = None
        self.finished_at = None

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["status"] = self.status.value
        payload["created_at"] = self.created_at.isoformat()
        payload["started_at"] = self.started_at.isoformat() if self.started_at else None
        payload["finished_at"] = self.finished_at.isoformat() if self.finished_at else None
        return payload

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "Job | None":
        required = {"id", "experiment_id", "kind", "status", "created_at"}
        missing = sorted(required - payload.keys())
        if missing:
            logger.warning("Skipping job payload missing keys: %s", ", ".join(missing))
            return None

        try:
            created_at = _parse_datetime(payload["created_at"])
            started_at = (
                _parse_datetime(payload["started_at"])
                if payload.get("started_at") is not None
                else None
            )
            finished_at = (
                _parse_datetime(payload["finished_at"])
                if payload.get("finished_at") is not None
                else None
            )
        except Exception as exc:
            logger.warning("Skipping job %s due to timestamp error: %s", payload.get("id", "<unknown>"), exc)
            return None

        try:
            return cls(
                id=str(payload["id"]),
                experiment_id=str(payload["experiment_id"]),
                kind=str(payload["kind"]),
                status=payload.get("status", JobStatus.QUEUED),
                params=dict(payload.get("params") or {}),
                datasets_in=list(payload.get("datasets_in") or []),
                datasets_out=list(payload.get("datasets_out") or []),
                error_message=payload.get("error_message"),
                created_at=created_at,
                started_at=started_at,
                finished_at=finished_at,
                max_retries=int(payload.get("max_retries", 3)),
                retry_count=int(payload.get("retry_count", 0)),
            )
        except Exception as exc:
            logger.warning("Skipping job %s due to validation error: %s", payload.get("id", "<unknown>"), exc)
            return None

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


def list_jobs_for_experiment(jobs: Sequence[Job], experiment_id: str) -> List[Job]:
    return [job for job in jobs if job.experiment_id == experiment_id]
