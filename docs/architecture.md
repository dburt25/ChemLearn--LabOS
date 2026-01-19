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
