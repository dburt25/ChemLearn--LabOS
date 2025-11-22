# Swarm Governance

Policies that keep the ChemLearn LabOS bot collective aligned with mission and compliance.

## Decision Hierarchy
1. **Invariants:** non-negotiable (see `INVARIANTS.md`).
2. **Vision & Phase Plans:** define what to build next.
3. **Role Leads:** coordinate within their domains and escalate conflicts.

## Conflict Resolution
- Document the issue in `REPO_HEALTH_CHECKLIST.md`.
- Seek consensus between relevant role leads; if unresolved, default to compliance-first choice.

## Transparency Requirements
- Each bot logs intent, actions, and results in their PR descriptions and docs.
- Major architectural decisions recorded in `MASTER_BLUEPRINT_INDEX.md` and referenced from `CHANGELOG.md` (future phase).

## Accountability
- Every commit must map to a tracked task or issue.
- Validation evidence and audit trails remain mandatory even for internal tooling.

## Roles
- **Swarm Orchestrator Bot:** owns scheduling, wave composition, and concurrency gates. Maintains `SWARM_STATUS.md`, `SWARM_PLAYBOOK.md`, and aligns with `SWARM_PERMISSIONS_MATRIX.md` to prevent path conflicts.
- **Builder/Module Bots:** execute scoped changes within their subsystems while adhering to permissions and validation rules. Defer to Orchestrator for timing, parallelism, and escalation when conflicts appear.

## Preconditions for New Bots/Waves
- Each new bot must confirm scope against `SWARM_PERMISSIONS_MATRIX.md`, consult `MASTER_BLUEPRINT_INDEX.md` for architectural intent, and check `SWARM_STATUS.md` for current wave timing.
- Before starting a wave, ensure prior wave validation is complete, tests are passing, and permissions updates (if any) are merged.

## Pause Rules
- Humans (or the Orchestrator) should pause launching new waves when:
  - Regression tests are failing or validation evidence is missing.
  - Merge conflicts or ownership overlap exist in the targeted directories.
  - Compliance/doc updates lag behind implemented features.
- Resume only after conflicts are resolved, validation rerun, and governance docs synchronized.
