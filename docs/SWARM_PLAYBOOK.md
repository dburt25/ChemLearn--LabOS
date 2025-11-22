# Swarm Playbook

Operating procedures for coordinating multiple ChemLearn LabOS bots.

## Role Declaration
- Each bot states its role, scope, and forbidden zones before editing.
- Roles link to `SWARM_PERMISSIONS_MATRIX.md` for quick reference.

## Collaboration Cycle
1. Read latest docs and open issues.
2. Draft a plan with scoped tasks and compliance considerations.
3. Execute minimal, reviewable changes.
4. Update CHANGELOG, validation notes, and relevant docs.

## Communication Norms
- Prefer deterministic, reproducible instructions.
- Highlight blockers and dependencies explicitly.
- Assume concurrent bots: avoid massive refactors without coordination.

## Safety Rules
- No deletion of artifacts without audit trail.
- All code changes accompanied by tests (once phases allow).
- Sensitive data never leaves secure storage paths.
