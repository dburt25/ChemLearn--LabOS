from __future__ import annotations

import json
import os
import platform
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

from scanner.backends.backend_base import ReconstructionResult
from scanner.frames import FrameExtractionResult
from scanner.ingest import IngestResult
from scanner.metadata import MetadataResult


def build_run_report(
    *,
    ingest: IngestResult,
    metadata: MetadataResult,
    frames: FrameExtractionResult,
    backend: str,
    params: dict[str, Any],
    reconstruction: ReconstructionResult | None,
    failure_reason: str | None,
    elapsed_seconds: float,
) -> dict[str, Any]:
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "path": str(ingest.input_path),
            "sha256": ingest.input_hash,
        },
        "output_dir": str(ingest.output_dir),
        "backend": backend,
        "params": params,
        "metadata": asdict(metadata),
        "frames": asdict(frames),
        "reconstruction": {
            "sparse_model_dir": str(reconstruction.sparse_model_dir)
            if reconstruction and reconstruction.sparse_model_dir
            else None,
            "backend_log": reconstruction.backend_log if reconstruction else None,
            "status": "success" if reconstruction and not failure_reason else "failed",
            "failure_reason": failure_reason,
        },
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "cpu_count": os.cpu_count(),
        },
        "versions": {
            "scanner": "0.1.0",
        },
        "elapsed_seconds": elapsed_seconds,
    }


def build_metrics_report(
    *,
    reconstruction: ReconstructionResult | None,
    metadata: MetadataResult,
    frame_result: FrameExtractionResult,
    failure_reason: str | None,
) -> dict[str, Any]:
    points3d_path = None
    reprojection_errors: list[float] = []
    point_count = 0

    if reconstruction and reconstruction.sparse_model_dir:
        points3d_path = Path(reconstruction.sparse_model_dir) / "points3D.txt"
        if points3d_path.exists():
            reprojection_errors = _parse_reprojection_errors(points3d_path)
            point_count = len(reprojection_errors)

    return {
        "status": "success" if reconstruction and not failure_reason else "failed",
        "failure_reason": failure_reason,
        "frame_usage": {
            "extracted": frame_result.frame_count,
            "used": frame_result.frame_count,
        },
        "point_count": point_count,
        "reprojection_error": {
            "mean": mean(reprojection_errors) if reprojection_errors else None,
            "min": min(reprojection_errors) if reprojection_errors else None,
            "max": max(reprojection_errors) if reprojection_errors else None,
        },
        "scale_confidence": classify_scale_confidence(metadata),
        "accuracy_tiers": {
            "tier_s_target_mm": 0.01,
            "tier_r_target_mm": 1.0,
            "tier_a_target_cm": 10.0,
            "phase0_disclaimer": "Phase 0 does not meet target precision tiers.",
        },
    }


def classify_scale_confidence(metadata: MetadataResult) -> str:
    if "streams.width" not in metadata.extracted_fields or "streams.height" not in metadata.extracted_fields:
        return "low"
    if metadata.source == "ffprobe":
        tags = {}
        for stream in metadata.streams:
            tags.update(stream.get("tags", {}) or {})
        tags.update(metadata.container.get("tags", {}) or {})
        if any(key.lower().startswith("com.apple") for key in tags.keys()):
            return "medium"
        if any("focal" in key.lower() for key in tags.keys()):
            return "medium"
    return "low"


def _parse_reprojection_errors(points_path: Path) -> list[float]:
    errors: list[float] = []
    with points_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.startswith("#"):
                continue
            parts = line.strip().split()
            if len(parts) < 8:
                continue
            try:
                errors.append(float(parts[7]))
            except ValueError:
                continue
    return errors


def write_json_report(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
