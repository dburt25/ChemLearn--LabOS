# Changelog

All notable changes will be documented in this file per `CHANGE_TYPES.md`.

## [0.1.0] - 2025-11-22
### Added
- LabOS Core Python package with configuration loader, audit logger, registries, runtime facade, and CLI entry point.
- JSONL audit log implementation with chained checksums as described in `docs/AUDIT_LOG_FORMAT.md`.
- File-backed dataset, experiment, and job registries plus a job runner that enforces experiment/job pairing.
- Minimal CLI commands: `labos init`, `labos new-experiment`, `labos register-dataset`, and `labos run-module`.
- Foundational documentation set (Development Vision Guide, Compliance Checklist, universal overview) to satisfy global context requirements.
- Editable packaging (`pyproject.toml`) and unit tests covering registries and job execution.
