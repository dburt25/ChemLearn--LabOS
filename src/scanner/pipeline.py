"""Simple scanning pipeline with marker-board anchoring."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from scanner.anchors import FrameData, resolve_marker_board_anchor, write_anchor_artifacts
from scanner.board import BoardSpec
from scanner.intrinsics import Intrinsics, load_intrinsics_json, parse_intrinsics_string
from scanner.quality_gates import QualityGateConfig


SUPPORTED_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".tiff", ".bmp"}


def _load_cv2():
    try:
        import cv2  # type: ignore
    except ModuleNotFoundError as exc:  # pragma: no cover - env dependent
        raise RuntimeError("OpenCV is required to load frames.") from exc
    return cv2


def load_frames_from_dir(frames_dir: str | Path) -> list[FrameData]:
    frames_path = Path(frames_dir)
    if not frames_path.exists():
        raise FileNotFoundError(f"Frames directory not found: {frames_path}")
    cv2 = _load_cv2()
    frames: list[FrameData] = []
    for index, path in enumerate(sorted(frames_path.iterdir())):
        if path.suffix.lower() not in SUPPORTED_IMAGE_SUFFIXES:
            continue
        image = cv2.imread(str(path))
        frames.append(FrameData(index=index, image=image, timestamp=None))
    return frames


def load_board_spec(path: Optional[str], overrides: dict) -> Optional[BoardSpec]:
    if path:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        return BoardSpec.from_dict(payload)
    if overrides:
        return BoardSpec.from_dict(overrides)
    return None


def load_intrinsics(path: Optional[str], intrinsics_value: Optional[str], dist_value: Optional[str]) -> Optional[Intrinsics]:
    if path:
        return load_intrinsics_json(path)
    if intrinsics_value:
        return parse_intrinsics_string(intrinsics_value, dist_value)
    return None


def run_pipeline(
    frames_dir: str,
    output_dir: str,
    anchor_type: str,
    board_spec_path: Optional[str],
    board_overrides: dict,
    intrinsics_path: Optional[str],
    intrinsics_value: Optional[str],
    dist_value: Optional[str],
    gate_config: QualityGateConfig,
    frame_step: int,
) -> None:
    frames = load_frames_from_dir(frames_dir)
    board_spec = load_board_spec(board_spec_path, board_overrides)
    intrinsics = load_intrinsics(intrinsics_path, intrinsics_value, dist_value)

    if anchor_type == "marker_board":
        anchor_result, poses = resolve_marker_board_anchor(
            frames,
            board_spec,
            intrinsics,
            gate_config,
            frame_step=frame_step,
        )
    else:
        raise ValueError(f"Unsupported anchor type: {anchor_type}")

    write_anchor_artifacts(output_dir, anchor_result, poses)
