"""Pipeline helpers for applying reference frame centering."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Optional, Sequence

from scanner.reference_frame import AnchorInputs, ReferenceFrame, select_reference_frame, translate_points


def write_ply(path: Path, points: Iterable[Sequence[float]]) -> None:
    pts = list(points)
    header = [
        "ply",
        "format ascii 1.0",
        f"element vertex {len(pts)}",
        "property float x",
        "property float y",
        "property float z",
        "end_header",
    ]
    body = [f"{p[0]} {p[1]} {p[2]}" for p in pts]
    path.write_text("\n".join(header + body) + "\n", encoding="utf-8")


def _reference_frame_payload(reference_frame: ReferenceFrame, anchors: AnchorInputs) -> dict[str, object]:
    payload = reference_frame.to_dict()
    payload["anchors"] = anchors.to_dict()
    return payload


def run_pipeline(
    output_dir: Path,
    anchors: AnchorInputs,
    *,
    point_cloud: Optional[Sequence[Sequence[float]]] = None,
    dense: bool = False,
    anchor_mode: str = "auto",
) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    reference_frame = select_reference_frame(point_cloud, anchors, anchor_mode=anchor_mode)

    centered_path: Optional[str] = None
    if reference_frame.origin_xyz and point_cloud:
        centered = translate_points(point_cloud, reference_frame.origin_xyz)
        filename = "dense_scaled_centered.ply" if dense else "scene_sparse_scaled_centered.ply"
        centered_path = str(output_dir / filename)
        write_ply(Path(centered_path), centered)

    reference_payload = _reference_frame_payload(reference_frame, anchors)
    (output_dir / "reference_frame.json").write_text(
        json.dumps(reference_payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    run_payload = {
        "reference_frame": reference_payload,
        "centered_point_cloud": centered_path,
    }
    (output_dir / "run.json").write_text(
        json.dumps(run_payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return run_payload
