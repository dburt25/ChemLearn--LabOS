"""Marker detection helpers for scanner anchors."""

from __future__ import annotations

import importlib
import importlib.util
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from scanner.anchor_types import AnchorResult, AnchorSpec, AnchorType, Confidence, MarkerFamily


@dataclass(frozen=True)
class MarkerDetection:
    frames_examined: int
    frames_with_markers: int
    detected_ids: list[int]
    id_counts: dict[int, int]
    corners_by_frame: dict[str, list[list[list[float]]]]
    pose_tvecs_m: list[list[float]]
    avg_marker_edge_px: float | None


def _load_cv2_module() -> Any | None:
    spec = importlib.util.find_spec("cv2")
    if spec is None:
        return None
    return importlib.import_module("cv2")


def aruco_capability_status() -> tuple[bool, list[str]]:
    cv2 = _load_cv2_module()
    if cv2 is None:
        return False, [
            "OpenCV is not installed. Install opencv-contrib-python to enable marker anchors.",
        ]
    if not hasattr(cv2, "aruco"):
        return False, [
            "OpenCV aruco module not available. Install opencv-contrib-python for marker anchors.",
        ]
    return True, []


def _aruco_dictionary(marker_family: MarkerFamily, cv2: Any) -> Any:
    if marker_family == MarkerFamily.ARUCO_5X5:
        return cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_5X5_100)
    return cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_100)


def _iter_frame_paths(frames_dir: Path, max_frames: int | None) -> Iterable[Path]:
    extensions = ("*.jpg", "*.jpeg", "*.png", "*.bmp", "*.tif", "*.tiff")
    paths: list[Path] = []
    for pattern in extensions:
        paths.extend(sorted(frames_dir.glob(pattern)))
    if max_frames is not None:
        return paths[:max_frames]
    return paths


def detect_markers(
    frames_dir: Path,
    marker_family: MarkerFamily,
    *,
    marker_ids: list[int] | None,
    marker_size_m: float | None,
    marker_frames_max: int | None,
    metadata: dict[str, Any],
) -> MarkerDetection:
    cv2 = _load_cv2_module()
    if cv2 is None or not hasattr(cv2, "aruco"):
        return MarkerDetection(
            frames_examined=0,
            frames_with_markers=0,
            detected_ids=[],
            id_counts={},
            corners_by_frame={},
            pose_tvecs_m=[],
            avg_marker_edge_px=None,
        )
    dictionary = _aruco_dictionary(marker_family, cv2)
    parameters = cv2.aruco.DetectorParameters()
    detector = None
    if hasattr(cv2.aruco, "ArucoDetector"):
        detector = cv2.aruco.ArucoDetector(dictionary, parameters)
    corners_by_frame: dict[str, list[list[list[float]]]] = {}
    detected_ids: list[int] = []
    id_counts: dict[int, int] = {}
    pose_tvecs_m: list[list[float]] = []
    marker_edge_px_samples: list[float] = []
    camera_matrix, dist_coeffs = _camera_intrinsics(metadata)

    frames_examined = 0
    frames_with_markers = 0

    for frame_path in _iter_frame_paths(frames_dir, marker_frames_max):
        image = cv2.imread(str(frame_path))
        if image is None:
            continue
        frames_examined += 1
        if detector is not None:
            frame_corners, frame_ids, _ = detector.detectMarkers(image)
        else:
            frame_corners, frame_ids, _ = cv2.aruco.detectMarkers(
                image,
                dictionary,
                parameters=parameters,
            )
        if frame_ids is None or len(frame_ids) == 0:
            continue
        frames_with_markers += 1
        ids = [int(value[0]) for value in frame_ids]
        detected_ids.extend(ids)
        for marker_id in ids:
            id_counts[marker_id] = id_counts.get(marker_id, 0) + 1
        corners_by_frame[str(frame_path.name)] = [corner.tolist() for corner in frame_corners]

        marker_edge_px_samples.extend(_marker_edge_lengths(frame_corners))

        if marker_size_m is not None and camera_matrix is not None:
            rvecs, tvecs, _ = cv2.aruco.estimatePoseSingleMarkers(
                frame_corners,
                marker_size_m,
                camera_matrix,
                dist_coeffs,
            )
            for tvec in tvecs:
                pose_tvecs_m.append([float(value) for value in tvec[0]])

    unique_ids = sorted(set(detected_ids))
    avg_marker_edge_px = (
        sum(marker_edge_px_samples) / len(marker_edge_px_samples)
        if marker_edge_px_samples
        else None
    )

    if marker_ids:
        missing = [marker_id for marker_id in marker_ids if marker_id not in unique_ids]
        if missing:
            for marker_id in missing:
                id_counts.setdefault(marker_id, 0)

    return MarkerDetection(
        frames_examined=frames_examined,
        frames_with_markers=frames_with_markers,
        detected_ids=unique_ids,
        id_counts=id_counts,
        corners_by_frame=corners_by_frame,
        pose_tvecs_m=pose_tvecs_m,
        avg_marker_edge_px=avg_marker_edge_px,
    )


