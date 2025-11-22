# Architecture Overview

Snapshot of the layered ChemLearn LabOS design.

## Layers
- **LabOS Core:** Python package providing configuration loading, audit logging, file-backed registries for experiments/jobs/datasets, and a CLI entry point (`labos`).
- **Scientific Modules:** domain-specific capabilities registered through `labos.modules` so each operation declares metadata and exposes deterministic entrypoints.
- **UI Shell:** multi-mode control panel plus future CLI/REST clients that call LabOS Core APIs.

## Cross-Cutting Concerns
- Compliance and audit logging wrap every action (see `AUDIT_LOG_FORMAT.md`).
- Data architecture enforces deterministic IDs and reproducible states using JSONL audit trails and JSON registries.
- Swarm governance coordinates concurrent contributors via `SWARM_PLAYBOOK.md` and `SWARM_PERMISSIONS_MATRIX.md`.

## Current Implementation Notes
- `LabOSConfig` centralizes directory layout and environment overrides.
- `AuditLogger` writes append-only JSONL files with chained checksums per UTC day.
- Registries persist one record per JSON file under `data/<domain>/`, keeping history in git-friendly structures.
- `LabOSRuntime` bundles config, audit, registries, and the job runner for CLI and future service entrypoints.

## Future Artifacts
- Sequence diagrams once interfaces stabilize.
- Deployment topologies after infra decisions.
