import argparse
from pathlib import Path

import cv2
import numpy as np


def build_demo_video(output_path: Path, frames: int = 20, size: tuple[int, int] = (320, 240)) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(output_path), fourcc, 10, size)
    for idx in range(frames):
        frame = np.zeros((size[1], size[0], 3), dtype=np.uint8)
        cv2.circle(frame, (20 + idx * 5, 40 + idx * 3), 20, (0, 255, 0), -1)
        cv2.putText(
            frame,
            f"Frame {idx}",
            (10, size[1] - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
        )
        writer.write(frame)
    writer.release()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a tiny demo video for the scanner pipeline.")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build_demo_video(args.output)
