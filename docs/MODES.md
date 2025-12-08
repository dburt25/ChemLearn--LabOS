# LabOS UI Modes: Learner, Lab, and Builder

## Overview

The LabOS Control Panel adapts its interface based on three distinct operational modes: **Learner**, **Lab**, and **Builder**. Each mode is designed for different audiences and use cases, balancing educational depth, operational efficiency, and technical debugging needs.

## Mode Selection

Users can switch modes via the sidebar radio button selector. The active mode persists in session state and affects:
- Information density and explanatory text
- Visibility of debug/technical payloads
- UI component verbosity (tooltips, captions, expandable sections)
- Default view preferences for data tables

## Learner Mode 🎓

**Target Audience:** Students, trainees, and novice users learning analytical chemistry concepts, experimental design, and data provenance.

**Philosophy:** Maximize educational value by explaining *why* each component exists, *how* it connects to scientific practice, and *what* the governance implications are.

### UI Characteristics

| Element | Behavior |
|---------|----------|
| **Explanatory Text** | Extensive. Every section includes context about ALCOA+ compliance, scientific method, or data integrity principles. |
| **Mode Banner** | Green badge with 📚 icon, caption: "Learner mode emphasizes educational context and provenance explanations." |
| **Section Headers** | Include "Why this matters" callouts explaining real-world relevance. |
| **Data Tables** | Annotated with column purpose (e.g., "experiment_id links this job to its parent study") |
| **Debug Toggles** | Hidden by default; JSON payloads deemphasized to avoid cognitive overload. |
| **Method & Data Footer** | Always visible with full citations, limitations, and dataset provenance. |
| **Tooltips** | Verbose, educational tone (e.g., "Sample ID ensures traceability per 21 CFR Part 11"). |
| **Error Messages** | Contextualized with learning objectives (e.g., "This validation prevents ALCOA compliance violations"). |

### Use Cases
- Classroom demonstrations of GLP/GMP workflows
- Self-paced learning modules about analytical method validation
- Onboarding new lab technicians to compliance requirements
- Educational workshops on data integrity and audit trails

### Example Interactions
- **Viewing Experiments:** Includes explanation of experiment lifecycle (draft → running → completed → archived) with analogies to paper lab notebooks.
- **Running Workflows:** Step-by-step guidance on parameter selection with warnings about data quality impacts.
- **Audit Log Review:** Each entry includes "What this means" annotations about regulatory significance.

---

## Lab Mode 🔬

**Target Audience:** Lab operators, QA/QC personnel, and routine users executing validated workflows in production environments.

**Philosophy:** Optimize for speed and clarity. Minimize distractions while maintaining traceability and compliance visibility.

### UI Characteristics

| Element | Behavior |
|---------|----------|
| **Explanatory Text** | Concise. Assumes domain knowledge; focuses on actionable information. |
| **Mode Banner** | Blue badge with 🔬 icon, caption: "Lab mode streamlines routine operations with essential compliance context." |
| **Section Headers** | Minimal; assumes user knows section purpose. |
| **Data Tables** | Compact, dense rows. Hides less-critical columns by default. |
| **Debug Toggles** | Hidden entirely; technical JSON payloads suppressed. |
| **Method & Data Footer** | Collapsed by default with expand option; assumes familiarity with SOPs. |
| **Tooltips** | Brief, operational tone (e.g., "Required for audit trail"). |
| **Error Messages** | Actionable, no educational context (e.g., "Invalid sample_id format: use SAMPLE-XXX"). |

### Use Cases
- Daily routine sample analysis
- High-throughput quality control checks
- Production workflows with validated methods
- Operators following established SOPs

### Example Interactions
- **Viewing Experiments:** Quick-scan table with status, last update, owner. No explanatory text.
- **Running Workflows:** Pre-filled forms from templates, one-click execution, minimal validation explanations.
- **Audit Log Review:** Timestamped entries with event type; details hidden in expandable rows.

---

## Builder Mode 🛠️

**Target Audience:** Developers, method validation scientists, system administrators, and technical troubleshooters.

**Philosophy:** Expose everything. Prioritize debugging, schema inspection, and system behavior verification over user-friendliness.

### UI Characteristics

| Element | Behavior |
|---------|----------|
| **Explanatory Text** | Technical. Focuses on implementation details, schema structures, and API contracts. |
| **Mode Banner** | Orange badge with 🛠️ icon, caption: "Builder mode exposes raw payloads and debugging tools for development." |
| **Section Headers** | Include schema hints and data model references. |
| **Data Tables** | Wide format with all columns visible. Includes internal IDs, timestamps with milliseconds, status codes. |
| **Debug Toggles** | Always visible with "Show JSON" / "Show registry payload" options expanded by default. |
| **Method & Data Footer** | Always expanded with raw metadata registry entries. |
| **Tooltips** | Technical, references code (e.g., "See `labos.core.workflows.run_module_job` for implementation"). |
| **Error Messages** | Full Python tracebacks in expandable sections. |

### Use Cases
- Developing new module descriptors
- Debugging workflow orchestration issues
- Validating registry metadata against requirements
- Inspecting dataset provenance linkage
- Testing new analytical methods pre-validation

