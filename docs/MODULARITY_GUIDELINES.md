# Modularity Guidelines

Principles for attaching new scientific capabilities to LabOS without destabilizing the core.

## Layer Definitions
- **Core:** `labos/core/**` – domain models, storage, registries, audit logging, and shared configuration utilities.
- **Modules:** `labos/modules/<domain>/**` – scientific capabilities that plug into the ModuleRegistry and job runner using stable descriptors.
- **UI:** `labos/ui/**` – Streamlit control panel, workspace, inspectors, and presentation-only glue to orchestrate core + modules.
- **CLI/API:** `labos/cli.py`, runtime entry points, and any external API shims that invoke Core + ModuleRegistry surfaces.
- **Tests:** `tests/**` plus targeted fixtures alongside code under test.
- **Docs:** `docs/**`, `README.md`, and related governance/compliance notes.

## Allowed Import Directions
- Core has no upstream dependencies on Modules or UI. It may expose extension points (registries, storage helpers) consumed downstream, but **core → NO UI** imports remain disallowed.
- Modules may import Core interfaces and shared utilities but must **not** import UI or other modules directly (**modules → NO UI**). Cross-module calls go through the ModuleRegistry, job runner, or shared data contracts.
- UI may import Core public APIs and Module descriptors/registrations to render operations but must not reach into module internals or private Core storage layers (**UI → only public APIs such as ModuleRegistry, workflows, runtime surface**).
- CLI/API layers may call Core runtime helpers and public ModuleRegistry/Workflow APIs only; they must not import UI or module internals directly.
- Tests may import their targets plus lightweight fixtures; avoid reaching across layers except via public interfaces.
- Docs reference code symbols by name only and should not be used as a source of runtime configuration.

## Module Boundary Rules
- Each module lives under `labos/modules/<domain>/` with its own README and validation notes.
- Modules communicate with LabOS Core through the module registry plus documented APIs (experiment registry, job runner, dataset store).
- Module descriptors must be registered via `register_descriptor()` and expose stable `module_id` + operation names for CLI/UI use.
- Modules should never directly import UI components, private Core storage internals, or sibling module code; use public APIs and data payloads instead.
- No module may bypass audit logging or provenance recording; return JSON-serializable payloads that registries and UI panels can consume.

## Versioning & Compatibility
- Modules declare semantic versions and supported LabOS Core versions in their descriptors and accompanying docs.
- Breaking changes require updates to `CHANGE_TYPES.md`, roadmap docs, and, when user-visible, the `CHANGELOG.md`.
- When Core interfaces change, provide backwards-compatible adapters or deprecation paths before removing old contracts.

## Testing Expectations
- Provide deterministic sample data or reference calculations so regression tests can run headless.
- Record validation evidence in `VALIDATION_LOG.md` once tests or manual validations run.
- Keep `docs/METHOD_AND_DATA.md` synchronized with module metadata (citations, limitations, status).

## Security & Ethics
- Modules that ingest PHI/PII must operate in Clinical Boundary Mode (see `CLINICAL_BOUNDARY_MODE.md`).
- Sensitive compute (e.g., ML inference) must expose explainability hooks and traceable parameters.
