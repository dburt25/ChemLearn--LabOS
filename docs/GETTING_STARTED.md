# Getting Started with ChemLearn LabOS

## What is LabOS?

LabOS (Laboratory Operating System) is an educational platform for learning analytical chemistry workflows with built-in data integrity, audit trails, and compliance practices. It's designed for students, lab technicians, and researchers who want to understand how data flows from experiments to results while maintaining ALCOA+ (Attributable, Legible, Contemporaneous, Original, Accurate + Complete, Consistent, Enduring, Available) principles.

**Key Features:**
- 📊 **Experiment Tracking:** Organize analyses with full lineage from raw data to conclusions
- 🔬 **Scientific Modules:** Pre-built modules for EI-MS, calorimetry, spectroscopy, and more
- 📝 **Audit Trails:** Every action recorded with who, what, when, why
- 🎓 **Educational Modes:** Learner, Lab, and Builder modes adapt UI to skill level
- 🛠️ **Extensible:** Create custom analytical modules following simple contracts

---

## Installation

### Prerequisites
- Python 3.10 or higher
- pip package manager
- (Optional) Streamlit for UI access

### Quick Install

```bash
# Clone the repository
git clone https://github.com/ChemLearn/LabOS.git
cd LabOS

# Create virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install LabOS
pip install -e .

# Verify installation
python -c "import labos; print(labos.__version__)"
```

---

## First Steps

### 1. Initialize LabOS

Create the required directory structure:

```bash
python -m labos.cli.app init
```

This creates:
```
data/
├── audit/          # Audit event logs
├── experiments/    # Experiment records
├── jobs/           # Job execution records
├── datasets/       # Dataset metadata
└── feedback/       # User feedback and examples
```

### 2. List Available Modules

See what analytical capabilities are built-in:

```bash
python -m labos.cli.app list-modules
```

Expected output:
```
key                      method
-------------------------  ----------------------------------------
ei_ms.basic_analysis     EI-MS fragmentation pattern recognition
import.wizard            Data import wizard with schema inference
pchem.calorimetry        Constant-pressure calorimetry
spectroscopy             Spectroscopy analysis (NMR, IR)
```

### 3. Run Your First Analysis

Execute a calorimetry calculation:

```bash
python -m labos.cli.app run-module pchem.calorimetry \
  --params-json '{"sample_id":"SAMPLE-001","delta_t":4.2,"heat_capacity":4.18}' \
  --experiment-name "My First Calorimetry Run"
```

This will:
1. Create a new experiment
2. Submit a job to the module
3. Generate a dataset with results
4. Record audit events for traceability

### 4. View Results

Check your experiments:

```bash
python -m labos.cli.app list-experiments
```

View datasets created:

```bash
python -m labos.cli.app list-datasets
```

---

## Using the UI (Streamlit Control Panel)

### Launch the Control Panel

```bash
streamlit run labos/ui/control_panel.py
```

Your browser will open to `http://localhost:8501` with the LabOS Control Panel.

### UI Tour

**Sidebar:**
- **Mode Selector:** Switch between Learner (🎓), Lab (🔬), and Builder (🛠️) modes
- **Navigation:** Jump to Experiments, Jobs, Datasets, Modules, Audit Log, Workspace

**Main Sections:**

1. **Overview:** Dashboard showing experiments, jobs, datasets, and module counts
2. **Experiments:** Browse experiment records with status and metadata
3. **Jobs:** View job execution history and results
4. **Datasets:** Explore generated datasets with provenance information
5. **Modules:** Inspect registered analytical methods and run workflows
6. **Audit Log:** Review complete audit trail with actor and timestamp details
7. **Workspace:** Collaborative area for notes, file uploads, and visualizations

### Running an Analysis in the UI

1. Navigate to **Modules & Operations**
2. Select a module (e.g., "pchem.calorimetry")
3. Scroll to the runner form
4. Fill in parameters:
   - Experiment Name: `UI Test Calorimetry`
   - Sample ID: `UI-SAMPLE-001`
   - Delta T (°C): `4.2`
   - Heat Capacity: `4.18`
5. Click **Run Calorimetry Workflow**
6. View results displayed with dataset and audit linkage

---

## Understanding LabOS Concepts

### Experiments
Containers that group related analyses. Each experiment has:
- Unique ID (e.g., `exp-20251207-103045`)
- Name, owner, creation timestamp
- Status (draft, running, completed, archived)
- List of associated jobs

**Analogy:** Like a lab notebook page documenting a study.

### Jobs
Individual analysis executions. Each job:
- Belongs to one experiment
- Invokes one module operation
- Has input parameters and output datasets
- Records success/failure status

**Analogy:** Like running a specific instrument with specific settings.

### Datasets
Results from job executions. Each dataset:
- Has metadata (sample ID, method, instrument)
- Links back to creating job and parent experiment
- Includes provenance (who, when, how generated)
- May reference raw data files

**Analogy:** Like a chromatogram, spectrum, or table of measurements.

