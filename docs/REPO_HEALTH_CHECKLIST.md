# Repo Health Checklist

Use this checklist before major merges or phase transitions.

## Documentation
- [ ] Vision and invariants reviewed this phase
- [ ] CHANGELOG updated (Phase 1+)
- [ ] Validation evidence logged
- [x] Storage abstraction defined (Phase 2)

## Code & Tests
- [ ] Lint/tests passing locally
- [x] Initial CI workflow created – runs tests on push/PR.
- [ ] Style checks automated (TODO)
- [ ] Coverage reports automated (TODO)
- [ ] Dependencies scanned for vulnerabilities (future phases)

## Compliance
- [ ] Audit log schema unchanged or reviewed
- [ ] Clinical Boundary Mode considerations documented where applicable

## Data Hygiene
- [ ] No raw PHI/PII committed
- [ ] Large binaries tracked via LFS
- [x] Data layout directories defined/seeded
