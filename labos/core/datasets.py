# labos/core/datasets.py

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict


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
    def example(cls, idx: int = 1, kind: str = "table") -> "DatasetRef":
        return cls(
            id=f"DS-{idx:03d}",
            label=f"Example Dataset {idx}",
            kind=kind,
            path_hint=f"data/phase0_example_{idx}.csv",
            metadata={"phase": "Phase 0 skeleton"},
        )
