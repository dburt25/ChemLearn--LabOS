from __future__ import annotations

import json
from pathlib import Path
from time import perf_counter

from scanner.backends.backend_base import BackendUnavailableError, get_backend
from scanner.export import export_sparse_ply
from scanner.frames import FrameExtractionResult, extract_frames
from scanner.ingest import IngestResult
from scanner.logging import build_logger
from scanner.metadata import FFPROBE_FIELDS, MetadataResult, extract_metadata
from scanner.report import (
    build_metrics_report,
    build_run_report,
    write_json_report,
)
from scanner.utils import hash_file, safe_mkdir


def run_pipeline(
    *,
    input_path: Path,
    output_dir: Path,
    backend_name: str,
    max_frames: int | None,
) -> int:
    logger = build_logger()
    start_time = perf_counter()
    output_dir = output_dir.resolve()
    safe_mkdir(output_dir)

    run_report_path = output_dir / "run.json"
    metrics_report_path = output_dir / "reconstruction_metrics.json"

    if not input_path.exists():
        failure_reason = (
            f"Input file does not exist: {input_path}. Provide a valid video path."
        )
        logger.error(
            "Input validation failed",
            extra={"context": {"reason": failure_reason}},
        )
        ingest = IngestResult(input_path=input_path, input_hash="", output_dir=output_dir)
        metadata = MetadataResult(
            container={},
            streams=[],
            extracted_fields=[],
            missing_fields=FFPROBE_FIELDS,
            source="missing",
        )
        frame_result = FrameExtractionResult(
            frames_dir=output_dir / "frames",
            frame_count=0,
            fps=0.0,
        )
        run_report = build_run_report(
            ingest=ingest,
            metadata=metadata,
            frames=frame_result,
            backend=backend_name,
            params={"max_frames": max_frames},
            reconstruction=None,
            failure_reason=failure_reason,
            elapsed_seconds=0.0,
        )
        write_json_report(run_report_path, run_report)
        metrics_report = build_metrics_report(
            reconstruction=None,
            metadata=metadata,
            frame_result=frame_result,
            failure_reason=failure_reason,
        )
        write_json_report(metrics_report_path, metrics_report)
        return 2

    ingest = IngestResult(
        input_path=input_path,
        input_hash=hash_file(input_path),
        output_dir=output_dir,
    )

    frames_dir = output_dir / "frames"
    failure_reason = None
    try:
        metadata = extract_metadata(input_path, logger)
    except Exception as exc:  # noqa: BLE001 - surfaced in report for Phase 0
        failure_reason = f"Metadata extraction failed: {exc}"
        logger.error(
            "Metadata extraction failed",
            extra={"context": {"reason": failure_reason}},
        )
        metadata = MetadataResult(
            container={},
            streams=[],
            extracted_fields=[],
            missing_fields=FFPROBE_FIELDS,
            source="error",
        )

    try:
        frame_result = extract_frames(
            input_path=input_path,
            output_dir=frames_dir,
            max_frames=max_frames,
            logger=logger,
        )
    except Exception as exc:  # noqa: BLE001 - surfaced in report for Phase 0
        if failure_reason is None:
            failure_reason = f"Frame extraction failed: {exc}"
        logger.error(
            "Frame extraction failed",
            extra={"context": {"reason": str(exc)}},
        )
        frame_result = FrameExtractionResult(
            frames_dir=frames_dir,
            frame_count=0,
            fps=0.0,
        )

    backend = get_backend(backend_name)
    reconstruction = None

    if failure_reason is None:
        try:
            reconstruction = backend.run(
                images_dir=frames_dir,
                workspace_dir=output_dir / "colmap",
                metadata=metadata,
                logger=logger,
            )
        except BackendUnavailableError as exc:
            failure_reason = str(exc)
            logger.error(
                "Backend unavailable",
                extra={"context": {"backend": backend_name, "reason": failure_reason}},
            )
        except RuntimeError as exc:
            failure_reason = str(exc)
            logger.error(
                "Reconstruction failed",
                extra={"context": {"backend": backend_name, "reason": failure_reason}},
            )

    sparse_ply_path: Path | None = None
    if reconstruction and reconstruction.sparse_model_dir:
        try:
            sparse_ply_path = export_sparse_ply(
                reconstruction.sparse_model_dir, output_dir, logger
            )
        except RuntimeError as exc:
            failure_reason = str(exc)
            logger.error(
                "Export failed",
                extra={"context": {"reason": failure_reason}},
            )

    elapsed = perf_counter() - start_time

    run_report = build_run_report(
        ingest=ingest,
        metadata=metadata,
        frames=frame_result,
        backend=backend_name,
        params={"max_frames": max_frames},
        reconstruction=reconstruction,
        failure_reason=failure_reason,
        elapsed_seconds=elapsed,
    )
    write_json_report(run_report_path, run_report)

    metrics_report = build_metrics_report(
        reconstruction=reconstruction,
        metadata=metadata,
        frame_result=frame_result,
        failure_reason=failure_reason,
    )
    write_json_report(metrics_report_path, metrics_report)

    if failure_reason:
        logger.error(
            "Pipeline completed with errors",
            extra={\"context\": {\"run_report\": str(run_report_path), \"metrics\": str(metrics_report_path)}},
        )
        return 2

    summary_path = output_dir / "summary.json"
    summary_path.write_text(
        json.dumps({"ply": str(sparse_ply_path) if sparse_ply_path else None}, indent=2)
        + "\n",
        encoding="utf-8",
    )
    logger.info(
        "Pipeline completed",
        extra={\"context\": {\"output_dir\": str(output_dir), \"ply\": str(sparse_ply_path)}},
    )
    return 0
