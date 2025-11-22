# Compliance Checklist

Use this list before merging or promoting work between phases. Status tags: ✅ DONE (Phase 2 baseline), ◐ PARTIAL, ☐ TODO (future phase).

## Data Integrity & Logging
- ✅ Every dataset/experiment/job change logged via `audit.record_event()` / `AuditLogger.record()` using `AuditEvent` payloads (Phase 2 baseline).
- ✅ BaseRecord derivatives attach audit IDs (`attach_audit_event`) before persisting to keep records linked to their audit events.
- ◐ ALCOA+ evidence (who/what/when/why/original) captured in docs or logs; user attribution and tamper-evident controls remain future hardening items.
- ◐ Experiment / Job / Dataset registries stabilized with deterministic IDs; future phases must validate persistence backends and enforce retention windows.
- ☐ Git LFS enforced for binaries per `BINARY_ASSET_HANDLING.md` (policy tracked but enforcement automation pending).

## Provenance & ModuleRegistry
- ✅ ModuleRegistry descriptors include source/version metadata before activation to support method provenance.
- ◐ Method & Data footer renders module key/name plus limitations where available; ensure consistent UI surfacing in all modes (future UI pass).
- ◐ Registry lookups should emit producing module IDs alongside jobs/datasets; extend coverage for downstream pipelines.

## Documentation & Traceability
- ✅ CHANGELOG updated for repository-visible changes.
- ✅ VALIDATION_LOG updated whenever scientific logic changes.
- ✅ `compliance-notes.md` entry added for regulatory-relevant decisions (ModuleRegistry provenance, audit trail, workflow shifts).
- ◐ Compliance mapping references ModuleRegistry provenance + AuditEvent design decisions; broaden mapping as additional controls land.

## Testing & Coverage
- ◐ Phase 2 baseline tests cover dataclass serialization, registry wiring, and audit logging helpers; expand to scientific stubs and provenance rendering.
- ☐ Establish minimal coverage threshold and regression gates for compliance-critical modules (Phase 3+).

## Access & Safety
- ✅ Secrets remain outside the repo (env vars or secrets manager).
- ◐ Clinical Boundary Mode implications evaluated for new features; formal safety case to be drafted in later phases.
- ✅ Role-based constraints cross-checked with `SWARM_PERMISSIONS_MATRIX.md` when introducing new capabilities.
- ◐ Signature stub (`labos.core.signature.Signature`) applied before release notes that impact regulated data; production signature policy TBD.
