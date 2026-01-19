# Camera Calibration (Charuco/Chessboard)

Reliable intrinsics are mandatory for **SMALL_OBJECT** scanning workflows. Use the calibration CLI to generate `camera.json` and a `calibration_report.json` before running marker-board anchoring.

## CLI examples

### Chessboard
```bash
scanner calibrate chessboard \
  --input ./captures/chessboard_session \
  --out ./calibration/camera.json \
  --squares-x 7 \
  --squares-y 6 \
  --square-size-mm 10 \
  --min-views 15
```

### Charuco (preferred when OpenCV aruco is available)
```bash
scanner calibrate charuco \
  --input ./captures/charuco.mp4 \
  --out ./calibration/camera.json \
  --aruco-family aruco_4x4 \
  --squares-x 6 \
  --squares-y 8 \
  --square-length-mm 10 \
  --marker-length-mm 7 \
  --min-views 15
```

> If `scanner calibrate charuco` reports missing capabilities, install `opencv-contrib-python` and re-run.

## Output artifacts
- **camera.json** – camera intrinsics used by marker-board anchoring (fx, fy, cx, cy, distortion).
- **calibration_report.json** – quality gates, per-view errors, warnings, and suggestions.
- **detected_corners_preview/** – optional annotated previews when `--preview-count` is enabled.

## Capture tips
- Capture **many views** (15+ distinct angles and distances) with the board filling most of the frame.
- Lock focus and exposure to avoid variation across frames.
- Use a fast shutter to avoid motion blur.
- Keep the board flat; avoid bending or warping the printout.

## Printing guidance
- Print calibration boards at **100% scale** (no scaling in the print dialog).
- Measure one square with calipers to confirm the square size in millimeters.
- Mount the board on a rigid surface to keep it planar.

## Common failure modes & fixes
- **Not enough views**: capture more images/videos with wider angles and distances.
- **High reprojection error**: improve lighting, focus, and stability; avoid motion blur.
- **No corners detected**: verify board dimensions match `--squares-x/--squares-y` and ensure the board fills the frame.

## Using camera.json in marker-board anchoring
When running marker-board anchoring for **SMALL_OBJECT**, supply the generated `camera.json` so intrinsics are not guessed. Calibration failures should be resolved before scanning.