def resolve_marker_anchor(
    anchor_spec: AnchorSpec,
    frames_dir: Path,
    metadata: dict[str, Any],
    *,
    marker_frames_max: int | None,
) -> AnchorResult:
    has_capability, warnings = aruco_capability_status()
    if not has_capability:
        return AnchorResult(
            resolved=False,
            applied=False,
            anchor_type=anchor_spec.anchor_type,
            confidence=Confidence.LOW,
            warnings=warnings,
            evidence={},
            failure_reason="marker_capability_missing",
        )
    marker_family = anchor_spec.marker_family or MarkerFamily.ARUCO_4X4
    detection = detect_markers(
        frames_dir,
        marker_family,
        marker_ids=anchor_spec.marker_ids,
        marker_size_m=anchor_spec.marker_size_m,
        marker_frames_max=marker_frames_max,
        metadata=metadata,
    )
    warnings = []
    if detection.frames_examined == 0:
        return AnchorResult(
            resolved=False,
            applied=False,
            anchor_type=anchor_spec.anchor_type,
            confidence=Confidence.LOW,
            warnings=["No frames available for marker detection."],
            evidence={"frames_examined": 0},
            failure_reason="no_frames",
        )
    if not detection.detected_ids:
        return AnchorResult(
            resolved=False,
            applied=False,
            anchor_type=anchor_spec.anchor_type,
            confidence=Confidence.LOW,
            warnings=["No markers detected in frames."],
            evidence={
                "frames_examined": detection.frames_examined,
                "frames_with_markers": detection.frames_with_markers,
            },
            failure_reason="markers_not_found",
        )

    if anchor_spec.marker_ids:
        missing = [
            marker_id
            for marker_id in anchor_spec.marker_ids
            if marker_id not in detection.detected_ids
        ]
        if missing:
            warnings.append(f"Expected marker IDs not detected: {missing}")

    required_count = 2 if anchor_spec.anchor_type == AnchorType.MARKER_PAIR else 1
    resolved = len(detection.detected_ids) >= required_count
    if not resolved:
        return AnchorResult(
            resolved=False,
            applied=False,
            anchor_type=anchor_spec.anchor_type,
            confidence=Confidence.LOW,
            warnings=warnings + ["Insufficient marker coverage for anchor type."],
            evidence=_detection_evidence(detection),
            failure_reason="insufficient_markers",
        )

    scale_factor = _infer_scale_factor(anchor_spec, detection, metadata)
    origin_xyz = _infer_origin_xyz(detection)
    confidence = _confidence_for_detection(anchor_spec, detection, scale_factor)

    if scale_factor is None:
        warnings.append(
            "Marker pose resolved, but scale cannot be inferred without intrinsics and size.",
        )

    return AnchorResult(
        resolved=True,
        applied=False,
        anchor_type=anchor_spec.anchor_type,
        confidence=confidence,
        warnings=warnings,
        evidence=_detection_evidence(detection),
        scale_factor=scale_factor,
        origin_xyz=origin_xyz,
    )


