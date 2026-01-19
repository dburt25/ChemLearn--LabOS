# Scanner Architecture (Anchor Stage)

## Pipeline order (v1)
1. Extract frames.
2. Extract metadata (camera intrinsics, user-provided hints).
3. Resolve anchors (marker detection or geo/time capture).
4. Reconstruction (COLMAP or equivalent).
5. Apply scale constraints.
6. Apply reference-frame centering.

## Anchor integration
- **Marker anchors** detect ArUco markers and capture evidence for scale/origin inference.
- **Geo/time anchors** store latitude/longitude/altitude and timestamp values without applying georegistration.
- Anchor results are persisted to `run.json` and `reconstruction_metrics.json` for forward-compatible pipelines.

## Limitations (v1)
- Marker-based scale is only computed when camera intrinsics are available; otherwise the anchor is recorded but not applied.
- Geo/time anchors are stored only; alignment is not yet implemented.
