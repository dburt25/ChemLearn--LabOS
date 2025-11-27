# Bot Permissions Matrix

Narrow, path-scoped privileges for each active/anticipated bot. "Allowed" paths are the outer limit—bots may self-restrict further. Forbidden lanes are absolute. Phase 2.5.3 hardening wave keeps roles separated as **Core**, **Modules**, **UI**, **Docs**, **Tests**, and **Automation/Data**.

| Bot | Role | Allowed Paths | Forbidden Paths | Purpose |
| --- | --- | --- | --- | --- |
| Core Stability Bot | Core | `labos/core/**`, `data/config/**` | `labos/ui/**`, `labos/modules/**`, `tests/**` | Maintain core models, storage primitives, registries, and config wiring.
| Module Wave Bot (EI-MS & Spectroscopy) | Modules | `labos/modules/eims/**`, `labos/modules/spectroscopy/**`, `docs/ei_ms/**`, `docs/spectroscopy/**` | `labos/ui/**`, `labos/core/**`, other `labos/modules/**` | Consolidate EI-MS and spectroscopy operations/metadata without touching UI or core internals.
| Module Wave Bot (PChem) | Modules | `labos/modules/pchem/**`, `docs/pchem/**` | `labos/ui/**`, `labos/core/**`, other `labos/modules/**` | Grow physical chemistry calculators within the PChem lane only.
| Module Wave Bot (Proteomics) | Modules | `labos/modules/proteomics/**` | `labos/ui/**`, `labos/core/**`, other `labos/modules/**` | Prototype proteomics routines and descriptors in isolation.
| Module Wave Bot (OrgChem) | Modules | `labos/modules/org_chem/**` | `labos/ui/**`, `labos/core/**`, other `labos/modules/**` | Iterate on organic chemistry helpers without cross-module imports.
| Import & Provenance Bot | Modules | `labos/modules/import_wizard/**`, `docs/PROVENANCE_GUIDE.md`, `docs/AUDIT_LOG_FORMAT.md` | `labos/ui/**`, `labos/core/**` (except stable registry APIs), non-import modules | Harden dataset ingest flows, provenance payloads, and descriptors.
| UI & Workspace Bot | UI | `labos/ui/**` | `labos/core/**`, `labos/modules/**` | Refine Streamlit panels and workspace UX using published APIs only.
| Testing & Validation Bot | Tests | `tests/**`, `VALIDATION_LOG.md` | `labos/ui/**` (unless running UI smoke fixtures), module/core logic changes | Expand coverage and record evidence without altering implementations.
| Docs & Governance Bot | Docs | `docs/**`, `README.md`, `COMPLIANCE_CHECKLIST*.md`, `compliance-notes.md` | Any `*.py` code paths, `labos/ui/**`, `labos/modules/**`, `labos/core/**` | Update policy, governance, and contributor docs only.
| Automation & Release Bot | Automation | `.github/workflows/**`, `CHANGELOG.md` (version bumps only) | `labos/core/**`, `labos/modules/**`, `labos/ui/**` | CI, release packaging, and workflow automation; no product logic edits.
| Data & Storage Bot | Data | `data/**` (non-source assets), `docs/DATA_ARCHITECTURE.md` | `labos/ui/**`, `labos/modules/**`, `labos/core/**` (code) | Migrate storage layouts/config; never modify executable code.
| Swarm Orchestrator Bot | Docs | `docs/SWARM_STATUS.md`, `docs/SWARM_GOVERNANCE.md`, `docs/SWARM_PERMISSIONS_MATRIX.md` | Any code paths, tests | Coordinate waves, assign lanes, and record status without editing code.
| Modularity & Permissions Doc Bot | Docs | `docs/MODULARITY_GUIDELINES.md`, `docs/BOT_PERMISSIONS_MATRIX.md`, `README.md` (links only) | Any `*.py` files, tests, UI/module/core code | Tighten modularity rules and clarify permissions for future swarms.

**Operating rules:**
- Cross-module collaboration happens through public Core APIs (registries, job runner, dataset/audit stores), never via direct imports.
- Any bot needing temporary access outside its lane must be re-slotted with an updated matrix entry before editing.
- When multiple bots share read access to the same path, only one may hold write access at a time.
