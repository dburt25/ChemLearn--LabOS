# Scanner Architecture (Marker-Board Anchoring)

## Overview
The scanner pipeline introduces a marker-board anchored world frame for true metric reconstruction when camera intrinsics are available. This is the first true metric path for SMALL_OBJECT regimes, and it requires calibrated intrinsics plus strict quality gating. The anchoring step happens before reconstruction and scale constraints so that the board defines origin, orientation, and metric scale.

## Pipeline order
1. **Frames**: load image frames and timestamps (if provided).
2. **Metadata**: capture board specification + camera intrinsics provenance.
3. **Anchors (marker board)**: detect markers, estimate board pose per frame, and evaluate quality gates.
4. **Reconstruction**: downstream photogrammetry or neural reconstruction (external to this module).
5. **Scale constraints**: skipped when board anchoring is applied; otherwise use fallback heuristics.
6. **Reference frame**: use the anchored board origin + axes when available.

## World frame definition
- **Origin**: board center, computed from board geometry.
- **Axes**: aligned to the board plane using the ArUco grid board convention.
- **Metric scale**: derived from marker size + spacing and camera intrinsics.

## Quality gates
Anchoring is only applied when:
- A minimum number of frames contain a valid board pose.
- Reprojection error statistics fall below configured thresholds.
- Outlier reprojection errors are rejected using MAD filtering.

## Failure handling
- Missing intrinsics or missing `cv2.aruco` support results in a non-applied anchor with clear guidance.
- Anchoring never fabricates scale or georegistration; failures propagate to fallback heuristics.

## Metrology disclaimer
Achieving millimeter-level accuracy requires calibrated intrinsics, controlled capture, and independent verification of printed board scale. The anchoring system provides a metric reference, not a guarantee of measurement precision.
