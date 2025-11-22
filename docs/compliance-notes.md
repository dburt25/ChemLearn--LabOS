# Compliance Notes Log

Use this file to capture regulatory considerations, decisions, and meeting summaries.

## Entry Template
- Date/Time (UTC)
- Participants / Roles
- Topic / Decision
- Actions / Owners

> Phase 0 placeholder — populate once compliance discussions begin.

## 2025-11-22T00:00:00Z — LabOS Core bootstrap
- **Participants:** Core Builder Bot, Compliance Bot (async review)
- **Topic:** Added LabOS core package (config, audit logger, registries, CLI) with JSONL audit trails and checksum chaining.
- **Actions:**
	- Enforce audit logging on dataset/experiment/job registries.
	- Require experiment IDs for `labos run-module` to keep provenance links intact.
