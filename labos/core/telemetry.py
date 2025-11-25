"""Local telemetry helpers for LabOS.

This module intentionally keeps telemetry local to the developer machine. It
creates lightweight records that can later be shipped to another system if the
user explicitly opts in. No network calls are made here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
from uuid import uuid4

from ..config import LabOSConfig


@dataclass(slots=True)
class TelemetryEvent:
    """A simple telemetry event recorded locally.

    Attributes
    ----------
    event_id:
        Unique identifier for the telemetry entry.
    name:
        Human-readable event name (e.g., "experiment_started").
    payload:
        Arbitrary metadata describing the event context. Payload values should
        remain local-friendly (e.g., no secrets, tokens, or PHI).
    created_at:
        UTC timestamp when the event was created.
    """

    event_id: str
    name: str
    payload: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        """Convert the telemetry event to a serializable dictionary."""

        return {
            "event_id": self.event_id,
            "name": self.name,
            "payload": self.payload,
            "created_at": self.created_at.isoformat(),
        }


class TelemetryRecorder:
    """Local recorder that keeps telemetry in memory and optionally on disk."""

    def __init__(
        self,
        storage_path: Optional[Path] = None,
        persist: bool = True,
    ) -> None:
        cfg = LabOSConfig.load()
        self.storage_path = storage_path or cfg.feedback_dir / "telemetry-events.jsonl"
        self.persist = persist
        self._events: List[TelemetryEvent] = []
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

    @property
    def events(self) -> Iterable[TelemetryEvent]:
        """Return an iterable view of recorded events."""

        return tuple(self._events)

    def log_event(self, name: str, payload: Optional[Dict[str, Any]] = None) -> TelemetryEvent:
        """Record a telemetry event locally.

        Parameters
        ----------
        name:
            Event name such as "experiment_started" or "job_completed".
        payload:
            Additional structured metadata. Data should be safe to persist to a
            local file without leaking credentials or secrets.
        """

        if not name:
            raise ValueError("Telemetry event name is required")

        event = TelemetryEvent(event_id=f"TEL-{uuid4()}", name=name, payload=payload or {})
        self._events.append(event)

        if self.persist:
            serialized = json.dumps(event.to_dict(), sort_keys=True)
            with self.storage_path.open("a", encoding="utf-8") as handle:
                handle.write(serialized + "\n")

        return event

    def record_experiment_started(self, experiment_id: str, metadata: Optional[Dict[str, Any]] = None) -> TelemetryEvent:
        """Record that an experiment has started."""

        payload = {"experiment_id": experiment_id, **(metadata or {})}
        return self.log_event("experiment_started", payload)

    def record_experiment_completed(self, experiment_id: str, status: str = "completed", metadata: Optional[Dict[str, Any]] = None) -> TelemetryEvent:
        """Record that an experiment has completed."""

        payload = {"experiment_id": experiment_id, "status": status, **(metadata or {})}
        return self.log_event("experiment_completed", payload)

    def record_job_started(self, job_id: str, metadata: Optional[Dict[str, Any]] = None) -> TelemetryEvent:
        """Record that a job has started."""

        payload = {"job_id": job_id, **(metadata or {})}
        return self.log_event("job_started", payload)

    def record_job_completed(self, job_id: str, status: str = "completed", metadata: Optional[Dict[str, Any]] = None) -> TelemetryEvent:
        """Record that a job has completed."""

        payload = {"job_id": job_id, "status": status, **(metadata or {})}
        return self.log_event("job_completed", payload)

    def record_error(self, context: str, message: str, details: Optional[Dict[str, Any]] = None) -> TelemetryEvent:
        """Record an error event without transmitting it anywhere."""

        payload: Dict[str, Any] = {"context": context, "message": message}
        if details:
            payload["details"] = details
        return self.log_event("error", payload)


_default_recorder = TelemetryRecorder()


def log_event(name: str, payload: Optional[Dict[str, Any]] = None) -> TelemetryEvent:
    """Record a telemetry event using the default recorder."""

    return _default_recorder.log_event(name, payload)


def record_experiment_started(experiment_id: str, metadata: Optional[Dict[str, Any]] = None) -> TelemetryEvent:
    """Record that an experiment has started using the default recorder."""

    return _default_recorder.record_experiment_started(experiment_id, metadata)


def record_experiment_completed(experiment_id: str, status: str = "completed", metadata: Optional[Dict[str, Any]] = None) -> TelemetryEvent:
    """Record that an experiment has completed using the default recorder."""

    return _default_recorder.record_experiment_completed(experiment_id, status, metadata)


def record_job_started(job_id: str, metadata: Optional[Dict[str, Any]] = None) -> TelemetryEvent:
    """Record that a job has started using the default recorder."""

    return _default_recorder.record_job_started(job_id, metadata)


def record_job_completed(job_id: str, status: str = "completed", metadata: Optional[Dict[str, Any]] = None) -> TelemetryEvent:
    """Record that a job has completed using the default recorder."""

    return _default_recorder.record_job_completed(job_id, status, metadata)


def record_error(context: str, message: str, details: Optional[Dict[str, Any]] = None) -> TelemetryEvent:
    """Record an error using the default recorder."""

    return _default_recorder.record_error(context, message, details)


__all__ = [
    "TelemetryEvent",
    "TelemetryRecorder",
    "log_event",
    "record_error",
    "record_experiment_started",
    "record_experiment_completed",
    "record_job_started",
    "record_job_completed",
]
