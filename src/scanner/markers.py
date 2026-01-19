"""Marker detection helpers for anchors."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import importlib
import importlib.util

from scanner.anchors import MarkerFamily


@dataclass(slots=True)
class MarkerDetectionResult:
    available: bool
    detected_ids: list[int]
    evidence: dict
    warnings: list[str] = field(default_factory=list)
    failure_reason: Optional[str] = None
    pose_tvecs_m: list[dict] = field(default_factory=list)


def detect_markers(
    *,
    frames_dir: Path,
    marker_family: MarkerFamily,
    marker_ids: Optional[list[int]],
    marker_size_m: Optional[float],
    metadata: dict,
    frames_max: Optional[int] = None,
) -> MarkerDetectionResult:
    cv2 = _load_cv2()
    if cv2 is None:
        return MarkerDetectionResult(
            available=False,
            detected_ids=[],
            evidence={"frames_scanned": 0},
            warnings=[
                "OpenCV is not installed; marker anchors require opencv-contrib-python.",
                "Install with: pip install opencv-contrib-python",
            ],
            failure_reason="opencv_missing",
        )

    if not hasattr(cv2, "aruco"):
        return MarkerDetectionResult(
            available=False,
            detected_ids=[],
            evidence={"frames_scanned": 0},
            warnings=[
                "OpenCV ArUco module is unavailable; marker anchors require opencv-contrib-python.",
                "Install with: pip install opencv-contrib-python",
            ],
            failure_reason="aruco_missing",
        )

    if marker_family == MarkerFamily.APRILTAG:
        return MarkerDetectionResult(
            available=False,
            detected_ids=[],
            evidence={"frames_scanned": 0},
            warnings=["AprilTag detection is not implemented in v1."],
            failure_reason="apriltag_unavailable",
        )

    dictionary = _aruco_dictionary_for_family(cv2, marker_family)
    parameters = cv2.aruco.DetectorParameters()
    detector = _build_detector(cv2, dictionary, parameters)

    frames = _list_frames(frames_dir, frames_max=frames_max)
    detections: dict[str, list[dict]] = {}
    detected_ids: list[int] = []
    pose_tvecs: list[dict] = []

    camera_matrix, dist_coeffs = _intrinsics_from_metadata(metadata)

    for frame_path in frames:
        image = cv2.imread(str(frame_path))
        if image is None:
            continue
        corners, ids, _rejected = detector.detectMarkers(image)
        if ids is None or len(ids) == 0:
            continue
        frame_hits: list[dict] = []
        for idx, marker_id in enumerate(ids.flatten()):
            if marker_ids and marker_id not in marker_ids:
                continue
            corners_list = corners[idx].reshape(-1, 2).tolist()
            frame_hits.append({"id": int(marker_id), "corners": corners_list})
            detected_ids.append(int(marker_id))
        if frame_hits:
            detections[frame_path.name] = frame_hits

            if camera_matrix is not None and dist_coeffs is not None and marker_size_m:
                pose_tvecs.extend(
                    _estimate_pose_tvecs(
                        cv2,
                        corners,
                        ids,
                        marker_size_m,
                        camera_matrix,
                        dist_coeffs,
                        frame_path.name,
                        marker_ids,
                    )
                )

    evidence = {
        "frames_scanned": len(frames),
        "frames_with_markers": len(detections),
        "detected_ids": sorted(set(detected_ids)),
        "detections": detections,
    }

    return MarkerDetectionResult(
        available=True,
        detected_ids=sorted(set(detected_ids)),
        evidence=evidence,
        warnings=[],
        failure_reason=None,
        pose_tvecs_m=pose_tvecs,
    )


def _load_cv2():
    if importlib.util.find_spec("cv2") is None:
        return None
    return importlib.import_module("cv2")


def _list_frames(frames_dir: Path, frames_max: Optional[int]) -> list[Path]:
    if not frames_dir.exists():
        return []
    valid_ext = {".png", ".jpg", ".jpeg"}
    frames = sorted(
        [
            path
            for path in frames_dir.iterdir()
            if path.is_file() and path.suffix.lower() in valid_ext
        ]
    )
    if frames_max is not None:
        return frames[: max(frames_max, 0)]
    return frames


def _aruco_dictionary_for_family(cv2, marker_family: MarkerFamily):
    mapping = {
        MarkerFamily.ARUCO_4X4: cv2.aruco.DICT_4X4_50,
        MarkerFamily.ARUCO_5X5: cv2.aruco.DICT_5X5_50,
    }
    return cv2.aruco.getPredefinedDictionary(mapping[marker_family])


def _build_detector(cv2, dictionary, parameters):
    if hasattr(cv2.aruco, "ArucoDetector"):
        return cv2.aruco.ArucoDetector(dictionary, parameters)
    return _LegacyDetector(cv2, dictionary, parameters)


def _intrinsics_from_metadata(metadata: dict):
    intrinsics = metadata.get("camera_intrinsics")
    if not intrinsics:
        return None, None
    camera_matrix = intrinsics.get("camera_matrix")
    dist_coeffs = intrinsics.get("dist_coeffs")
    if camera_matrix is None or dist_coeffs is None:
        return None, None
    import numpy as np

    return np.array(camera_matrix, dtype=float), np.array(dist_coeffs, dtype=float)


def _estimate_pose_tvecs(
    cv2,
    corners,
    ids,
    marker_size_m: float,
    camera_matrix,
    dist_coeffs,
    frame_name: str,
    allowed_ids: Optional[list[int]],
) -> list[dict]:
    if not hasattr(cv2.aruco, "estimatePoseSingleMarkers"):
        return []
    if ids is None:
        return []
    rvecs, tvecs, _ = cv2.aruco.estimatePoseSingleMarkers(
        corners,
        marker_size_m,
        camera_matrix,
        dist_coeffs,
    )
    results: list[dict] = []
    for idx, marker_id in enumerate(ids.flatten()):
        if allowed_ids and marker_id not in allowed_ids:
            continue
        tvec = tvecs[idx][0]
        distance_m = float((tvec[0] ** 2 + tvec[1] ** 2 + tvec[2] ** 2) ** 0.5)
        results.append(
            {
                "frame": frame_name,
                "id": int(marker_id),
                "tvec_m": [float(coord) for coord in tvec],
                "distance_m": distance_m,
            }
        )
    return results


class _LegacyDetector:
    def __init__(self, cv2, dictionary, parameters) -> None:
        self._cv2 = cv2
        self._dictionary = dictionary
        self._parameters = parameters

    def detectMarkers(self, image):
        return self._cv2.aruco.detectMarkers(
            image,
            self._dictionary,
            parameters=self._parameters,
        )
