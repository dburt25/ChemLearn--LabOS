from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path

from scanner.backends.backend_base import BackendUnavailableError, ReconstructionResult
from scanner.metadata import MetadataResult
from scanner.utils import safe_mkdir


class ColmapBackend:
    name = "colmap"

    def run(
        self,
        *,
        images_dir: Path,
        workspace_dir: Path,
        metadata: MetadataResult,
        logger: logging.Logger,
    ) -> ReconstructionResult:
        if shutil.which("colmap") is None:
            raise BackendUnavailableError(
                "COLMAP is not installed or not on PATH. "
                "Install COLMAP (https://colmap.github.io/) and retry."
            )

        safe_mkdir(workspace_dir)
        database_path = workspace_dir / "database.db"
        sparse_dir = workspace_dir / "sparse"
        safe_mkdir(sparse_dir)
        log_path = workspace_dir / "colmap.log"

        commands = [
            [
                "colmap",
                "feature_extractor",
                "--database_path",
                str(database_path),
                "--image_path",
                str(images_dir),
            ],
            [
                "colmap",
                "exhaustive_matcher",
                "--database_path",
                str(database_path),
            ],
            [
                "colmap",
                "mapper",
                "--database_path",
                str(database_path),
                "--image_path",
                str(images_dir),
                "--output_path",
                str(sparse_dir),
            ],
        ]

        with log_path.open("w", encoding="utf-8") as log_file:
            for command in commands:
                logger.info(
                    "Running COLMAP",
                    extra={"context": {"command": " ".join(command)}},
                )
                try:
                    subprocess.run(command, check=True, stdout=log_file, stderr=log_file)
                except subprocess.CalledProcessError as exc:
                    raise RuntimeError(
                        f"COLMAP command failed: {' '.join(command)} (exit {exc.returncode})"
                    ) from exc

        sparse_model_dir = _find_sparse_model(sparse_dir)
        if sparse_model_dir is None:
            raise RuntimeError("COLMAP did not produce a sparse model directory.")

        return ReconstructionResult(sparse_model_dir=sparse_model_dir, backend_log=str(log_path))


def _find_sparse_model(sparse_dir: Path) -> Path | None:
    if not sparse_dir.exists():
        return None
    for candidate in sorted(sparse_dir.iterdir()):
        if candidate.is_dir():
            return candidate
    return None
