"""Lightweight provenance helpers for LabOS Phase 0/1.

The helpers here are intentionally in-memory only. They allow other modules to
log relationships between imports, datasets, and experiments without assuming
any storage backend. The resulting structures can be displayed directly in the
UI or persisted by higher layers when available.
"""

from __future__ import annotations

from datetime import datetime
from typing import Iterable, Mapping

from .audit import AuditEvent


def link_import_to_experiment(
    experiment_id: str,
    dataset_id: str,
    actor: str | None = None,
    notes: Mapping[str, object] | None = None,
) -> AuditEvent:
    """Create an audit event linking an imported dataset to an experiment."""

    return AuditEvent(
        id=f"AUD-LINK-{dataset_id}-{experiment_id}",
        actor=actor or "unknown",
        action="link-dataset",
        target=experiment_id,
        details={
            "dataset_id": dataset_id,
            "experiment_id": experiment_id,
            "notes": dict(notes or {}),
        },
    )


def trace_dataset_lineage(
    dataset_id: str,
    audit_events: Iterable[AuditEvent | Mapping[str, object]] | None = None,
) -> dict[str, object]:
    """Summarize provenance from a list of audit events.

    This helper is deliberately simple: it scans the provided events for entries
    that mention the target dataset and returns a narrative-friendly structure
    containing the related experiment or import identifiers. It does not hit any
    persistence layer.
    """

    related_events = []
    for event in audit_events or []:
        if isinstance(event, AuditEvent):
            payload = event.to_dict()
        else:
            payload = dict(event)
        details = payload.get("details", {})
        if payload.get("target") == dataset_id or details.get("dataset_id") == dataset_id:
            related_events.append(payload)

    return {
        "dataset_id": dataset_id,
        "event_count": len(related_events),
        "events": related_events,
        "generated_at": datetime.utcnow().isoformat(),
    }