### Audit Events
Immutable records of actions taken. Each event:
- Identifies actor (user ID)
- Describes action (e.g., "create_experiment", "run_module")
- Timestamps occurrence
- Links to affected resources

**Analogy:** Like entries in a regulatory audit log.

---

## Example Workflows

### Workflow 1: EI-MS Fragmentation Analysis

```bash
# Run EI-MS analysis
python -m labos.cli.app run-module ei_ms.basic_analysis \
  --operation analyze \
  --params-json '{
    "precursor_mass": 250.0,
    "fragment_masses": [235.0, 222.0, 207.0],
    "fragment_intensities": [100.0, 65.0, 40.0]
  }' \
  --experiment-name "EI-MS Caffeine Analysis"

# View the generated dataset
python -m labos.cli.app list-datasets
```

### Workflow 2: NMR Spectrum Stub

```bash
python -m labos.cli.app run-module spectroscopy \
  --operation nmr_stub \
  --params-json '{
    "sample_id": "NMR-CAFFEINE-001",
    "nucleus": "1H",
    "solvent": "CDCl3",
    "peak_list": [
      {"shift_ppm": 7.12, "intensity": 0.8, "multiplicity": "d"}
    ]
  }' \
  --experiment-name "1H-NMR Caffeine"
```

### Workflow 3: Batch Processing

```bash
# Create parameter file
cat > batch_params.json << EOF
{
  "samples": [
    {"sample_id": "BATCH-001", "delta_t": 3.5, "heat_capacity": 4.18},
    {"sample_id": "BATCH-002", "delta_t": 4.2, "heat_capacity": 4.18},
    {"sample_id": "BATCH-003", "delta_t": 5.1, "heat_capacity": 4.18}
  ]
}
EOF

# Process each sample
for sample in $(jq -c '.samples[]' batch_params.json); do
  python -m labos.cli.app run-module pchem.calorimetry \
    --params-json "$sample" \
    --experiment-name "Batch Processing $(date +%Y%m%d)"
done
```

---

## Educational Features

### Learner Mode 🎓

Perfect for students and newcomers. Provides:
- Extensive explanations of each concept
- Connections to regulatory compliance (ALCOA+, 21 CFR Part 11)
- Citations and references for scientific methods
- Warnings about limitations and educational boundaries

**Use Cases:**
- Classroom demonstrations
- Self-paced learning
- Onboarding new lab staff

### Lab Mode 🔬

Optimized for production workflows:
- Minimal explanatory text
- Compact, dense data tables
- Quick-access forms with templates
- Essential compliance information only

**Use Cases:**
- Daily routine sample analysis
- High-throughput QC operations
- Following established SOPs

### Builder Mode 🛠️

For developers and method validation:
- Full JSON payload inspection
- Debug toggles and raw data views
- Schema validation feedback
- Error tracebacks and system details

**Use Cases:**
- Developing new analytical methods
- Debugging workflow issues
- System integration testing

---

## Troubleshooting

### Import Errors

**Problem:** `ModuleNotFoundError: No module named 'labos'`

**Solution:**
```bash
# Ensure you're in the LabOS directory
cd LabOS

# Install in editable mode
pip install -e .
```

### CLI Not Working

**Problem:** `python -m labos.cli.app: No module named labos.cli.app`

**Solution:**
```bash
# Use the correct entry point
python -m labos.cli.app --help

# Or use the package directly
python -c "from labos.cli.app import main; main()" --help
```

### Streamlit UI Not Loading

**Problem:** Blank page or errors in browser

**Solution:**
```bash
# Install Streamlit if missing
pip install streamlit>=1.39.0

# Verify installation
streamlit --version

# Launch with verbose output
streamlit run labos/ui/control_panel.py --logger.level=debug
```

### Tests Failing

**Problem:** Unit tests fail on import

**Solution:**
```bash
# Activate virtual environment
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Re-install dependencies
pip install -e .

# Run tests
python -m unittest discover -s tests -p 'test_*.py'
```

---

## Next Steps

### Learn More
- 📖 Read [MODES.md](MODES.md) for detailed mode behaviors
- 🔧 See [MODULE_REGISTRATION_STANDARDS.md](MODULE_REGISTRATION_STANDARDS.md) to create custom modules
- 📊 Review [CLI_API_PARITY.md](CLI_API_PARITY.md) for advanced CLI usage
- ✅ Check [COMPLIANCE_CHECKLIST.md](COMPLIANCE_CHECKLIST.md) for regulatory alignment

### Try Advanced Features
- Create experiment templates
- Build custom analytical modules
- Set up automated workflows
- Explore dataset provenance graphs

### Get Involved
- Report issues on GitHub
- Contribute new modules
- Improve documentation
- Share educational use cases

---

## Support

- **Documentation:** `docs/` directory contains detailed guides
- **Issues:** GitHub Issues for bug reports and feature requests
- **Questions:** Check FAQ or open a discussion

---

**Welcome to LabOS! Start exploring analytical chemistry with confidence in your data integrity.**
