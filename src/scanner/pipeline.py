"""Scanner pipeline skeleton with anchor integration."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from scanner.anchors import (
    AnchorResult,
    AnchorSpec,
    apply_anchor_overrides,
    resolve_anchors,
)


@dataclass(slots=True)
class PipelineInputs:
    frames_dir: Path
    metadata: dict
    scale_constraints: dict
    reference_frame: dict
    anchor_spec: Optional[AnchorSpec]
    output_dir: Path


def run_pipeline(inputs: PipelineInputs) -> AnchorResult:
    """Run the scanner pipeline stages relevant to anchors.

    This is a skeleton that wires anchor resolution into scale/reference
    handling and persists anchor results in pipeline artifacts.
    """

    anchor_result = _default_anchor_result()
    if inputs.anchor_spec:
        anchor_result = resolve_anchors(inputs.anchor_spec, inputs.frames_dir, inputs.metadata)
        updated_scale, updated_reference = apply_anchor_overrides(
            inputs.scale_constraints,
            inputs.reference_frame,
            anchor_result,
        )
        if updated_scale != inputs.scale_constraints or updated_reference != inputs.reference_frame:
            anchor_result.applied = True
        inputs.scale_constraints = updated_scale
        inputs.reference_frame = updated_reference

    _write_anchor_artifacts(inputs.output_dir, anchor_result)
    return anchor_result


def _default_anchor_result() -> AnchorResult:
    from scanner.anchors import AnchorConfidence, AnchorType

    return AnchorResult(
        resolved=False,
        applied=False,
        anchor_type=AnchorType.MARKER_BOARD,
        scale_factor=None,
        origin_xyz=None,
        rotation_quat_wxyz=None,
        confidence=AnchorConfidence.LOW,
        warnings=["No anchor specification provided."],
        evidence={},
        failure_reason="no_anchor_spec",
    )


def _write_anchor_artifacts(output_dir: Path, anchor_result: AnchorResult) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    run_path = output_dir / "run.json"
    metrics_path = output_dir / "reconstruction_metrics.json"

    _update_json(run_path, {"anchor_result": anchor_result.to_dict()})
    _update_json(metrics_path, {"anchor_result": anchor_result.to_dict()})


def _update_json(path: Path, updates: dict) -> None:
    data: dict[str, Any] = {}
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
    data.update(updates)
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
