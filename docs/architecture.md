# Reference frame architecture (scanner module)

## Why reference frames exist
Structure-from-motion (SfM) reconstructions yield point clouds with arbitrary origin, rotation, and scale. Without an explicit anchor, downstream measurements are ambiguous. The reference frame module defines a **center point** that becomes the new origin, leaving rotation untouched in v1. This keeps the system honest about what is (and is not) aligned yet.

## Reference frame inputs
- **User origin (x,y,z)**: Explicit model-space anchor. This is the only high-confidence source in v1.
- **Bounding-box heuristic**: The bounding box center of the point cloud when heuristics are allowed.
- **Marker anchors**: Reserved for ArUco/AprilTag detection (placeholder only).
- **Geospatial anchors**: Reserved for GPS/time anchoring (placeholder only).

## Regime defaults
| Regime | Default heuristic behavior | Notes |
| --- | --- | --- |
| SMALL_OBJECT | heuristics **off** | Metrology requires explicit anchoring. |
| ROOM_BUILDING | heuristics **on** | BBox center is acceptable for rough placement. |
| AERIAL | heuristics **on** | Records a warning that geospatial anchoring is not implemented. |

## Output artifacts
- `reference_frame.json`: Selected origin, source, confidence, and warnings.
- `run.json`: Captures the reference-frame payload and user-provided anchors.
- `scene_sparse_scaled_centered.ply` or `dense_scaled_centered.ply`: Point cloud translated so the origin becomes `(0,0,0)`.

## Future hooks
- **Marker-based centering** will use outer-border markers for small-object metrology.
- **Geospatial/time anchoring** will translate scans into a GPS/time frame once accuracy is validated.

> **Note:** Marker and geospatial anchors are recorded for provenance in v1, but geometry is only affected by user anchors or bounding-box heuristics.
