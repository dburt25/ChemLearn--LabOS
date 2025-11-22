# Compliance Checklist

Use this list before merging or promoting work between phases.

## Data Integrity
- [ ] Every dataset/experiment/job change logged via `audit.record_event()` or `AuditLogger.record()`.
- [ ] BaseRecord derivatives attach audit IDs (`attach_audit_event`) before persisting.
- [ ] ALCOA+ evidence (who/what/when/why/original) captured in docs or logs.
- [ ] Git LFS enforced for binaries per `BINARY_ASSET_HANDLING.md`.

## Documentation
- [ ] CHANGELOG updated for repository-visible changes.
- [ ] VALIDATION_LOG updated whenever scientific logic changes.
- [ ] `compliance-notes.md` entry added for regulatory-relevant decisions (ModuleRegistry provenance, audit trail, workflow shifts).
- [ ] Compliance mapping references ModuleRegistry provenance + AuditEvent design decisions.

## Access & Safety
- [ ] Secrets remain outside the repo (env vars or secrets manager).
- [ ] Clinical Boundary Mode implications evaluated for new features.
- [ ] Role-based constraints cross-checked with `SWARM_PERMISSIONS_MATRIX.md`.
- [ ] Signature stub (`labos.core.signature.Signature`) applied before release notes that impact regulated data.
- [ ] ModuleRegistry descriptors include source/version metadata before activation.
