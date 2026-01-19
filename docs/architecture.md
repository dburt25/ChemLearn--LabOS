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
