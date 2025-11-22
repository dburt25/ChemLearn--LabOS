# Data Architecture (Draft)

Outlines how experiments, jobs, datasets, and audit logs flow through storage tiers.

## Storage Layers
- **Hot Tier:** Active experiments/jobs stored in transactional DB.
- **Warm Tier:** Versioned datasets and artifacts managed via Git LFS + object storage.
- **Cold Tier:** Long-term archives, regulatory exports, and immutable backups.

## Data Layout Conventions (Phase 2)
- `data/raw/` — first-touch ingest; keep immutable snapshots and avoid PHI/PII without controls.
- `data/processed/` — cleaned, validated derivatives ready for experiments and jobs.
- `data/results/` — job outputs, reports, figures, and derived metrics.
- `data/logs/` — structured run logs and debugging traces for local development.
- `data/feedback/` — anonymized qualitative feedback from learners.

The `DatasetRef.path_hint` field can point into these logical directories to suggest where a dataset
originates or should be materialized (e.g., `data/processed/exp123/features.parquet`). Future phases
will bind these hints to real storage backends and enforce retention/classification policies per
tier.

## Governance Hooks
- Every write operation logs to the audit stream.
- Data classified per sensitivity; Clinical Boundary Mode enforces stricter policies.
- Retention schedules tracked alongside storage tier metadata.
