"""Lightweight orchestration helpers for experiments, jobs, and datasets."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from .audit import AuditEvent
from .datasets import DatasetRef
from .experiments import Experiment
from .jobs import Job


def _utc_now() -> datetime:
    """Return timezone-aware UTC now to align with other core models."""

    return datetime.now(timezone.utc)


def create_experiment_with_job(
    *,
    experiment_id: str,
    experiment_name: str,
    job_id: str,
    job_kind: str,
    owner: str = "local-user",
    mode: str = "Lab",
    experiment_metadata: Optional[Dict[str, object]] = None,
    job_params: Optional[Dict[str, object]] = None,
    job_datasets_in: Optional[List[str]] = None,
) -> Tuple[Experiment, Job]:
    """Create a paired ``Experiment`` and ``Job`` with consistent IDs.

    This helper keeps setup code concise for quick prototyping or UI wiring.
    It mirrors the default field choices of the underlying dataclasses while
    allowing overrides for owner/mode/params.
    """

    experiment = Experiment(
        id=experiment_id,
        name=experiment_name,
        owner=owner,
        mode=mode,
        metadata=dict(experiment_metadata or {}),
    )

    job = Job(
        id=job_id,
        experiment_id=experiment.id,
        kind=job_kind,
        params=dict(job_params or {}),
        datasets_in=list(job_datasets_in or []),
    )

    experiment.add_job(job.id)
    return experiment, job


def attach_dataset_to_job(job: Job, dataset_id: str, direction: str = "out") -> None:
    """Attach a dataset reference to a job input or output list.

    Args:
        job: Job to be updated.
        dataset_id: Dataset identifier (e.g., ``"DS-001"``).
        direction: "in" or "out" to target ``datasets_in`` or ``datasets_out``.
    """

    if direction not in {"in", "out"}:
        raise ValueError("direction must be either 'in' or 'out'")

    target = job.datasets_in if direction == "in" else job.datasets_out
    if dataset_id not in target:
        target.append(dataset_id)


def log_event_for_job(
    job: Job,
    action: str,
    details: Optional[Dict[str, object]] = None,
    *,
    actor: str = "local-system",
    event_id: Optional[str] = None,
    dataset: Optional[DatasetRef] = None,
) -> AuditEvent:
    """Create an ``AuditEvent`` describing an action against a job.

    If ``event_id`` is not supplied, a timestamp-based identifier is
    generated with the ``AUD-`` prefix to maintain a consistent shape
    with other audit helpers.
    """

    timestamp_ms = int(_utc_now().timestamp() * 1000)
    resolved_event_id = event_id or f"AUD-{timestamp_ms}"

    payload: Dict[str, object] = {"job_id": job.id, "experiment_id": job.experiment_id}
    payload.update(details or {})
    if dataset:
        payload["dataset_id"] = dataset.id

    return AuditEvent(
        id=resolved_event_id,
        actor=actor,
        action=action,
        target=job.id,
        created_at=_utc_now().replace(tzinfo=None),
        details=payload,
    )
