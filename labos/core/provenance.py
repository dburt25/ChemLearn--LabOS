"""Provenance helper utilities for jobs, datasets, and audit chains."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional

from .audit import AuditEvent
from .datasets import DatasetRef


def _timestamp_id(prefix: str) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    return f"{prefix}-{ts}"


def link_job_to_dataset(job_id: str, dataset_id: str, direction: str = "out") -> AuditEvent:
    """Create an audit event linking a job to a dataset reference."""

    if direction not in {"in", "out"}:
        raise ValueError("direction must be 'in' or 'out'")

    return AuditEvent(
        id=_timestamp_id("AUD-LINK"),
        actor="system",
        action="link-dataset",
        target=job_id,
        details={"dataset_id": dataset_id, "direction": direction},
    )


def register_import_result(
    experiment_id: Optional[str], job_id: Optional[str], dataset_ref: DatasetRef
) -> Dict[str, object]:
    """Prepare provenance records for an imported dataset.

    Returns a dictionary containing the dataset, generated audit events, and
    linkage hints that calling code can persist if desired.
    """

    events: List[AuditEvent] = []

    dataset_event = AuditEvent(
        id=_timestamp_id("AUD-DATASET"),
        actor=dataset_ref.metadata.get("imported_by", "unknown"),
        action="register-dataset",
        target=dataset_ref.id,
        details={
            "experiment_id": experiment_id,
            "job_id": job_id,
            "module_key": dataset_ref.metadata.get("module_key"),
            "path_hint": dataset_ref.path_hint,
        },
    )
    events.append(dataset_event)

    if job_id:
        events.append(link_job_to_dataset(job_id, dataset_ref.id, direction="out"))

    if experiment_id:
        events.append(
            AuditEvent(
                id=_timestamp_id("AUD-EXP"),
                actor="system",
                action="link-dataset",
                target=experiment_id,
                details={"dataset_id": dataset_ref.id, "job_id": job_id},
            )
        )

    return {
        "dataset": dataset_ref.to_dict(),
        "audit_events": [event.to_dict() for event in events],
        "links": {
            "job_id": job_id,
            "experiment_id": experiment_id,
            "dataset_id": dataset_ref.id,
        },
    }
