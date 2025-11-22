# LabOS Bot Swarm – Phase 1 Initialization

This document defines the starting conditions for all bots working inside the ChemLearn LabOS repository.

## Purpose of Phase 1
- Extend the Phase 0 skeleton into a functional LabOS Core
- Strengthen the Control Panel UI (Learner / Lab / Builder)
- Establish module architecture for scientific tools (EI-MS, PChem, etc.)
- Begin the provenance (Method & Data) system
- Add a basic test suite
- Add structured entries to CHANGELOG and VALIDATION_LOG

## Global Rules
All bots MUST obey:
- docs/AGENT_GLOBAL_INSTRUCTIONS.md
- VISION.md
- DEVELOPMENT_VISION_GUIDE.md
- DEVELOPMENT_GUIDE.md
- COMPLIANCE_CHECKLIST.md
- CHANGELOG.md
- VALIDATION_LOG.md

## Phase 1 Deliverables (across all bots)
1. A working “Experiment → Job → Dataset” pipeline (stubbed logic acceptable)
2. A professional, mode-aware UI supporting:
   - Learner Mode (explanations, tooltips)
   - Lab Mode (clean, efficient tools)
   - Builder Mode (developer tools)
3. Module Registry enriched with:
   - Method name
   - Primary citation
   - Dataset citations
   - Limitations
4. Basic tests that instantiate:
   - Experiment
   - Job
   - DatasetRef
   - ModuleMetadata
5. Functional placeholders for:
   - EI-MS engine
   - PChem tools
   - Data Import Wizard (planned stubs only)
6. Compliance logging hooks (stubs)

Phase 1 ends when:
- The Control Panel shows experiments, jobs, datasets, modules, and method metadata.
- Tests run and pass.
- CHANGELOG and VALIDATION_LOG have Phase 1 entries.
