"""Scanner utilities for marker board anchoring."""

from .anchor import AnchorResult, ReferenceFrame, ScaleConstraints
from .board import BoardSpec, generate_board_image
from .intrinsics import Intrinsics
from .pose import AnchorPose, PoseQualityGates, estimate_board_poses

__all__ = [
    "AnchorResult",
    "ReferenceFrame",
    "ScaleConstraints",
    "BoardSpec",
    "generate_board_image",
    "Intrinsics",
    "AnchorPose",
    "PoseQualityGates",
    "estimate_board_poses",
]
"""Scanner package for marker-board anchoring workflows."""

from scanner.anchors import AnchorResult, AnchorType
from scanner.board import BoardSpec, MarkerFamily
from scanner.intrinsics import Intrinsics
from scanner.quality_gates import QualityGateConfig

__all__ = [
    "AnchorResult",
    "AnchorType",
    "BoardSpec",
    "MarkerFamily",
    "Intrinsics",
    "QualityGateConfig",
]
"""Scanner tooling for reconstruction pipelines."""

from src.scanner.scale_constraints import ScanRegime, ScalePolicy, ScaleEstimate, ScaleSource

__all__ = ["ScanRegime", "ScalePolicy", "ScaleEstimate", "ScaleSource"]
