# labos/core/experiments.py

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class Experiment:
    """
    Minimal experiment record.

    Phase 0 goals:
    - Keep this simple: good for UI display, logs, and tests.
    - Make it trivial to extend later with status, lineage, and links to Jobs/Datasets.

    This is intentionally NOT tied to a DB yet.
    """

    id: str
    name: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    owner: str = "local-user"
    metadata: Dict[str, Any] = field(default_factory=dict)
    mode: str = "Lab"  # "Learner" / "Lab" / "Builder"

    def short_label(self) -> str:
        return f"{self.id} — {self.name}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "owner": self.owner,
            "metadata": self.metadata,
            "mode": self.mode,
        }

    @classmethod
    def example(cls, idx: int = 1, mode: str = "Lab") -> "Experiment":
        return cls(
            id=f"EXP-{idx:03d}",
            name=f"Example Experiment {idx}",
            mode=mode,
            metadata={"phase": "Phase 0 skeleton"},
        )