def _detection_evidence(detection: MarkerDetection) -> dict[str, Any]:
    return {
        "frames_examined": detection.frames_examined,
        "frames_with_markers": detection.frames_with_markers,
        "detected_ids": detection.detected_ids,
        "id_counts": detection.id_counts,
        "corners_by_frame": detection.corners_by_frame,
        "pose_tvecs_m": detection.pose_tvecs_m,
        "avg_marker_edge_px": detection.avg_marker_edge_px,
    }


def _camera_intrinsics(metadata: dict[str, Any]) -> tuple[Any | None, Any | None]:
    intrinsics = metadata.get("camera_intrinsics") or {}
    if not intrinsics:
        return None, None
    fx = intrinsics.get("fx")
    fy = intrinsics.get("fy")
    cx = intrinsics.get("cx")
    cy = intrinsics.get("cy")
    if fx is None or fy is None or cx is None or cy is None:
        return None, None
    cv2 = _load_cv2_module()
    if cv2 is None:
        return None, None
    camera_matrix = cv2.UMat(
        [[float(fx), 0.0, float(cx)], [0.0, float(fy), float(cy)], [0.0, 0.0, 1.0]]
    )
    dist_coeffs = intrinsics.get("dist_coeffs")
    if dist_coeffs is None:
        dist_coeffs = [0.0, 0.0, 0.0, 0.0, 0.0]
    dist_coeffs_mat = cv2.UMat([list(map(float, dist_coeffs))])
    return camera_matrix, dist_coeffs_mat


def _marker_edge_lengths(frame_corners: Iterable[Any]) -> list[float]:
    lengths: list[float] = []
    for marker in frame_corners:
        if len(marker) == 0:
            continue
        corners = marker[0]
        if len(corners) < 4:
            continue
        for idx in range(4):
            x1, y1 = corners[idx]
            x2, y2 = corners[(idx + 1) % 4]
            length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
            lengths.append(float(length))
    return lengths


def _infer_scale_factor(
    anchor_spec: AnchorSpec,
    detection: MarkerDetection,
    metadata: dict[str, Any],
) -> float | None:
    if anchor_spec.marker_size_m is None:
        return None
    intrinsics = metadata.get("camera_intrinsics")
    if not intrinsics:
        return None
    if detection.avg_marker_edge_px is None or detection.avg_marker_edge_px == 0:
        return None
    return float(anchor_spec.marker_size_m) / float(detection.avg_marker_edge_px)


def _infer_origin_xyz(detection: MarkerDetection) -> tuple[float, float, float] | None:
    if not detection.pose_tvecs_m:
        return None
    count = len(detection.pose_tvecs_m)
    if count == 0:
        return None
    avg = [0.0, 0.0, 0.0]
    for tvec in detection.pose_tvecs_m:
        for idx, value in enumerate(tvec):
            avg[idx] += value
    return (avg[0] / count, avg[1] / count, avg[2] / count)


def _confidence_for_detection(
    anchor_spec: AnchorSpec,
    detection: MarkerDetection,
    scale_factor: float | None,
) -> Confidence:
    if scale_factor is not None and detection.pose_tvecs_m:
        return Confidence.HIGH
    if detection.detected_ids:
        return Confidence.MED
    return Confidence.LOW


def generate_marker_image(
    marker_id: int,
    marker_family: MarkerFamily,
    *,
    side_pixels: int = 200,
) -> Any | None:
    cv2 = _load_cv2_module()
    if cv2 is None or not hasattr(cv2, "aruco"):
        return None
    dictionary = _aruco_dictionary(marker_family, cv2)
    if hasattr(cv2.aruco, "generateImageMarker"):
        image = cv2.aruco.generateImageMarker(dictionary, marker_id, side_pixels)
    else:
        image = cv2.aruco.drawMarker(dictionary, marker_id, side_pixels)
    return image
