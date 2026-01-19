# Architecture Notes

## Scanner Pipeline (Reference Frame)
The scanner pipeline treats the structure-from-motion (SfM) coordinate system as arbitrary. The reference frame stage defines a stable scene origin that downstream artifacts can reference, even when reconstruction outputs are skipped. The current implementation is a structural skeleton and does not claim geospatial accuracy.

### Reference Frame Stage
1. **Origin selection:**
   - User-supplied origin (highest confidence).
   - Bounding-box center heuristic when allowed by regime.
   - Marker/GEO anchors are accepted but not applied (placeholders).
2. **Centering:**
   - After scale is applied, point clouds are translated so the selected origin maps to `(0, 0, 0)`.
   - Centered outputs are emitted as `*_scaled_centered.ply`.
3. **Reporting:**
   - `run.json` and `reconstruction_metrics.json` capture source, origin, confidence, warnings, and unused anchors.

### Regime-aware defaults
- **SMALL_OBJECT:** requires explicit origin.
- **ROOM_BUILDING:** allows heuristic bbox center.
- **AERIAL:** allows heuristic bbox center with warnings; geo/time anchors are future work.
# Scanner Reference Frame Architecture (v1)

## Why a reference frame module
Structure-from-Motion pipelines produce point clouds with arbitrary origin, rotation, and scale until explicit anchors are applied. The reference frame module defines a consistent origin selection step and records provenance for any anchors the user provides.

## Origin selection flow
1. **User anchor**: If a model-space origin is provided, it is used with high confidence.
2. **Heuristic fallback**: When heuristics are allowed, the bounding-box center of the point cloud becomes the origin with medium/low confidence.
3. **No anchor**: When heuristics are disallowed and no user origin exists, the pipeline fails with a clear message.

## Regime defaults
- **Small object**: heuristics are disabled by default to keep metrology paths explicit.
- **Room/building**: heuristics are enabled by default.
- **Aerial**: heuristics are enabled by default, but a warning is recorded because geospatial anchoring is only a placeholder in v1.

## Marker + geospatial anchors (v1)
Marker-based centering and geospatial/time anchors are accepted as inputs and stored in provenance, but they do not yet alter geometry. The reference frame report explicitly notes when these anchors are recorded without being applied.

## Output centering
After reconstruction and scale (if present), the pipeline translates point clouds so the selected origin becomes (0, 0, 0). Centered outputs are saved with a `_centered` suffix for transparency.
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
# Scanner Architecture Notes

## Marker board anchoring (Anchors v2)
The scanner package adds a marker-board anchored world frame. This is the first true metric path for the SMALL_OBJECT regime because the board plus calibrated intrinsics provides scale, origin, and orientation.

### Pipeline order
1. Frames + metadata ingestion
2. Marker-board anchoring (PnP)
3. Reconstruction
4. Scale constraints
5. Reference frame resolution

If the marker board anchor is applied, the reference frame and scale constraints are derived from the board’s metric definition (no autoscale). If it is not applied, the pipeline falls back to existing heuristics.

### Metrology disclaimer
Millimeter-level accuracy requires calibrated intrinsics, controlled capture, and verification against known measurements. The anchor system records quality gate statistics, but it does not replace a full metrology validation plan.
# Scanner Architecture (Scale Constraints)

## Pipeline stage: scale constraints
Structure-from-motion reconstructions are scale ambiguous. The scale constraints stage exists to keep reconstructions within sane units and to make every scale decision explicit.

**Placement:** run after reconstruction artifacts are available (e.g., a sparse PLY). If reconstruction is skipped or unavailable, the stage still emits the scale policy and an estimate marked as not applied.

## Policy logic
1. **Select a scan regime**
   - **SMALL_OBJECT**: expected scene size ~0.05–1.0 m. Requires a user reference by default.
   - **ROOM_BUILDING**: expected scene size ~1–30 m. Allows autoscale if hard bounds are violated.
   - **AERIAL**: expected scene size ~30–5000 m. Allows autoscale if hard bounds are violated.

2. **Apply expected size + hard bounds**
   - *Expected size* is advisory: it defines a typical range for autoscale targets.
   - *Hard bounds* are absolute clamps to prevent nonsensical outputs (e.g., 500 km scenes).

3. **Scale references (ordered by trust)**
   - User distance pair, object size, marker size, or a weak metadata prior.
   - When no reference is provided, the estimate is LOW confidence and the output is marked as unscaled.

4. **Autoscale guardrails**
   - If a hard bound is violated and autoscale is allowed, the pipeline computes a conservative scale factor that brings the extent back into the expected range.
   - Autoscale is logged as LOW confidence with an explicit `AUTOSCALE_APPLIED` note.

5. **Small-object rule**
   - SMALL_OBJECT scans default to requiring a user reference. An explicit `--allow-weak-scale` override is needed to proceed without one.

## Outputs
- `scene_sparse_scaled.ply` when a scale factor is applied to a point cloud.
- `run.json` and `reconstruction_metrics.json` include the scale policy, estimate, and any violations.

> The scale constraints stage is conservative and does **not** claim metrology precision. It exists to prevent absurd units and to capture explicit references when available.
