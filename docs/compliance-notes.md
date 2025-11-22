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

## Phase 2 Traceability Notes
AuditEvent payloads (actor, action, timestamp, checksum pointer) directly reinforce ALCOA+ by preserving who performed which change, when it occurred, what the intent was, and where the original values are referenced. Registry calls that attach `AuditEvent` IDs to BaseRecord derivatives keep the chain intact across datasets, experiments, and jobs.

The ModuleRegistry catalogs source/version metadata for each method and feeds the Method & Data footer so rendered outputs carry module keys, names, citations, and stated limitations. This pairing of registry provenance and on-screen footers strengthens end-to-end traceability for method selection and downstream dataset/job creation.

Limitations: LabOS is currently a development/educational scaffold and has not been validated for clinical decision support. Controls such as user authentication, environment hardening, and formal verification remain future-phase tasks; outputs should not be used to guide patient care.

## 2025-11-22T15:00:00Z — Phase 2 Wave 2 provenance previews
- **Participants:** Compliance & Legal Bot (Phase 2), UI/Import/Test bots (asynchronous handoff)
- **Topic:** Wave-2 upgrades expose dataset/job/audit previews in the Control Panel and tighten workspace hooks to tag research artifacts while wiring import provenance into lineage helpers.
- **Actions:**
        - Note partial ALCOA+ improvement: users can inspect provenance before promoting data, but signatures/identity controls are still pending.
        - Flag manual UI verification for provenance previews and workspace tags until automated harnesses ship.
        - Restate boundary: no PHI/PII, no clinical decision support; research/education only despite improved traceability.
