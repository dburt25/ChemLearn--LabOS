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
