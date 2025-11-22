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

## [0.1.1] - 2025-11-22
### Fixed
- Ensured `render_control_panel()` executes when `streamlit run app.py` is invoked so the Control Panel always renders.
- Added a placeholder core smoke test that instantiates the exported Phase 0 dataclasses to guard against regressions.

## [0.1.2] - 2025-11-22
### Added
- `audit.record_event()` helper so bots can emit ALCOA-friendly JSONL entries without wiring an `AuditLogger` manually.
- Stub `Signature` dataclass plus BaseRecord hooks to capture intent/time/evidence for future electronic signatures.
### Changed
- Registries now attach audit event IDs back onto Experiment, Dataset, and Job records for traceability.
- Compliance docs (checklist, notes, validation log) updated to reflect ModuleRegistry provenance expectations and Phase 1 workflow.
