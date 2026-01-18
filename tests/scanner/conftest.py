from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import pytest


def create_test_video(path: Path, frames: int = 8, size: tuple[int, int] = (160, 120)) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(path), fourcc, 10, size)
    for idx in range(frames):
        frame = np.zeros((size[1], size[0], 3), dtype=np.uint8)
        cv2.rectangle(frame, (5 + idx, 5 + idx), (30 + idx, 30 + idx), (255, 0, 0), -1)
        writer.write(frame)
    writer.release()


@pytest.fixture()
def sample_video(tmp_path: Path) -> Path:
    video_path = tmp_path / "sample.mp4"
    create_test_video(video_path)
    return video_path
