# Bot Permissions Matrix

Narrow, path-scoped privileges for each active/anticipated bot. "Allowed" paths are the outer limit—bots may self-restrict further. Forbidden lanes are absolute.

| Bot | Allowed Paths | Forbidden Paths | Purpose |
| --- | --- | --- | --- |
| Core Stability Bot | `labos/core/**`, `data/config/**` | `labos/ui/**`, `labos/modules/**`, `tests/**` | Maintain core models, storage primitives, registries, and config wiring.
| Module Wave Bot (EI-MS) | `labos/modules/eims/**`, `docs/ei_ms/**` | `labos/ui/**`, `labos/core/**`, other `labos/modules/**` | Extend EI-MS operations and metadata without touching UI or core internals.
| Module Wave Bot (PChem) | `labos/modules/pchem/**`, `docs/pchem/**` | `labos/ui/**`, `labos/core/**`, other `labos/modules/**` | Grow physical chemistry calculators within the PChem lane only.
| Module Wave Bot (Proteomics) | `labos/modules/proteomics/**` | `labos/ui/**`, `labos/core/**`, other `labos/modules/**` | Prototype proteomics routines and descriptors in isolation.
| Module Wave Bot (OrgChem) | `labos/modules/org_chem/**` | `labos/ui/**`, `labos/core/**`, other `labos/modules/**` | Iterate on organic chemistry helpers without cross-module imports.
| Import & Provenance Bot | `labos/modules/import_wizard/**`, `docs/PROVENANCE_GUIDE.md`, `docs/AUDIT_LOG_FORMAT.md` | `labos/ui/**`, `labos/core/**` (except stable registry APIs), non-import modules | Harden dataset ingest flows, provenance payloads, and descriptors.
| UI & Workspace Bot | `labos/ui/**` | `labos/core/**`, `labos/modules/**` | Refine Streamlit panels and workspace UX using published APIs only.
| Testing & Validation Bot | `tests/**`, `VALIDATION_LOG.md` | `labos/ui/**` (unless running UI smoke fixtures), module/core logic changes | Expand coverage and record evidence without altering implementations.
| Docs & Governance Bot | `docs/**`, `README.md`, `COMPLIANCE_CHECKLIST*.md`, `compliance-notes.md` | Any `*.py` code paths, `labos/ui/**`, `labos/modules/**`, `labos/core/**` | Update policy, governance, and contributor docs only.
| Automation & Release Bot | `.github/workflows/**`, `CHANGELOG.md` (version bumps only) | `labos/core/**`, `labos/modules/**`, `labos/ui/**` | CI, release packaging, and workflow automation; no product logic edits.
| Data & Storage Bot | `data/**` (non-source assets), `docs/DATA_ARCHITECTURE.md` | `labos/ui/**`, `labos/modules/**`, `labos/core/**` (code) | Migrate storage layouts/config; never modify executable code.
| Swarm Orchestrator Bot | `docs/SWARM_STATUS.md`, `docs/SWARM_GOVERNANCE.md`, `docs/SWARM_PERMISSIONS_MATRIX.md` | Any code paths, tests | Coordinate waves, assign lanes, and record status without editing code.
| Modularity & Permissions Doc Bot | `docs/MODULARITY_GUIDELINES.md`, `docs/BOT_PERMISSIONS_MATRIX.md`, `README.md` (links only) | Any `*.py` files, tests, UI/module/core code | Tighten modularity rules and clarify permissions for future swarms.

**Operating rules:**
- Cross-module collaboration happens through public Core APIs (registries, job runner, dataset/audit stores), never via direct imports.
- Any bot needing temporary access outside its lane must be re-slotted with an updated matrix entry before editing.
- When multiple bots share read access to the same path, only one may hold write access at a time.
