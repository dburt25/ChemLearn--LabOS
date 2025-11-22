# Compliance Checklist

Use this list before merging or promoting work between phases.

## Data Integrity
- [ ] Every dataset/experiment/job change logged via `AUDIT_LOG_FORMAT`.
- [ ] ALCOA+ evidence (who/what/when/why/original) captured in docs or logs.
- [ ] Git LFS enforced for binaries per `BINARY_ASSET_HANDLING.md`.

## Documentation
- [ ] CHANGELOG updated for repository-visible changes.
- [ ] VALIDATION_LOG updated whenever scientific logic changes.
- [ ] `compliance-notes.md` entry added for regulatory-relevant decisions.

## Access & Safety
- [ ] Secrets remain outside the repo (env vars or secrets manager).
- [ ] Clinical Boundary Mode implications evaluated for new features.
- [ ] Role-based constraints cross-checked with `SWARM_PERMISSIONS_MATRIX.md`.
