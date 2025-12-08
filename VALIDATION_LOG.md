# Validation Log

Document scientific validation activities once numerical or analytical logic ships.

| Date (UTC) | Component | Change Summary | Evidence |
| --- | --- | --- | --- |
| 2026-05-21T00:45:00Z | Core workflow integration | Pass – P-Chem and EI-MS workflows wired through Run buttons and CLI wrappers; job lineage and dataset/audit IDs validated end-to-end. | `python -m pytest tests/test_workflow_pipeline.py tests/test_workflow_jobs_integration.py` |
| 2026-05-21T00:35:00Z | Storage & audit stress | Pass – File-backed registries and JSONL audit log sustained repeated job runs without checksum drift or orphaned refs. | `python -m pytest tests/test_storage_in_memory.py tests/test_telemetry_logging.py` |
| 2026-05-21T00:25:00Z | Import Wizard provenance | Pass – Import Wizard workflows preserved dataset/experiment linkage and ModuleRegistry metadata across calorimetry/EI-MS ingest paths. | `python -m pytest tests/test_import_calorimetry.py tests/test_import_provenance.py tests/test_module_registry.py` |
| 2026-05-21T00:15:00Z | CLI/API integration | Pass – Demo data seeding and workflow execution exercised via new CLI commands and LabOSRuntime API wrappers. | Manual CLI/API session logs |
| 2026-05-21T00:05:00Z | Workflow + storage regression | Pass – Combined workflow, CLI, storage, and audit scenarios executed to cover stabilization work for Phase 2.5.3. | `python -m pytest tests/test_pchem_operations.py tests/test_ei_ms_basic_analysis.py tests/perf` |
| 2026-05-14T00:00:00Z | Telemetry logging | Added pytest coverage ensuring `log_event` serializes JSONL output without touching the filesystem and accumulates repeated calls in memory. | `python -m pytest tests/test_telemetry_logging.py` |
| 2026-03-07T00:00:00Z | Mode helper predicates | Added regression tests for mode resolution defaults and explicit mode overrides in control panel helpers. | `python -m pytest tests/test_ui_mode_helpers.py` |
| 2026-03-06T00:00:00Z | Security docs | Added UI input sanitization, unsafe content handling, and anti-eval guidance to security notes and compliance checklists. | Documentation review |
| 2025-11-25T23:37:01Z | Storage layer | Added unit tests for in-memory dataset, experiment, and job stores and confirmed job linkage stays disabled without an experiment store. | `PYTHONDONTWRITEBYTECODE=1 pytest tests/test_storage_in_memory.py` |
| 2026-03-06T00:00:00Z | Provenance docs | Updated PROVENANCE_GUIDE and compliance checklists to require method_name/primary_citation/dataset_citations and textbook attribution guidance. | Documentation review |
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
| 2025-11-23T12:45:00Z | Performance stubs | Added time-boxed workflow repetition and inline import runs to surface stability issues before heavier benchmarks. | `python -m pytest tests/perf` |
| 2025-11-25T00:59:30Z | Control Panel UI Tests | Added default-mode fallbacks, audit lookup, and dataset ID parsing coverage for mode helpers. | `python -m pytest tests/test_ui_mode_helpers.py` |
| 2025-11-23T12:00:00Z | P-Chem, EI-MS, Import validation | Added unit tests covering calorimetry stubs, ideal gas and ΔG helpers, EI-MS base peak/loss tagging, and calorimetry import column/validation paths. | `pytest tests/test_pchem_operations.py tests/test_ei_ms_basic_analysis.py tests/test_import_calorimetry.py` |
| 2025-11-23T18:00:00Z | Workflow lineage & registry | Added calorimetry workflow regression for Experiment/Job/DatasetRef/AuditEvent IDs and ModuleRegistry built-in key coverage. | `python -m pytest tests/test_workflow_experiment_lineage.py tests/test_module_registry.py` |

## 2025-11-27 11:26:38 -06:00 - self reviewed
- [SUCCESS] Build labos-dev image (logs\verify\20251127-112638\01_docker_build.log)
- [SUCCESS] Run unit tests (logs\verify\20251127-112638\02_unit_tests.log)
- [SUCCESS] Rate Dockerfile with Gordon (logs\verify\20251127-112638\03_docker_ai_rate.log)
- [SUCCESS] Start Streamlit container (logs\verify\20251127-112638\04_container_start.log)
- [SUCCESS] Analyze running container with Gordon (logs\verify\20251127-112638\05_docker_ai_analyze.log)
- [SUCCESS] Scan image with Docker Scout (logs\verify\20251127-112638\06_docker_scout.log)
- [SUCCESS] Log compose helper availability (logs\verify\20251127-112638\07_compose_helper.log)


## 2025-11-27 11:28:47 -06:00 - self reviewed
- [SUCCESS] Build labos-dev image (logs\verify\20251127-112847\01_docker_build.log)
- [SUCCESS] Run unit tests (logs\verify\20251127-112847\02_unit_tests.log)
- [SUCCESS] Rate Dockerfile with Gordon (logs\verify\20251127-112847\03_docker_ai_rate.log)
- [SUCCESS] Start Streamlit container (logs\verify\20251127-112847\04_container_start.log)
- [SUCCESS] Analyze running container with Gordon (logs\verify\20251127-112847\05_docker_ai_analyze.log)
- [SUCCESS] Scan image with Docker Scout (logs\verify\20251127-112847\06_docker_scout.log)
- [SUCCESS] Log compose helper availability (logs\verify\20251127-112847\07_compose_helper.log)


## 2025-12-07 19:01:46 -06:00 - local dev verification
- [SUCCESS] Unit tests passed (31 test files)
- [SUCCESS] Import checks passed

