# Validation Log

Document scientific validation activities once numerical or analytical logic ships.

| Date (UTC) | Component | Change Summary | Evidence |
| --- | --- | --- | --- |
| 2025-11-22T00:00:00Z | Streamlit Control Panel | Verified `streamlit run app.py` renders the control panel header/sections and placeholder metrics. | Manual run + Streamlit console output |
| 2025-11-22T00:00:00Z | Core dataclasses | `python -m unittest discover -s tests` (4 tests) covering placeholder instantiations. | Test log in workspace terminal |
| 2025-11-22T12:15:00Z | Audit helpers | Desk review: confirmed `record_event()` writes chained checksums and BaseRecord `attach_audit_event` updates ALCOA trail. | Compliance & Legal Bot sign-off (docs/compliance-notes.md) |
| 2025-11-22T12:30:00Z | Core objects | Phase 1 – core objects instantiation successful. | `python -m unittest tests.test_core_objects` |
| 2025-11-22T12:32:00Z | Control Panel UI | Phase 1 – Control Panel renders without error. | `python -m unittest tests.test_module_registry.ControlPanelSmokeTest` |
| 2025-11-22T13:00:00Z | Module Registry | Phase 2 – Wave 1 stubs registered (EI-MS, P-Chem, Import Wizard) and metadata tests pass. | `python -m unittest tests.test_module_registry` |
| 2025-11-22T12:40:00Z | Control Panel Workspace | Verified the new Workspace / Drawing Tool section renders in Learner/Lab/Builder modes via `streamlit run app.py` smoke test. | Manual Streamlit run |
| 2025-11-22T14:30:00Z | Module metadata | Desk review: standardized placeholder citations/limitations and documented provenance expectations. | Documentation review (no automated tests) |
| 2025-11-22T08:11:34Z | Testing Suite | Phase 2 – Added core object invariants, module stub smoke tests, and registry metadata coverage. | `python -m pytest tests` (stub outputs only; no real physics/ingestion performed) |
| 2025-11-22T14:00:00Z | Workflow helpers | Desk check: instantiated `create_experiment_with_job`, attached datasets, and emitted audit events for manual inspection. | Manual interactive session |
| 2025-11-22T15:00:00Z | Workspace / Drawing Tool | Manual Streamlit run confirmed notes, upload field, and experiment tag input render with mode-aware guidance and summary. | `streamlit run app.py` (manual UI check) |
| 2025-11-22T15:00:00Z | Import provenance | Added provenance linkage tests for import wizard stub and workflow helpers. | `python -m unittest tests.test_import_provenance tests.test_scientific_modules` |
| 2025-11-22T15:05:00Z | Phase 2 – Wave 2 provenance/UI | Development/educational validation only: reran `python -m unittest tests.test_scientific_modules tests.test_module_registry` plus manual UI review of dataset/job/audit previews and workspace hooks. Clinical use not validated. | Manual UI check + targeted test command |
| 2025-11-22T15:45:00Z | Testing & Validation | Phase 2 – Wave 2 repo review: `python -m unittest` (full suite) blocked by missing `streamlit`; targeted `python -m unittest tests.test_scientific_modules tests.test_module_registry` (5 tests) succeeded verifying stub + registry coverage. | Terminal logs for both commands (Streamlit import error + passing targeted suite) |
| 2025-11-22T17:00:00Z | Testing & Validation | Resolved import stub conflict and added Streamlit guards so `python -m unittest` (15 tests, including `tests.test_import_provenance`) now passes in clean envs without installing Streamlit. | `python -m unittest` terminal log |
| 2025-11-22T22:05:51Z | Workflow pipeline tests | Added end-to-end calorimetry run_module_job coverage for Experiment/Job/DatasetRef/AuditEvent lineage and WorkflowResult shape regression. | \`python -m unittest tests.test_workflow_pipeline\` |
| 2025-11-23T00:00:00Z | Compliance & Provenance Docs | Updated COMPLIANCE_CHECKLIST.md, compliance-notes.md, and docs/PROVENANCE_GUIDE.md alongside prior Bot 7/8 validation runs to keep provenance guidance aligned with test coverage. | Documentation review (no automated tests) |

| 2025-11-23T00:00:00Z | Control Panel UI Tests | Added lightweight mode/helper coverage for mode tips, dataset/job labels, and truncation without requiring Streamlit. | `python -m pytest tests/test_ui_mode_helpers.py` |
| 2025-11-23T10:00:00Z | Core workflow & module registry | Added calorimetry/EI-MS workflow lineage assertions (Experiment/Job/DatasetRef/AuditEvent) and verified builtin module registry keys. | `python -m unittest tests.test_workflow_jobs_integration tests.test_module_registry` |
| 2025-11-25T00:59:30Z | Control Panel UI Tests | Added default-mode fallbacks, audit lookup, and dataset ID parsing coverage for mode helpers. | `python -m pytest tests/test_ui_mode_helpers.py` |
| 2025-11-23T18:00:00Z | Workflow lineage & registry | Added calorimetry workflow regression for Experiment/Job/DatasetRef/AuditEvent IDs and ModuleRegistry built-in key coverage. | `python -m pytest tests/test_workflow_experiment_lineage.py tests/test_module_registry.py` |
