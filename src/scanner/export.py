from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path


def export_sparse_ply(sparse_model_dir: Path, output_dir: Path, logger: logging.Logger) -> Path:
    if shutil.which("colmap") is None:
        raise RuntimeError("COLMAP is required to export PLY from the sparse model.")

    output_path = output_dir / "sparse.ply"
    command = [
        "colmap",
        "model_converter",
        "--input_path",
        str(sparse_model_dir),
        "--output_path",
        str(output_path),
        "--output_type",
        "PLY",
    ]
    logger.info(
        "Exporting PLY", extra={"context": {"command": " ".join(command)}}
    )
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError("COLMAP model_converter failed") from exc
    return output_path


def export_obj(_: Path, __: Path) -> None:
    raise NotImplementedError("OBJ export will be added in a future phase.")


def export_gltf(_: Path, __: Path) -> None:
    raise NotImplementedError("glTF export will be added in a future phase.")
