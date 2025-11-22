# Development Vision Guide

Bridges the aspirational `VISION.md` with day-to-day implementation choices.

## Guiding Themes
- Build LabOS Core first: deterministic IDs, auditability, and reproducibility.
- Every feature must be explainable to undergraduate learners yet trustworthy for clinicians.
- Prefer plain Python, minimal dependencies, and scripted tooling for ease of validation.

## Execution Principles
1. Treat registries (experiments, jobs, datasets) as the single source of truth.
2. Require audit logging for every persistent change.
3. Keep compliance artifacts (CHANGELOG, VALIDATION_LOG, `compliance-notes.md`) current with each increment.
4. Defer scientific heuristics until validation criteria are documented.

## Implementation Roadmap Snapshot
- Phase 1: Ship LabOS core package, CLI, and audit logging hooks.
- Phase 2: Harden data services, provenance pipelines, and CLI automation.
- Phase 3+: Layer scientific modules, UI shells, and ML upgrades per `PHASES_OVERVIEW.md`.
