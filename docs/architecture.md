# Architecture

## Pipeline Stages
1. **ingest**: validate inputs, compute hashes, capture environment metadata.
2. **metadata**: extract container and camera metadata (best-effort).
3. **frames**: extract frames to a workspace.
4. **multiview_backend**: execute a backend (COLMAP Phase 0).
5. **export**: convert reconstruction outputs to PLY.
6. **report**: emit run + metrics reports regardless of failure.

## Modules
- `scanner.pipeline`: orchestration and error handling.
- `scanner.metadata`: ffprobe/OpenCV metadata extraction.
- `scanner.frames`: OpenCV frame extraction.
- `scanner.backends`: backend interface + COLMAP implementation.
- `scanner.export`: export utilities.
- `scanner.report`: run.json + reconstruction_metrics.json.
- `scanner.logging`: structured JSON logging.

## Extensibility
Each stage is a typed module with explicit inputs/outputs. Backends conform to `BackendBase`, enabling future dense MVS, TSDF, or VIO integration without altering upstream stages.
