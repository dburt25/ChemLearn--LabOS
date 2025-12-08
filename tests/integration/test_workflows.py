"""Comprehensive integration tests for run_module_job across all registered modules.

Verifies that every active module can be invoked through the workflow system
and produces valid experiment, job, dataset, and audit artifacts.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from labos.core.jobs import JobStatus
from labos.core.workflows import WorkflowResult, run_module_job
from labos.modules import get_registry


class WorkflowIntegrationTests(unittest.TestCase):
    """Verify run_module_job works end-to-end for all registered modules."""

    def setUp(self):
        """Get fresh module registry for each test."""
        self.registry = get_registry()

    def _verify_workflow_artifacts(self, result: WorkflowResult, module_key: str, operation: str) -> None:
        """Common assertions for workflow results."""
        # Verify success
        if not result.succeeded():
            # Print error for debugging
            print(f"\n{module_key}.{operation} failed: {result.error}")
        self.assertTrue(result.succeeded(), f"{module_key}.{operation} workflow should succeed")
        self.assertEqual(result.job.status, JobStatus.COMPLETED)

        # Verify experiment linkage
        self.assertIsNotNone(result.experiment)
        self.assertIn(result.job.id, result.experiment.jobs)
        self.assertEqual(result.job.experiment_id, result.experiment.id)

        # Verify dataset creation
        self.assertIsNotNone(result.dataset, f"{module_key} should create a dataset")
        self.assertIn(result.dataset.id, result.job.datasets_out)
        self.assertTrue(result.dataset.label, "Dataset should have a label")

        # Verify audit trail
        self.assertGreaterEqual(len(result.audit_events), 1)
        # Check if any event references the module
        has_module_ref = any(
            event.details.get("module_key") == module_key for event in result.audit_events
        )
        self.assertTrue(has_module_ref, f"Audit events should reference {module_key}")

    def test_spectroscopy_nmr_stub_workflow(self):
        """Verify spectroscopy.nmr_stub creates valid artifacts."""
        params = {
            "sample_id": "NMR-INTEGRATION-001",
            "chemical_formula": "C8H10N4O2",
            "nucleus": "1H",
            "solvent": "CDCl3",
            "peak_list": [
                {"shift_ppm": 7.12, "intensity": 0.8, "multiplicity": "d", "notes": "aromatic"}
            ],
        }

        result = run_module_job(
            module_key="spectroscopy",
            operation="nmr_stub",
            params=params,
            actor="integration-tester",
            experiment_name="Spectroscopy NMR Integration Test",
        )

        self._verify_workflow_artifacts(result, "spectroscopy", "nmr_stub")

    def test_spectroscopy_ir_stub_workflow(self):
        """Verify spectroscopy.ir_stub creates valid artifacts."""
        params = {
            "sample_id": "IR-INTEGRATION-001",
            "chemical_formula": "C8H10N4O2",
            "peak_list": [
                {"wavenumber_cm_1": 1710, "intensity": 0.9, "assignment": "C=O stretch"}
            ],
        }

        result = run_module_job(
            module_key="spectroscopy",
            operation="ir_stub",
            params=params,
            actor="integration-tester",
            experiment_name="Spectroscopy IR Integration Test",
        )

        self._verify_workflow_artifacts(result, "spectroscopy", "ir_stub")

    def test_pchem_calorimetry_workflow(self):
        """Verify pchem.calorimetry creates valid artifacts."""
        params = {
            "sample_id": "CAL-INTEGRATION-001",
            "delta_t": 4.2,
            "heat_capacity": 4.18,
        }

        result = run_module_job(
            module_key="pchem.calorimetry",
            operation="compute",
            params=params,
            actor="integration-tester",
            experiment_name="Calorimetry Integration Test",
        )

        self._verify_workflow_artifacts(result, "pchem.calorimetry", "compute")

        # Verify calorimetry-specific outputs
        # Note: calorimetry stub returns dataset/audit metadata structure, not direct heat_transfer
        self.assertIsNotNone(result.module_output)
        assert result.module_output is not None
        self.assertIn("dataset", result.module_output)

    def test_ei_ms_basic_analysis_workflow(self):
        """Verify ei_ms.basic_analysis creates valid artifacts."""
        params = {
            "precursor_mass": 250.0,
            "fragment_masses": [235.0, 222.0, 207.0],
            "fragment_intensities": [100.0, 65.0, 40.0],
        }

        result = run_module_job(
            module_key="ei_ms.basic_analysis",
            operation="analyze",
            params=params,
            actor="integration-tester",
            experiment_name="EI-MS Integration Test",
        )

        self._verify_workflow_artifacts(result, "ei_ms.basic_analysis", "analyze")

        # Verify EI-MS-specific outputs
        self.assertIsNotNone(result.module_output)
        assert result.module_output is not None  # Type narrowing for checker
        self.assertIn("fragments", result.module_output)

    def test_import_wizard_workflow(self):
        """Verify import.wizard creates valid artifacts."""
        params = {
            "data": [
                {"sample": "STD-1", "analyte": "Caffeine", "value": 1.23, "units": "mg/L"},
                {"sample": "STD-2", "analyte": "Caffeine", "value": 4.56, "units": "mg/L"},
            ],
            "source_type": "inline",
            "notes": {"test": "integration"},
        }

        result = run_module_job(
            module_key="import.wizard",
            operation="compute",
            params=params,
            actor="integration-tester",
            experiment_name="Import Wizard Integration Test",
        )

        self._verify_workflow_artifacts(result, "import.wizard", "compute")

    def test_all_modules_discoverable(self):
        """Verify all expected modules are registered and have operations."""
        expected_modules = {
            "spectroscopy": ["nmr_stub", "ir_stub", "analyze_nmr_spectrum", "analyze_ir_spectrum"],
            "pchem.calorimetry": ["compute"],
            "ei_ms.basic_analysis": ["analyze", "compute"],
            "import.wizard": ["compute"],
        }

        for module_id, expected_ops in expected_modules.items():
            descriptor = self.registry.ensure_module_loaded(module_id)
            self.assertIsNotNone(descriptor, f"Module {module_id} should be registered")

            for op_name in expected_ops:
                self.assertIn(
                    op_name,
                    descriptor.operations,
                    f"Operation {op_name} should exist in {module_id}",
                )

    def test_module_operations_callable(self):
        """Verify all registered operations can be retrieved and are callable."""
        module_ids = self.registry.list_module_ids()

        # Filter out legacy modules
        active_modules = [m for m in module_ids if m != "eims.fragmentation"]

        for module_id in active_modules:
            descriptor = self.registry.ensure_module_loaded(module_id)

            for op_name, operation in descriptor.operations.items():
                self.assertTrue(
                    callable(operation.handler),
                    f"{module_id}.{op_name} handler should be callable",
                )

                # Verify operation has required fields
                self.assertTrue(operation.name)
                self.assertTrue(operation.description)


if __name__ == "__main__":
    unittest.main()
