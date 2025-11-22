# Data Architecture (Draft)

Outlines how experiments, jobs, datasets, and audit logs flow through storage tiers.

## Storage Layers
- **Hot Tier:** Active experiments/jobs stored in transactional DB.
- **Warm Tier:** Versioned datasets and artifacts managed via Git LFS + object storage.
- **Cold Tier:** Long-term archives, regulatory exports, and immutable backups.

## Directories (Phase 0 placeholders)
- `data/experiments/` — structured metadata exports.
- `data/jobs/` — job manifests and run histories.
- `data/datasets/` — curated datasets (never raw PHI without controls).
- `data/audit/` — signed audit bundles.
- `data/examples/` — instructional samples for learners.
- `data/feedback/` — anonymized qualitative feedback.

## Governance Hooks
- Every write operation logs to the audit stream.
- Data classified per sensitivity; Clinical Boundary Mode enforces stricter policies.
- Retention schedules tracked alongside storage tier metadata.
