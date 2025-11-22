# Capabilities Registry

Master list of scientific and operational capabilities that LabOS offers.

## Table

| Capability ID | Name | Description | Module(s) involved | Phase | Status |
| --- | --- | --- | --- | --- | --- |
| core.experiment_model | Experiment registry | Dataclass-backed experiment records with JSON storage and audit hooks for create/status updates. | `labos.experiments`, `labos.storage`, `labos.audit` | 1 | implemented |
| core.dataset_registry | Dataset registry | File-backed dataset records capturing owner, dataset type, URI, tags, and metadata with audit emission. | `labos.datasets`, `labos.storage`, `labos.audit` | 1 | implemented |
| core.job_pipeline | Job runner + registry | Creates and executes jobs against registered module operations, persists results, and records audit events. | `labos.jobs`, `labos.modules`, `labos.audit`, `labos.config` | 1 | implemented |
| core.module_registry | Plugin loader | Registers `ModuleDescriptor` objects and exposes operations for scientific plugins; auto-loads built-in stubs. | `labos.modules.__init__` | 1 | implemented |
| core.method_metadata_registry | Provenance metadata | In-memory `ModuleMetadata` registry feeding “ⓘ Method & Data” UI surfaces with citations and limitations. | `labos.core.module_registry` | 1 | implemented |
| module.eims_fragmentation_stub | EI-MS fragmentation stub | Deterministic placeholder returning module-tagged dataset/audit payloads for EI-MS demos. | `labos.modules.eims.fragmentation_stub` | 2 | stub |
| module.pchem_calorimetry_stub | P-Chem calorimetry stub | Deterministic metadata emitter for calorimetry walkthroughs; no thermodynamics performed. | `labos.modules.pchem.calorimetry_stub` | 2 | stub |
| module.import_wizard_stub | Import wizard stub | Emits dataset/audit placeholders for data onboarding scenarios without touching real files. | `labos.modules.import_wizard.stub` | 2 | stub |
| ui.control_panel_modes | Control Panel modes | Streamlit Control Panel with Learner/Lab/Builder banners, tips, and mode-aware copy. | `labos.ui.control_panel` | 1 | implemented |
| ui.module_inspector | Module inspector | UI section exposing registered module descriptors/operations for safe inspection across modes. | `labos.ui.control_panel`, `labos.modules` | 1 | implemented |

## Maintenance Rules
- Registry updated whenever a capability is added, modified, or retired.
- Validation evidence linked to `VALIDATION_LOG.md` (Phase 1+).
