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