### Example Interactions
- **Viewing Experiments:** JSON toggle showing full `experiment.to_dict()` payload alongside table view.
- **Running Workflows:** Raw parameter editor with JSON schema validation feedback.
- **Audit Log Review:** Full event dictionaries with system-level details (process ID, hostname if available).

---

## Mode Comparison Matrix

| Feature | Learner 🎓 | Lab 🔬 | Builder 🛠️ |
|---------|-----------|--------|-----------|
| **Primary Goal** | Education | Efficiency | Debugging |
| **Explanatory Text Volume** | High | Low | Medium (technical) |
| **JSON Payload Visibility** | Optional (collapsed) | Hidden | Visible (expanded) |
| **Table Density** | Sparse (wide rows) | Dense (compact) | Dense (all columns) |
| **Error Detail Level** | Contextualized | Actionable | Full traceback |
| **Method & Data Footer** | Always expanded | Collapsed | Always expanded |
| **Tooltip Verbosity** | Educational | Brief | Technical |
| **Audit Log Detail** | Annotated | Timestamped | Full payload |
| **Target Time-to-Action** | Minutes (learning) | Seconds (executing) | Variable (investigating) |

---

## Implementation Patterns

### Mode Detection Helpers

```python
def is_learner(mode: str = None) -> bool:
    mode = mode or st.session_state.get("mode", "learner")
    return mode.lower() == "learner"

def is_lab(mode: str = None) -> bool:
    mode = mode or st.session_state.get("mode", "lab")
    return mode.lower() == "lab"

def is_builder(mode: str = None) -> bool:
    mode = mode or st.session_state.get("mode", "builder")
    return mode.lower() == "builder"
```

### Conditional UI Rendering

```python
if is_learner(mode):
    st.info("📚 **Why Experiments Matter:** Experiments group related analyses "
            "and preserve context for reproducibility per ALCOA+ guidelines.")
elif is_lab(mode):
    show_lab_mode_note("Quick experiment selector below; detailed logs in Audit section.")
else:  # Builder
    st.caption("Builder mode: Raw experiment registry with full metadata payloads.")
    render_debug_toggle("Show experiment JSON", key="exp_debug", payload=exp.to_dict())
```

### Mode-Aware Captions

Use `_mode_tip()` helper to return mode-specific guidance:

```python
def _mode_tip(section: str) -> str:
    mode = st.session_state.get("mode", "learner")
    tips = {
        "experiments": {
            "learner": "Experiments link datasets to research context. Each has a lifecycle: draft → running → completed.",
            "lab": "Experiments group related jobs for audit trail integrity.",
            "builder": "Registry backing: data/experiments/*.json; see Experiment.to_dict() schema."
        },
        # ... more sections
    }
    return tips.get(section, {}).get(mode, "")
```

---

## Best Practices

### For Learner Mode Development
1. **Every table column** should have a tooltip explaining its purpose
2. **Every workflow step** should link to underlying scientific concept
3. **Citations** must be visible and accessible without deep navigation
4. **Limitations** must be prominently displayed (e.g., "Educational use only, not validated for clinical applications")

### For Lab Mode Development
1. **Minimize clicks** to common actions (pre-fill forms from templates)
2. **Hide complexity** unless user explicitly requests details
3. **Status indicators** should use clear visual cues (✅ ⚠️ ❌)
4. **Audit trails** must remain accessible but not intrusive

### For Builder Mode Development
1. **Expose schema contracts** via JSON toggles and type hints
2. **Include object IDs** in all tables for cross-referencing
3. **Show raw errors** with full stack traces for debugging
4. **Registry metadata** should be inspectable at all decision points

---

## Mode Switching Guidelines

### When to Recommend Learner Mode
- User asks "What does this mean?"
- Training sessions or demos
- Compliance audits where explanation is needed
- Documentation generation

### When to Recommend Lab Mode
- Production workflows
- High-throughput operations
- Users complain about "too much text"
- Speed-critical environments

### When to Recommend Builder Mode
- Developing new modules
- Debugging workflow failures
- Validating data model changes
- System integration testing

---

## Governance Alignment

All modes maintain ALCOA+ compliance by:
- Preserving complete audit trails (visibility varies by mode)
- Enforcing read-only constraints on archived experiments
- Maintaining dataset provenance linkage
- Recording actor identity in all mutations

The mode selection affects **presentation**, not **data integrity**. Regulatory requirements are met regardless of active mode.

---

## Future Enhancements

### Planned for Phase 3
- **Custom mode profiles:** Organizations can define mode presets (e.g., "GMP Production", "R&D Exploratory")
- **Role-based defaults:** User profiles map to default modes based on job function
- **Mode hints:** Contextual suggestions when user behavior mismatches active mode
- **Accessibility profiles:** Screen reader optimization per mode

### Under Consideration
- **Hybrid modes:** "Lab+" with selective Builder debug toggles
- **Quick-switch shortcuts:** Keyboard shortcuts (L/B/O) for mode switching
- **Mode analytics:** Track which modes are most used for UX optimization

---

## See Also
- `labos/ui/control_panel.py` - Mode detection and conditional rendering
- `labos/ui/components.py` - Reusable mode-aware UI primitives
- `COMPLIANCE_CHECKLIST.md` - Regulatory alignment across modes
- `VISION.md` - Educational philosophy driving Learner mode design
