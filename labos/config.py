"""Configuration loading utilities for ChemLearn LabOS."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
from typing import Optional

from .core.utils import utc_now


@dataclass(slots=True)
class LabOSConfig:
    """Represents runtime configuration for registry and audit storage."""

    root_dir: Path
    data_dir: Path
    audit_dir: Path
    experiments_dir: Path
    jobs_dir: Path
    datasets_dir: Path
    examples_dir: Path
    feedback_dir: Path

    @classmethod
    def load(cls, root: Optional[Path] = None) -> "LabOSConfig":
        """Load configuration from environment variables and defaults."""

        root_dir = root or Path(os.getenv("LABOS_ROOT", Path.cwd())).resolve()
        data_dir = Path(os.getenv("LABOS_DATA_DIR", root_dir / "data")).resolve()
        cfg = cls(
            root_dir=root_dir,
            data_dir=data_dir,
            audit_dir=Path(os.getenv("LABOS_AUDIT_DIR", data_dir / "audit")).resolve(),
            experiments_dir=Path(os.getenv("LABOS_EXPERIMENT_DIR", data_dir / "experiments")).resolve(),
            jobs_dir=Path(os.getenv("LABOS_JOB_DIR", data_dir / "jobs")).resolve(),
            datasets_dir=Path(os.getenv("LABOS_DATASET_DIR", data_dir / "datasets")).resolve(),
            examples_dir=Path(os.getenv("LABOS_EXAMPLES_DIR", data_dir / "examples")).resolve(),
            feedback_dir=Path(os.getenv("LABOS_FEEDBACK_DIR", data_dir / "feedback")).resolve(),
        )
        cfg.ensure_directories()
        return cfg

    def ensure_directories(self) -> None:
        """Create directories when they do not yet exist."""

        for directory in (
            self.data_dir,
            self.audit_dir,
            self.experiments_dir,
            self.jobs_dir,
            self.datasets_dir,
            self.examples_dir,
            self.feedback_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)

    def timestamped_path(self, base_dir: Path, stem: str, suffix: str = "json") -> Path:
        """Return a path under *base_dir* with a UTC timestamp to avoid collisions."""

        ts = utc_now().replace(":", "-")
        return base_dir / f"{stem}-{ts}.{suffix}"
