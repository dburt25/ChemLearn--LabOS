"""Scanner pipeline entrypoints with anchor integration."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from scanner.anchor_types import AnchorResult, AnchorSpec, ScanRegime
from scanner.anchors import resolve_anchors
from scanner.reference_frame import apply_reference_frame
from scanner.scale_constraints import apply_scale_constraints


def run_pipeline(
    *,
    frames_dir: Path,
    output_dir: Path,
    metadata_path: Path | None,
    anchor_spec: AnchorSpec | None,
    regime: ScanRegime,
    marker_frames_max: int | None,
) -> dict[str, Any]:
    frames_dir = Path(frames_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    metadata = _load_metadata(metadata_path)

    anchor_result: AnchorResult | None = None
    if anchor_spec is not None:
        anchor_result = resolve_anchors(
            anchor_spec,
            frames_dir,
            metadata,
            marker_frames_max=marker_frames_max,
        )

    reconstruction = _run_reconstruction_stub(frames_dir, metadata)

    scale_result = apply_scale_constraints(reconstruction, metadata, anchor_result)
    reference_result = apply_reference_frame(reconstruction, metadata, anchor_result)

    if anchor_result and (
        scale_result["source"] == "anchor" or reference_result["source"] == "anchor"
    ):
        anchor_result.applied = True

    notes = []
    if scale_result["source"] == "anchor":
        notes.append("Anchor-derived scale_factor overrides heuristics.")
    if reference_result["source"] == "anchor":
        notes.append("Anchor-derived origin overrides centering heuristics.")

    run_record = {
        "regime": regime.value,
        "frames_dir": str(frames_dir),
        "metadata_path": str(metadata_path) if metadata_path else None,
        "anchor_result": _serialize_anchor_result(anchor_result),
        "scale_constraints": scale_result,
        "reference_frame": reference_result,
        "notes": notes,
    }

    _write_json(output_dir / "run.json", run_record)
    _write_json(
        output_dir / "reconstruction_metrics.json",
        {
            "anchor_result": _serialize_anchor_result(anchor_result),
            "scale_constraints": scale_result,
            "reference_frame": reference_result,
        },
    )

    return run_record


def _serialize_anchor_result(anchor_result: AnchorResult | None) -> dict[str, Any] | None:
    if anchor_result is None:
        return None
    payload = asdict(anchor_result)
    payload["anchor_type"] = anchor_result.anchor_type.value
    payload["confidence"] = anchor_result.confidence.value
    return payload


def _run_reconstruction_stub(frames_dir: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "stub",
        "frames_count": len(list(frames_dir.iterdir())) if frames_dir.exists() else 0,
        "notes": [
            "Reconstruction pipeline not implemented in LabOS; this is a placeholder.",
        ],
    }


def _load_metadata(metadata_path: Path | None) -> dict[str, Any]:
    if metadata_path is None:
        return {}
    metadata_path = Path(metadata_path)
    if not metadata_path.exists():
        return {}
    with metadata_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
