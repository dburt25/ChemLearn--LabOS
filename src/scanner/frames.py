from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import cv2

from scanner.utils import safe_mkdir


@dataclass(frozen=True)
class FrameExtractionResult:
    frames_dir: Path
    frame_count: int
    fps: float


def extract_frames(
    *,
    input_path: Path,
    output_dir: Path,
    max_frames: int | None,
    logger: logging.Logger,
) -> FrameExtractionResult:
    safe_mkdir(output_dir)
    capture = cv2.VideoCapture(str(input_path))
    if not capture.isOpened():
        raise RuntimeError(f"Unable to open video file: {input_path}")

    fps = capture.get(cv2.CAP_PROP_FPS)
    frame_idx = 0
    written = 0
    while True:
        if max_frames is not None and written >= max_frames:
            break
        ret, frame = capture.read()
        if not ret:
            break
        frame_path = output_dir / f"frame_{frame_idx:06d}.png"
        cv2.imwrite(str(frame_path), frame)
        written += 1
        frame_idx += 1

    capture.release()
    logger.info(
        "Frames extracted",
        extra={"context": {"frames": written, "fps": fps, "output_dir": str(output_dir)}},
    )
    return FrameExtractionResult(frames_dir=output_dir, frame_count=written, fps=fps)
