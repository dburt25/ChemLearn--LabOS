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
    Lightweight reference to a dataset with versioning support.

    Phase 0:
    - We don't care where the data physically lives yet.
    - We just want a structured handle we can show in the UI and log.

    Phase 2.5.4:
    - Added semantic versioning (major.minor.patch)
    - Support for parent_version to track dataset evolution
    - Version bumping helpers for major/minor/patch updates

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
    version: str = "1.0.0"  # Semantic versioning: major.minor.patch
    parent_version: str | None = None  # Points to previous version if this is a revision

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("DatasetRef id is required")
        if any(ch.isspace() for ch in self.id):
            raise ValueError("DatasetRef id cannot include whitespace")
        self._validate_version()

    def _validate_version(self) -> None:
        """Validate semantic version format (major.minor.patch)."""
        parts = self.version.split(".")
        if len(parts) != 3:
            raise ValueError(f"Version must be in format 'major.minor.patch', got '{self.version}'")
        for part in parts:
            try:
                int(part)
            except ValueError:
                raise ValueError(f"Version components must be integers, got '{self.version}'")

    def bump_major(self) -> "DatasetRef":
        """Create new version with major increment (breaking changes)."""
        major, _, _ = map(int, self.version.split("."))
        new_version = f"{major + 1}.0.0"
        return self._create_next_version(new_version)

    def bump_minor(self) -> "DatasetRef":
        """Create new version with minor increment (new features, backward compatible)."""
        major, minor, _ = map(int, self.version.split("."))
        new_version = f"{major}.{minor + 1}.0"
        return self._create_next_version(new_version)

    def bump_patch(self) -> "DatasetRef":
        """Create new version with patch increment (bug fixes, corrections)."""
        major, minor, patch = map(int, self.version.split("."))
        new_version = f"{major}.{minor}.{patch + 1}"
        return self._create_next_version(new_version)

    def _create_next_version(self, new_version: str) -> "DatasetRef":
        """Helper to create next version with current as parent."""
        return DatasetRef(
            id=self.id,
            label=self.label,
            kind=self.kind,
            created_at=datetime.now(timezone.utc),
            path_hint=self.path_hint,
            metadata=dict(self.metadata),
            version=new_version,
            parent_version=self.version,
        )

    def get_version_tuple(self) -> tuple[int, int, int]:
        """Return version as (major, minor, patch) tuple for comparisons."""
        return tuple(map(int, self.version.split(".")))  # type: ignore

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "kind": self.kind,
            "created_at": self.created_at.isoformat(),
            "path_hint": self.path_hint,
            "metadata": dict(self.metadata),
            "version": self.version,
            "parent_version": self.parent_version,
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
                version=str(payload.get("version", "1.0.0")),
                parent_version=payload.get("parent_version"),
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
