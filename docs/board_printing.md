# Marker Board Printing

To generate a printable marker board:

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
