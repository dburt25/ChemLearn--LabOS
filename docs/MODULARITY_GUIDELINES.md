# Modularity Guidelines

Principles for attaching new scientific capabilities to LabOS without destabilizing the core.

## Module Boundary Rules
- Each module lives under `chemlearn_modules/<domain>/` with its own README and validation notes.
- Modules communicate with LabOS Core through documented APIs (experiment registry, job runner, dataset store).
- No module may bypass audit logging or provenance recording.

## Versioning & Compatibility
- Modules declare semantic versions and supported LabOS Core versions.
- Breaking changes require updates to `CHANGE_TYPES.md` and the roadmap.

## Testing Expectations
- Provide golden datasets or reference calculations for regression tests.
- Record validation evidence in `VALIDATION_LOG.md` once Phase 1+ enables testing.

## Security & Ethics
- Modules that ingest PHI/PII must operate in Clinical Boundary Mode (see `CLINICAL_BOUNDARY_MODE.md`).
- Sensitive compute (e.g., ML inference) must expose explainability hooks.
