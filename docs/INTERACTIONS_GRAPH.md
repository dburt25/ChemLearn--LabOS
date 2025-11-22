# Interactions Graph

High-level view of how LabOS components communicate.

## Core flow (Phase 1–2 skeleton)

```
Experiment -> Job -> Module Operation -> Result Artifact
                          |                     |
                          v                     v
                    ModuleRegistry        DatasetRef/Result JSON
                          |                     |
                          v                     v
                    AuditEvent log   ->   DatasetRegistry entry
```

- **ExperimentRegistry** persists intent and purpose, linking user context to downstream jobs.
- **JobRunner/JobRegistry** creates jobs bound to a module operation, executes via `ModuleRegistry`, and persists result JSON paths.
- **ModuleRegistry** (scientific plugins) resolves operations; stubs return structured `dataset` + `audit` payloads for provenance.
- **DatasetRegistry** stores dataset metadata (owner, URI, tags, module provenance) when stubs or future modules emit DatasetRefs.
- **AuditLogger** records every registry write and job transition to maintain ALCOA+ traces.

## UI touchpoints

```
Control Panel (Learner/Lab/Builder)
    -> loads registries from LabOSRuntime
    -> displays experiments/jobs/datasets tables
    -> Module Inspector pulls ModuleRegistry + ModuleMetadata
```

- Mode banners/tips in the Streamlit Control Panel adjust copy but all rely on the same registries.
- The Module Inspector surfaces both executable operations (`ModuleDescriptor`) and provenance metadata (`ModuleMetadata`) for transparency.
- Draft experiment creation in UI is read-only until persisted via CLI/API, reinforcing separation between demo mode and audit-backed records.

## Module and import stubs

```
ModuleDescriptor (auto-registered)
    compute(params) -> {module_key, dataset, audit, status}
```

- EI-MS fragmentation, P-Chem calorimetry, and Import Wizard stubs are auto-loaded; each emits deterministic dataset/audit payloads tagged with `module_key` for downstream provenance.
- Stubs currently mark status as `not-implemented`, signaling educational/demo use only.
- Import Wizard helpers now provide schema inference + dataset preview structures that can be promoted into DatasetRegistry entries once jobs wire them in.

## Import wizard & data provenance flow

```
Learner uploads table/sample -> Import Wizard helpers -> DatasetRef + AuditEvent -> DatasetRegistry -> Control Panel (Method & Data)
```

- Schema inference ensures downstream modules understand column intent before processing.
- `labos.core.provenance` links imported datasets back to experiments/jobs so audits display full lineage.
- Upcoming waves will let Jobs promote import outputs into the DatasetRegistry and show provenance inline in the UI footer.

## Data and compliance surfaces

- **Storage**: JSONFileStore under `LabOSConfig` directories backs experiment/job/dataset registries; job results serialize module outputs for inspection.
- **AuditEvent linkage**: Registries attach audit IDs to records upon create/update, enabling traceability across Experiment → Job → Dataset transitions.
- **ModuleMetadata**: Separate from executable descriptors; supplies citations, limitations, and reference URLs for UI provenance panels.

## Swarm orchestration overlay

- Governance docs (`SWARM_PLAYBOOK.md`, `SWARM_PERMISSIONS_MATRIX.md`, `SWARM_STATUS.md`) coordinate which bots may touch each subsystem at any moment.
- Permissions ensure only one bot writes to a path (e.g., `labos/ui/*`) per wave while others operate on disjoint subsystems.
- Swarm orchestration outputs feed directly into the Control Panel roadmap and future CLI tooling so automation stays aligned with compliance rules.

## Planned extensions

- Enrich DatasetRef modeling so module outputs can be promoted into the DatasetRegistry automatically.
- Annotate interactions with protocols (CLI/REST/events) once Phase 2+ services and automation mature.
