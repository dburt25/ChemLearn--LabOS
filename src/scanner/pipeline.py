"""Scanner pipeline entrypoints."""

from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np

from scanner.anchors import AnchorResult, AnchorType, resolve_marker_board_anchor
from scanner.board import BoardSpec
from scanner.intrinsics import Intrinsics
from scanner.quality_gates import QualityGateConfig

_cv2_spec = importlib.util.find_spec("cv2")
if _cv2_spec:
    import cv2


@dataclass(frozen=True)
class PipelineConfig:
    anchor_type: AnchorType
    board_spec: BoardSpec
    intrinsics: Optional[Intrinsics]
    quality_config: QualityGateConfig
    anchor_frame_step: int = 1
    frames_dir: Optional[Path] = None
    output_dir: Path = Path("out")


def _load_frames(frames_dir: Path) -> list[np.ndarray]:
    if not _cv2_spec:
        raise RuntimeError("cv2 is required to load frames from disk")
    frames = []
    for image_path in sorted(frames_dir.glob("*")):
        if image_path.is_dir():
            continue
        image = cv2.imread(str(image_path))
        if image is None:
            continue
        frames.append(image)
    return frames


def run_pipeline(config: PipelineConfig) -> AnchorResult:
    if config.frames_dir is None:
        raise ValueError("frames_dir is required")
    frames = _load_frames(config.frames_dir)

    if config.anchor_type == AnchorType.MARKER_BOARD:
        return resolve_marker_board_anchor(
            frames=frames,
            board_spec=config.board_spec,
            intrinsics=config.intrinsics,
            quality_config=config.quality_config,
            frame_step=config.anchor_frame_step,
            output_dir=config.output_dir,
        )

    return AnchorResult(
        anchor_type=config.anchor_type,
        resolved=False,
        applied=False,
        failure_reason="unsupported_anchor_type",
    )
