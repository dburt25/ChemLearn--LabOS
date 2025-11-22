# Clinical Boundary Mode (Draft)

Defines safeguards when operating near clinical workflows.

## Activation Criteria
- Handling PHI/PII or regulated datasets.
- Running jobs that could influence diagnostic or therapeutic decisions.

## Controls
- Enforce role-based access with detailed audit trails.
- Require dual validation sign-off before releasing results.
- Disable experimental modules lacking regulatory clearance.

## Documentation
- Record every Clinical Boundary session in `compliance-notes.md`.
- Maintain traceability artifacts for FDA/ISO audits.
