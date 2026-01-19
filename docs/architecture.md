# Scanner Architecture (Anchors v1)

## Anchor stage overview
The scanner pipeline resolves anchors after frame and metadata extraction, before reconstruction output is finalized. The anchor stage is responsible for:

1. Marker detection for small-object scans (optional; requires OpenCV ArUco).
2. Capturing geo/time anchor metadata for aerial scans (stored only in v1).
3. Feeding any resolved scale/origin hints into the scale constraints and reference frame steps.

### Pipeline order (anchor-aware)
1. Extract frames
2. Extract metadata
3. **Resolve anchors** (marker detection or geo/time capture)
4. Reconstruction (COLMAP or equivalent)
5. Apply scale constraints
6. Apply reference frame centering

Anchor results are persisted into `run.json` and `reconstruction_metrics.json` for forward compatibility.
