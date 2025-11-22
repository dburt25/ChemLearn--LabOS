# Swarm Permissions Matrix

Access levels for each bot role (RW = read/write, R = read only, - = no access). Bots may further restrict themselves within a directory, but they must not exceed the grants below.

| Role | labos/core/* | labos/ui/* | labos/modules/eims/* | labos/modules/pchem/* | labos/modules/import_wizard/* | labos/modules/proteomics/* | labos/modules/org_chem/* | labos/modules/simulation/* | labos/modules/ml/* | tests/* | docs/* | .github/workflows/* |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Core Builder Bot | RW | R | R | R | R | - | - | - | - | R | R | - |
| UI Integration Bot | R | RW | - | - | - | - | - | - | - | R | R | - |
| Workspace & Visualization Bot | R | RW | - | - | - | - | - | - | - | R | R | - |
| EI-MS Module Bot | R | R | RW | R | R | - | - | - | - | R | R | - |
| PChem Module Bot | R | R | R | RW | R | - | - | - | - | R | R | - |
| Import & Provenance Bot | RW (provenance helpers) | R | R | R | RW | - | - | - | - | R | R | - |
| Proteomics Module Bot | R | R | - | - | - | RW | R | - | - | R | R | - |
| OrgChem Module Bot | R | R | - | - | - | R | RW | - | - | R | R | - |
| Simulation Engine Bot | R | R | - | - | - | - | - | RW | R | R | R | - |
| ML Upgrade Bot | R | R | - | - | - | - | - | R | RW | R | R | - |
| CLI & Interface Bot | R | R | R | R | R | - | - | - | - | R | R | RW |
| Compliance & Legal Bot | R | R | - | - | - | - | - | - | - | - | RW | R |
| Testing & Validation Bot | R | R | R | R | R | R | R | R | R | RW | R | - |
| Data & Storage Bot | RW (config only) | - | - | - | - | - | - | - | - | R | RW | - |
| Swarm Orchestrator Bot | R | R | R | R | R | R | R | R | R | R | RW | - |

Update this matrix whenever roles or directories change. When multiple bots share `labos/ui/*` or other overlapping paths, the Swarm Orchestrator sequences their waves to prevent collisions.
