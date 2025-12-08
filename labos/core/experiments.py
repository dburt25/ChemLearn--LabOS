"""Experiment record with lifecycle state and job linkage."""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Mapping


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
        raise ValueError(f"Experiment IDs must start with `{prefix}`; received {value!r}")
    if any(ch.isspace() for ch in value):
        raise ValueError("Experiment IDs cannot contain whitespace")
    return value


class ExperimentStatus(str, Enum):
    DRAFT = "draft"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"


# Valid state transitions for experiment lifecycle
VALID_TRANSITIONS: Dict[ExperimentStatus, List[ExperimentStatus]] = {
    ExperimentStatus.DRAFT: [ExperimentStatus.RUNNING, ExperimentStatus.ARCHIVED],
    ExperimentStatus.RUNNING: [ExperimentStatus.COMPLETED, ExperimentStatus.FAILED, ExperimentStatus.ARCHIVED],
    ExperimentStatus.COMPLETED: [ExperimentStatus.ARCHIVED],
    ExperimentStatus.FAILED: [ExperimentStatus.ARCHIVED, ExperimentStatus.DRAFT],  # Allow retry from failure
    ExperimentStatus.ARCHIVED: [],  # Terminal state
}


class InvalidStateTransitionError(ValueError):
    """Raised when attempting an invalid experiment status transition."""
    pass


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

    def update_status(self, new_status: ExperimentStatus) -> None:
        """Update experiment status with transition validation.
        
        Args:
            new_status: Target status
            
        Raises:
            InvalidStateTransitionError: If transition is not allowed
        """
        if new_status == self.status:
            return  # No-op if already at target status
            
        valid_targets = VALID_TRANSITIONS.get(self.status, [])
        if new_status not in valid_targets:
            raise InvalidStateTransitionError(
                f"Invalid transition from {self.status.value} to {new_status.value}. "
                f"Valid transitions: {[s.value for s in valid_targets]}"
            )
        
        self.status = new_status
        self.updated_at = _utc_now()

    def mark_running(self) -> None:
        """Transition experiment to RUNNING status."""
        self.update_status(ExperimentStatus.RUNNING)

    def mark_completed(self) -> None:
        """Transition experiment to COMPLETED status."""
        self.update_status(ExperimentStatus.COMPLETED)

    def mark_failed(self) -> None:
        """Transition experiment to FAILED status."""
        self.update_status(ExperimentStatus.FAILED)

    def mark_archived(self) -> None:
        """Transition experiment to ARCHIVED status (terminal)."""
        self.update_status(ExperimentStatus.ARCHIVED)

    def is_finished(self) -> bool:
        """Check if experiment is in terminal state."""
        return self.status in {ExperimentStatus.COMPLETED, ExperimentStatus.FAILED}
    
    def is_active(self) -> bool:
        """Check if experiment can accept new jobs."""
        return self.status in {ExperimentStatus.DRAFT, ExperimentStatus.RUNNING}

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
    def from_dict(cls, payload: Mapping[str, Any]) -> "Experiment | None":
        required = {"id", "name", "created_at", "updated_at"}
        missing = sorted(required - payload.keys())
        if missing:
            logger.warning("Skipping experiment payload missing keys: %s", ", ".join(missing))
            return None

        try:
            created_at = _parse_datetime(payload["created_at"])
            updated_at = _parse_datetime(payload["updated_at"])
        except Exception as exc:
            logger.warning("Skipping experiment %s due to timestamp error: %s", payload.get("id", "<unknown>"), exc)
            return None

        try:
            return cls(
                id=str(payload["id"]),
                name=str(payload["name"]),
                owner=str(payload.get("owner", "local-user")),
                mode=payload.get("mode", ExperimentMode.LAB),
                status=payload.get("status", ExperimentStatus.DRAFT),
                metadata=dict(payload.get("metadata") or {}),
                jobs=list(payload.get("jobs") or []),
                created_at=created_at,
                updated_at=updated_at,
            )
        except Exception as exc:
            logger.warning("Skipping experiment %s due to validation error: %s", payload.get("id", "<unknown>"), exc)
            return None

    @classmethod
    def example(cls, idx: int = 1, mode: str = "Lab") -> "Experiment":
        return cls(
            id=f"EXP-{idx:03d}",
            name=f"Example Experiment {idx}",
            owner="phase0",
            mode=mode,
            metadata={"phase": "Phase 0 skeleton"},
        )
