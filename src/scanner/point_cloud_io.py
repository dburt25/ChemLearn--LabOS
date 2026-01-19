"""Minimal PLY point cloud IO for scanner pipelines."""

from __future__ import annotations

from pathlib import Path


class PlyFormatError(ValueError):
    """Raised when a PLY file cannot be parsed by the lightweight reader."""


def read_ply_points(path: str | Path) -> list[tuple[float, float, float]]:
    path = Path(path)
    with path.open("r", encoding="utf-8") as handle:
        header = []
        line = handle.readline()
        if not line:
            raise PlyFormatError("PLY file is empty.")
        header.append(line.strip())
        if header[0] != "ply":
            raise PlyFormatError("PLY header missing magic 'ply'.")

        vertex_count = None
        while True:
            line = handle.readline()
            if not line:
                raise PlyFormatError("PLY header terminated unexpectedly.")
            line = line.strip()
            header.append(line)
            if line.startswith("element vertex"):
                parts = line.split()
                if len(parts) != 3:
                    raise PlyFormatError("Malformed vertex element line.")
                vertex_count = int(parts[2])
            if line == "end_header":
                break

        if vertex_count is None:
            raise PlyFormatError("PLY header missing vertex count.")

        points: list[tuple[float, float, float]] = []
        for _ in range(vertex_count):
            line = handle.readline()
            if not line:
                raise PlyFormatError("PLY vertex data truncated.")
            parts = line.strip().split()
            if len(parts) < 3:
                raise PlyFormatError("PLY vertex line missing coordinates.")
            points.append((float(parts[0]), float(parts[1]), float(parts[2])))
        return points


def write_ply_points(path: str | Path, points: list[tuple[float, float, float]]) -> None:
    path = Path(path)
    with path.open("w", encoding="utf-8") as handle:
        handle.write("ply\n")
        handle.write("format ascii 1.0\n")
        handle.write(f"element vertex {len(points)}\n")
        handle.write("property float x\n")
        handle.write("property float y\n")
        handle.write("property float z\n")
        handle.write("end_header\n")
        for x, y, z in points:
            handle.write(f"{x} {y} {z}\n")
