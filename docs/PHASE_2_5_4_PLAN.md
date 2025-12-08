# Phase 2.5.4 Implementation Plan - BOT SWARM Activation

## Overview
Phase 2.5.3 delivered hardened storage, workflow integration tests, module registration standards, comprehensive UI wiring, and mode documentation. Phase 2.5.4 focuses on **production readiness** and **feature completion** per VISION.md.

## Current State Assessment (December 7, 2025)
- ✅ 40 tests passing (33 core + 7 integration)
- ✅ Storage hardened (locking, backups, checksums)
- ✅ All modules executable via UI + CLI
- ✅ Module registration standardized
- ✅ Modes documented (Learner/Lab/Builder)
- ✅ CLI/API parity verified

## BOT SWARM SLOT ALLOCATION

Following SWARM_STATUS.md governance (max 6 concurrent bots):

### Slot 1: Core Schema / Workflow Bot
**Objective:** Enhanced workflow orchestration and experiment lifecycle management
**Tasks:**
1. Add experiment state transitions (draft → running → completed → archived)
2. Implement job retry/resume capability
3. Add dataset versioning support
4. Create workflow composition helpers (chain jobs)
5. Add experiment templates system

**Files:** `labos/core/experiments.py`, `labos/core/jobs.py`, `labos/core/workflows.py`

---

### Slot 2: EI-MS Module Bot
**Objective:** Expand EI-MS capabilities beyond basic fragmentation
**Tasks:**
1. Add isotope pattern recognition
2. Implement neutral loss detection
3. Create fragment tree visualization data
4. Add database matching stub (NIST-like)
5. Enhance annotation with chemical intelligence

**Files:** `labos/modules/ei_ms/**`, `docs/ei_ms/**`

---

### Slot 3: PChem Module Bot
**Objective:** Expand physical chemistry module portfolio
**Tasks:**
1. Add thermodynamics calculators (Gibbs free energy, equilibrium constants)
2. Create kinetics helpers (rate laws, Arrhenius)
3. Implement ideal gas law suite
4. Add error propagation utilities
5. Create batch processing templates

**Files:** `labos/modules/pchem/**`, `docs/pchem/**`

---

### Slot 4: UI / Control Panel Bot
**Objective:** Polish UI/UX and add interactive features
**Tasks:**
1. Implement experiment comparison view
2. Add dataset preview/download capabilities
3. Create job queue management interface
4. Add real-time job progress tracking
5. Implement search/filter across all sections

**Files:** `labos/ui/**`

---

### Slot 5: Testing & Validation Bot
**Objective:** Expand test coverage and add CI/CD
**Tasks:**
1. Add UI integration tests (Streamlit testing framework)
2. Create performance benchmarks
3. Add mutation testing for core logic
4. Implement contract testing for module registry
5. Set up GitHub Actions CI workflow

**Files:** `tests/**`, `.github/workflows/**`

---

### Slot 6: Docs & Compliance Bot
**Objective:** Complete documentation and prepare for Phase 3
**Tasks:**
1. Create Getting Started tutorial
2. Write Module Development Guide
3. Add API reference documentation
4. Create deployment guide
5. Update compliance checklists for new features

**Files:** `docs/**`, `README.md`, `COMPLIANCE_CHECKLIST.md`

---

## Implementation Order (Sequential Waves)

### Wave 1: Foundation Strengthening (Slots 1, 5, 6)
**Duration:** ~3-4 sessions
**Focus:** Core stability, testing infrastructure, documentation baseline

**Deliverables:**
- Experiment state machine with validation
- Job retry mechanism
- 60+ tests passing (20 new tests)
- Getting Started guide
- CI/CD pipeline active

---

### Wave 2: Module Expansion (Slots 2, 3)
**Duration:** ~4-5 sessions
**Focus:** Scientific capability expansion

**Deliverables:**
- EI-MS isotope patterns + neutral loss detection
- PChem thermodynamics + kinetics calculators
- 80+ tests passing (new module tests)
- Module development guide

---

### Wave 3: UX Polish (Slot 4, 6)
**Duration:** ~3-4 sessions
**Focus:** User experience refinement

