from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from scanner.metadata import MetadataResult


class BackendUnavailableError(RuntimeError):
    """Raised when a backend dependency is missing."""


@dataclass(frozen=True)
class ReconstructionResult:
    sparse_model_dir: Path | None
    backend_log: str | None


class BackendBase(Protocol):
    name: str

    def run(
        self,
        *,
        images_dir: Path,
        workspace_dir: Path,
        metadata: MetadataResult,
        logger,
    ) -> ReconstructionResult:
        ...


def get_backend(name: str) -> BackendBase:
    if name.lower() == "colmap":
        from scanner.backends.colmap_backend import ColmapBackend

        return ColmapBackend()
    raise BackendUnavailableError(f"Unsupported backend '{name}'.")
