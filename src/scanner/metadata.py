from __future__ import annotations

import json
import logging
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import cv2


@dataclass(frozen=True)
class MetadataResult:
    container: dict[str, Any]
    streams: list[dict[str, Any]]
    extracted_fields: list[str]
    missing_fields: list[str]
    source: str


FFPROBE_FIELDS = [
    "format.format_name",
    "format.duration",
    "format.bit_rate",
    "format.tags",
    "streams.codec_name",
    "streams.codec_type",
    "streams.width",
    "streams.height",
    "streams.avg_frame_rate",
    "streams.r_frame_rate",
    "streams.tags",
]


def _run_ffprobe(path: Path, logger: logging.Logger) -> MetadataResult | None:
    if shutil.which("ffprobe") is None:
        return None
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(path),
    ]
    try:
        output = subprocess.check_output(cmd, text=True)
    except subprocess.CalledProcessError as exc:
        logger.warning(
            "ffprobe failed",
            extra={"context": {"error": str(exc), "command": " ".join(cmd)}},
        )
        return None

    payload = json.loads(output)
    container = payload.get("format", {})
    streams = payload.get("streams", [])
    extracted = [field for field in FFPROBE_FIELDS if _field_exists(payload, field)]
    missing = [field for field in FFPROBE_FIELDS if field not in extracted]
    return MetadataResult(
        container=container,
        streams=streams,
        extracted_fields=extracted,
        missing_fields=missing,
        source="ffprobe",
    )


def _field_exists(payload: dict[str, Any], field: str) -> bool:
    target = payload
    for part in field.split("."):
        if isinstance(target, list):
            target = target[0] if target else None
        if not isinstance(target, dict) or part not in target:
            return False
        target = target[part]
    return target is not None


def _fallback_cv_metadata(path: Path) -> MetadataResult:
    capture = cv2.VideoCapture(str(path))
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = capture.get(cv2.CAP_PROP_FPS)
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    capture.release()

    container = {"format_name": "unknown", "duration": None, "bit_rate": None}
    streams = [
        {
            "codec_type": "video",
            "width": width,
            "height": height,
            "avg_frame_rate": fps,
            "frame_count": frame_count,
        }
    ]
    extracted = ["streams.width", "streams.height", "streams.avg_frame_rate"]
    missing = [field for field in FFPROBE_FIELDS if field not in extracted]
    return MetadataResult(
        container=container,
        streams=streams,
        extracted_fields=extracted,
        missing_fields=missing,
        source="opencv",
    )


def extract_metadata(path: Path, logger: logging.Logger) -> MetadataResult:
    ffprobe_result = _run_ffprobe(path, logger)
    if ffprobe_result:
        return ffprobe_result
    logger.warning(
        "Metadata extraction fallback to OpenCV", extra={"context": {"path": str(path)}}
    )
    return _fallback_cv_metadata(path)
