# Marker Board Printing

To generate a printable marker board:
# Marker Board Printing Guide

## Generate a board
Use the scanner CLI to generate a board image at a fixed DPI:

```bash
scanner board generate \
  --family aruco_4x4 \
  --rows 4 \
  --cols 6 \
  --marker-size-m 0.03 \
  --marker-spacing-m 0.006 \
  --out out/board.png
```

**Printing guidance**

- Print at **100% scale** (no fit-to-page).
- Disable any automatic scaling in the print dialog.
- Verify one marker with a ruler after printing to confirm scale.

If you need a PDF, convert the PNG to PDF with your preferred tool after generation.
  --marker-size-m 0.02 \
  --marker-spacing-m 0.005 \
  --out out/board.png
```

## Print settings
- **Print at 100% scale** (no fit-to-page or shrink-to-fit).
- Disable automatic scaling in the print dialog.
- Verify a few marker dimensions with calipers before capture.

The anchor system assumes the board dimensions match `marker_size_m` and `marker_spacing_m` exactly.
