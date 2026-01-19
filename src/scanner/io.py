"""I/O helpers for scanner artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Tuple


def write_ply(path: Path, points: Iterable[Tuple[float, float, float]]) -> None:
    point_list = list(points)
    header = [
        "ply",
        "format ascii 1.0",
        f"element vertex {len(point_list)}",
        "property float x",
        "property float y",
        "property float z",
        "end_header",
    ]
    lines = ["{:.6f} {:.6f} {:.6f}".format(x, y, z) for x, y, z in point_list]
    path.write_text("\n".join(header + lines) + "\n", encoding="utf-8")
