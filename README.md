# Multiview 3D Scanner (Phase 0)

A modular, metadata-aware multiview 3D reconstruction pipeline focused on accuracy tiers and reproducibility. Phase 0 delivers a vertical slice that runs end-to-end and prepares the architecture for future precision upgrades.

## Purpose
- Provide a **multiview** reconstruction pipeline that accepts video inputs and prepares a consistent output + reporting surface.
- Establish modular interfaces so future upgrades can plug in dense MVS / TSDF / VIO and precision-calibrated workflows.

## Non-goals (Phase 0)
- Achieving the target precision tiers today.
- Providing a dense, watertight mesh.
- Automatic scale calibration without metadata or external references.

## Accuracy Tiers (Targets, not Phase 0 claims)
- **Tier S** (small objects < 1 m³): target 0.01 mm precision (metrology-grade)
- **Tier R** (rooms/buildings): target 1.0 mm precision
- **Tier A** (aerial overhead): target 10 cm precision

Phase 0 reports what prevents reaching these tiers and **never** claims to meet them.

## Quickstart
```bash
make setup
make run-demo
```

Run the pipeline on your own video:
```bash
scanner pipeline --input /path/to/video.mov --out /path/to/output
```

## Outputs
- `sparse.ply` (if COLMAP succeeds)
- `run.json` (always)
- `reconstruction_metrics.json` (always)
- Blender import instructions: `docs/blender_import.md`

## Limitations (Phase 0)
- Depends on COLMAP for sparse reconstruction; if missing, the pipeline exits non-zero and writes guidance.
- Metadata extraction is best-effort; missing intrinsics/orientation reduces scale confidence.
- No dense reconstruction or meshing.

## Roadmap
- Dense MVS backend + TSDF fusion.
- Camera calibration ingestion and improved scale estimation.
- Precision tier validation suites and ground truth datasets.

## Documentation
- `docs/architecture.md`
- `docs/decisions.md`
- `docs/blender_import.md`

