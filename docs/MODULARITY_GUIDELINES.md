# Modularity Guidelines

Principles for attaching new scientific capabilities to LabOS without destabilizing the core.

## Module Boundary Rules
- Each module lives under `labos/modules/<domain>/` with its own README and validation notes.
- Modules communicate with LabOS Core through the module registry plus documented APIs (experiment registry, job runner, dataset store).
- Module descriptors must be registered via `register_descriptor()` and expose stable `module_id` + operation names for CLI/UI use.
- No module may bypass audit logging or provenance recording; return JSON-serializable payloads that registries and UI panels can consume.

## Versioning & Compatibility
- Modules declare semantic versions and supported LabOS Core versions in their descriptors and accompanying docs.
- Breaking changes require updates to `CHANGE_TYPES.md`, roadmap docs, and, when user-visible, the `CHANGELOG.md`.

## Testing Expectations
- Provide deterministic sample data or reference calculations so regression tests can run headless.
- Record validation evidence in `VALIDATION_LOG.md` once tests or manual validations run.
- Keep `docs/METHOD_AND_DATA.md` synchronized with module metadata (citations, limitations, status).

## Security & Ethics
- Modules that ingest PHI/PII must operate in Clinical Boundary Mode (see `CLINICAL_BOUNDARY_MODE.md`).
- Sensitive compute (e.g., ML inference) must expose explainability hooks and traceable parameters.