**Deliverables:**
- Dataset preview/download
- Job queue management
- Search functionality
- API reference documentation
- Deployment guide

---

## Success Criteria (Phase 2.5.4 → Phase 3 Gateway)

### Technical Milestones
- [ ] 100+ tests passing
- [ ] CI/CD pipeline green
- [ ] All critical paths covered by integration tests
- [ ] Storage performance benchmarked
- [ ] Module registry contract tests passing

### Feature Completeness
- [ ] Experiment lifecycle management complete
- [ ] 8+ scientific modules operational
- [ ] Dataset versioning implemented
- [ ] UI search/filter functional
- [ ] Job retry mechanism validated

### Documentation
- [ ] Getting Started tutorial complete
- [ ] Module Development Guide published
- [ ] API reference generated
- [ ] Deployment guide tested
- [ ] All compliance checklists current

### Governance
- [ ] Bot slot discipline maintained (max 6 concurrent)
- [ ] All bots respect path boundaries
- [ ] VALIDATION_LOG.md kept current
- [ ] No regressions in existing functionality

---

## Risk Management

### Technical Risks
1. **Storage Performance:** Mitigate with benchmarking and indexing strategy
2. **Module Complexity:** Enforce registration standards and contract testing
3. **UI Responsiveness:** Profile Streamlit performance, add caching
4. **Test Flakiness:** Use deterministic test data, avoid timing dependencies

### Process Risks
1. **Bot Overlap:** Strict path enforcement per SWARM_STATUS.md
2. **Scope Creep:** Each wave has fixed deliverables, no feature drift
3. **Documentation Lag:** Docs bot runs concurrently with implementation
4. **Compliance Drift:** Validation bot verifies ALCOA+ alignment each wave

---

## Next Steps (Immediate Actions)

### 1. Activate Slot 1 (Core Schema / Workflow Bot)
**First Task:** Implement experiment state transition validation
```python
# labos/core/experiments.py
class ExperimentStatus(str, Enum):
    DRAFT = "draft"
    RUNNING = "running"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    FAILED = "failed"

# Add state transition rules
VALID_TRANSITIONS = {
    ExperimentStatus.DRAFT: [ExperimentStatus.RUNNING, ExperimentStatus.ARCHIVED],
    ExperimentStatus.RUNNING: [ExperimentStatus.COMPLETED, ExperimentStatus.FAILED],
    # ...
}
```

### 2. Activate Slot 5 (Testing & Validation Bot)
**First Task:** Set up GitHub Actions CI pipeline
```yaml
# .github/workflows/ci.yml
name: LabOS CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install -e .
      - run: python -m unittest discover
```

### 3. Activate Slot 6 (Docs & Compliance Bot)
**First Task:** Create Getting Started tutorial
```markdown
# docs/GETTING_STARTED.md
## Quick Start
1. Install: pip install -e .
2. Initialize: python -m labos.cli.app init
3. Run module: python -m labos.cli.app run-module pchem.calorimetry ...
4. Launch UI: streamlit run labos/ui/control_panel.py
```

---

## Phase 3 Preview (Q1 2026)

Phase 3 focuses on:
- Real analytical method validation
- Multi-user collaboration features
- Advanced provenance queries
- 3D molecule visualization
- LIMS integration hooks
- Production deployment hardening

Phase 2.5.4 prepares the foundation for these capabilities.

---

## Execution Tracking

Use this checklist to track wave completion:

### Wave 1 Progress
- [ ] Experiment state machine implemented
- [ ] Job retry mechanism added
- [ ] CI/CD pipeline configured
- [ ] Getting Started guide published
- [ ] 60 tests passing

### Wave 2 Progress
- [ ] EI-MS isotope patterns functional
- [ ] PChem thermodynamics calculators operational
- [ ] Module development guide complete
- [ ] 80 tests passing

### Wave 3 Progress
- [ ] Dataset preview/download working
- [ ] Job queue management UI ready
- [ ] Search functionality tested
- [ ] 100 tests passing
- [ ] Deployment guide validated

---

**Status:** Ready to execute Wave 1
**Next Action:** Begin Slot 1 (Core Schema) implementation
