# labos/core/jobs.py

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Literal


JobStatus = Literal["queued", "running", "completed", "failed"]


@dataclass
class Job:
    """
    Minimal job record.

    Each serious LabOS computation will later be represented as a Job
    with:
    - an ID
    - parameters
    - timestamps
    - status
    - links to input/output datasets

    Phase 0: just enough structure to display in the UI and evolve later.
    """

    id: str
    experiment_id: str
    kind: str
    status: JobStatus = "queued"
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: datetime | None = None
    finished_at: datetime | None = None
    params: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "experiment_id": self.experiment_id,
            "kind": self.kind,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "params": self.params,
        }

    @classmethod
    def example(cls, idx: int = 1, experiment_id: str = "EXP-001") -> "Job":
        return cls(
            id=f"JOB-{idx:03d}",
            experiment_id=experiment_id,
            kind="pchem:calorimetry",
            status="completed" if idx == 1 else "queued",
            params={"phase": "Phase 0 skeleton"},
        )
