# Clinical Boundary Mode (Draft)

Defines safeguards when operating near clinical workflows.

## Activation Criteria
- Handling PHI/PII or regulated datasets.
- Running jobs that could influence diagnostic or therapeutic decisions.

## Controls
- Enforce role-based access with detailed audit trails.
- Require dual validation sign-off before releasing results.
- Disable experimental modules lacking regulatory clearance.
- Treat Wave-2 provenance previews and workspace tagging as advisory only; clinical builds must add validated pipelines, signatures, and regulated storage.

## Documentation
- Record every Clinical Boundary session in `compliance-notes.md`.
- Maintain traceability artifacts for FDA/ISO audits.
- Note that the mainline Phase 2 build is research/education only; any clinical deployment requires a separately validated configuration.
