# Compliance Overview (Phase 2 Baseline)

## Scope
Summarizes how current LabOS scaffolding aligns with FDA/ISO/ALCOA+ expectations during Phase 2. This is a living document; future phases will add validation and safety controls.

## Core Controls
- **AuditEvent Logging:** All dataset/experiment/job mutations route through `audit.record_event()` / `AuditLogger.record()` to capture actor, action, timestamp, payload hash, and linkage back to records.
- **Registries with Deterministic IDs:** Experiment, Job, and Dataset registries issue stable IDs and store the audit event reference to maintain traceable provenance across artifacts.
- **ModuleRegistry Provenance:** Module descriptors require source repository/version metadata and feed Method & Data footers so outputs disclose method lineage, citations, and declared limitations.
- **Documentation Cadence:** `CHANGELOG.md`, `VALIDATION_LOG.md`, and `docs/compliance-notes.md` are updated when audit patterns, module provenance, or scientific logic changes.

## Gaps & Future Work
- Formal authentication/authorization, Clinical Boundary Mode enforcement, and signing of regulated exports are placeholders awaiting later phases.
- Git LFS enforcement, retention policies, and coverage thresholds need automation before validation.
- No clinical validation has been performed; LabOS remains a development/education platform until regulated testing is complete.
