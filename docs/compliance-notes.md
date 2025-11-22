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

## 2025-11-22T12:00:00Z — ModuleRegistry provenance stubs
- **Participants:** Compliance & Legal Bot (async), Module Ops Bot (review)
- **Topic:** Documented ModuleRegistry discovery provenance so each descriptor references its origin repo/version.
- **Actions:**
	- Require ModuleRegistry entries to include descriptor metadata + audit hook before exposure in the UI.
	- Capture provenance summary inside compliance checklist for future verification.

## 2025-11-22T12:10:00Z — AuditEvent design refresh
- **Participants:** Compliance & Legal Bot
- **Topic:** Introduced `record_event()` helper plus BaseRecord audit hooks to ensure ALCOA+ trails survive across registries.
- **Actions:**
	- Mandate that registries attach audit IDs back onto stored records.
	- Track helper usage in CHANGELOG/VALIDATION_LOG to show rationale for investigators.

## 2025-11-22T12:20:00Z — Phase 1 development workflow guardrails
- **Participants:** Compliance & Legal Bot, Phase 1 Coordinator
- **Topic:** Defined lightweight workflow: audit event stub, signature placeholder, compliance docs update before merging.
- **Actions:**
	- Update compliance checklist to call out signatures, provenance, and log touchpoints.
	- Keep ALCOA+ reminder in CHANGELOG/VALIDATION_LOG for each compliance-impacting change.
