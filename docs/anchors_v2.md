# Anchors v2 (Marker Board)

Anchors v2 uses marker-board alignment to stabilize 3D scans. For **SMALL_OBJECT** workflows, camera intrinsics are mandatory.

## Calibration requirement
- **Always run calibration first** for SMALL_OBJECT scans.
- Provide the resulting `camera.json` to marker-board anchoring so fx/fy/cx/cy/distortion are not guessed.

If intrinsics are missing, the pipeline should fail with:

```
Run scanner calibrate chessboard/charuco --input <video_or_dir> --out camera.json to generate camera.json
```

## Example usage
```bash
scanner calibrate chessboard \
  --input ./captures/chessboard_session \
  --out ./calibration/camera.json \
  --squares-x 7 \
  --squares-y 6 \
  --square-size-mm 10
```

Then feed `./calibration/camera.json` into the marker-board anchoring configuration.
