"""Scanner pipeline helpers."""

from __future__ import annotations

from pathlib import Path


def ensure_intrinsics_for_small_object(
    *,
    regime: str,
    anchor: str,
    intrinsics_path: str | None,
) -> None:
    """Ensure intrinsics exist for SMALL_OBJECT + marker_board workflows."""

    if regime != "SMALL_OBJECT" or anchor != "marker_board":
        return

    if not intrinsics_path or not Path(intrinsics_path).exists():
        raise ValueError(
            "Run scanner calibrate chessboard/charuco --input <video_or_dir> --out camera.json to generate camera.json"
        )
