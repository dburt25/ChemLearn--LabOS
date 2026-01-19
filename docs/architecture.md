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
