# labos/core/datasets.py

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Mapping


logger = logging.getLogger(__name__)


@dataclass
class DatasetRef:
    """
    Lightweight reference to a dataset.

    Phase 0:
    - We don't care where the data physically lives yet.
    - We just want a structured handle we can show in the UI and log.

    Later:
    - This will point to files, DB tables, or remote storage locations.
    - We'll add schema info, provenance, and validation metadata.
    """

    id: str
    label: str
    kind: str = "table"  # e.g. "table", "spectrum", "timeseries"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    path_hint: str | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("DatasetRef id is required")
        if any(ch.isspace() for ch in self.id):
            raise ValueError("DatasetRef id cannot include whitespace")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "kind": self.kind,
            "created_at": self.created_at.isoformat(),
            "path_hint": self.path_hint,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "DatasetRef | None":
        required = {"id", "label", "created_at"}
        missing = sorted(required - payload.keys())
        if missing:
            logger.warning("Skipping dataset payload missing keys: %s", ", ".join(missing))
            return None

        try:
            created_at_raw = payload["created_at"]
            created_at = created_at_raw if isinstance(created_at_raw, datetime) else datetime.fromisoformat(str(created_at_raw))
        except Exception as exc:
            logger.warning("Skipping dataset %s due to timestamp error: %s", payload.get("id", "<unknown>"), exc)
            return None

        try:
            return cls(
                id=str(payload["id"]),
                label=str(payload["label"]),
                kind=str(payload.get("kind", "table")),
                created_at=created_at,
                path_hint=payload.get("path_hint"),
                metadata=dict(payload.get("metadata") or {}),
            )
        except Exception as exc:
            logger.warning("Skipping dataset %s due to validation error: %s", payload.get("id", "<unknown>"), exc)
            return None

    @classmethod
    def example(cls, idx: int = 1, kind: str = "table") -> "DatasetRef":
        return cls(
            id=f"DS-{idx:03d}",
            label=f"Example Dataset {idx}",
            kind=kind,
            path_hint=f"data/phase0_example_{idx}.csv",
            metadata={"phase": "Phase 0 skeleton"},
        )
