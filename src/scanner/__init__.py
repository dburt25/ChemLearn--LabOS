"""Scanner utilities for reference frame handling."""

from .reference_frame import (
    ReferenceFrameConfidence,
    ReferenceFramePolicy,
    ReferenceFrameResult,
    ReferenceFrameSource,
    ReferenceFrameUserInputs,
    ScanRegime,
    resolve_reference_frame,
)

__all__ = [
    "ReferenceFrameConfidence",
    "ReferenceFramePolicy",
    "ReferenceFrameResult",
    "ReferenceFrameSource",
    "ReferenceFrameUserInputs",
    "ScanRegime",
    "resolve_reference_frame",
]
"""Scanner package for 3D reconstruction utilities."""
"""Scanner tooling for 3D capture workflows."""

from scanner.intrinsics import Intrinsics

__all__ = ["Intrinsics"]
"""Marker-board anchored scanning utilities."""
"""Scanner package for marker-board anchoring workflows."""

from scanner.anchors import AnchorResult, AnchorType
from scanner.board import BoardSpec, MarkerFamily
from scanner.intrinsics import Intrinsics
from scanner.quality_gates import QualityGateConfig

__all__ = [
    "AnchorResult",
    "AnchorType",
    "BoardSpec",
    "Intrinsics",
    "MarkerFamily",
]
    "MarkerFamily",
    "Intrinsics",
    "QualityGateConfig",
]
"""Scanner tooling for reconstruction pipelines."""

from src.scanner.scale_constraints import ScanRegime, ScalePolicy, ScaleEstimate, ScaleSource

__all__ = ["ScanRegime", "ScalePolicy", "ScaleEstimate", "ScaleSource"]
