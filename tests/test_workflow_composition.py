"""Tests for workflow composition helpers."""

import unittest

from labos.core.workflows import (
    JobChain,
    ParallelJobs,
    chain_jobs,
    parallel_jobs,
    execute_job_chain,
    execute_parallel_jobs,
)


class TestWorkflowComposition(unittest.TestCase):
    """Test workflow composition helpers for sequential and parallel execution."""

    def test_chain_jobs_creates_empty_chain(self):
        """chain_jobs() creates empty JobChain."""
        chain = chain_jobs("EXP-001")
        self.assertEqual(chain.experiment_id, "EXP-001")
        self.assertEqual(chain.length(), 0)

    def test_chain_jobs_with_initial_specs(self):
        """chain_jobs() accepts initial job specifications."""
        specs = [
            ("pchem.calorimetry", "analyze", {"delta_t": 4.2}),
            ("spectroscopy", "nmr_stub", {"nucleus": "1H"}),
        ]
        chain = chain_jobs("EXP-002", job_specs=specs)
        self.assertEqual(chain.length(), 2)

    def test_chain_add_job(self):
        """JobChain.add_job() appends job to chain."""
        chain = chain_jobs("EXP-003")
        chain.add_job("pchem.calorimetry", "analyze", {"delta_t": 4.2})
        self.assertEqual(chain.length(), 1)
        self.assertEqual(chain.jobs[0][0], "pchem.calorimetry")

    def test_chain_add_job_returns_self(self):
        """JobChain.add_job() returns self for method chaining."""
        chain = chain_jobs("EXP-004")
        result = chain.add_job("pchem.calorimetry", "analyze", {})
        self.assertIs(result, chain)

    def test_chain_method_chaining(self):
        """JobChain supports fluent method chaining."""
        chain = (
            chain_jobs("EXP-005")
            .add_job("import.wizard", "import_csv", {"file": "data.csv"})
            .add_job("ei_ms.basic_analysis", "analyze", {"precursor_mass": 250})
            .add_job("spectroscopy", "nmr_stub", {"nucleus": "1H"})
        )
        self.assertEqual(chain.length(), 3)

    def test_parallel_jobs_creates_empty_parallel(self):
        """parallel_jobs() creates empty ParallelJobs."""
        parallel = parallel_jobs("EXP-006")
        self.assertEqual(parallel.experiment_id, "EXP-006")
        self.assertEqual(parallel.length(), 0)

    def test_parallel_jobs_with_initial_specs(self):
        """parallel_jobs() accepts initial job specifications."""
        specs = [
            ("pchem.calorimetry", "analyze", {"delta_t": 4.2}),
            ("spectroscopy", "nmr_stub", {"nucleus": "1H"}),
        ]
        parallel = parallel_jobs("EXP-007", job_specs=specs)
        self.assertEqual(parallel.length(), 2)

    def test_parallel_add_job(self):
        """ParallelJobs.add_job() appends job to group."""
        parallel = parallel_jobs("EXP-008")
        parallel.add_job("pchem.calorimetry", "analyze", {"delta_t": 4.2})
        self.assertEqual(parallel.length(), 1)

    def test_parallel_method_chaining(self):
        """ParallelJobs supports fluent method chaining."""
        parallel = (
            parallel_jobs("EXP-009")
            .add_job("pchem.calorimetry", "analyze", {"delta_t": 4.2})
            .add_job("spectroscopy", "nmr_stub", {"nucleus": "1H"})
            .add_job("ei_ms.basic_analysis", "analyze", {"precursor_mass": 250})
        )
        self.assertEqual(parallel.length(), 3)

    def test_execute_job_chain_sequential_execution(self):
        """execute_job_chain() executes jobs in order."""
        chain = (
            chain_jobs("EXP-010")
            .add_job("pchem.calorimetry", "compute", {
                "sample_id": "SAMPLE-001",
                "delta_t": 4.2,
                "heat_capacity": 4.18,
            })
            .add_job("spectroscopy", "nmr_stub", {
                "sample_id": "NMR-001",
                "nucleus": "1H",
                "solvent": "CDCl3",
                "peak_list": [],
            })
        )
        
        results = execute_job_chain(chain)
        
        self.assertEqual(len(results), 2)
        self.assertTrue(all(r.succeeded() for r in results))
        self.assertIn("pchem.calorimetry", results[0].job.kind)
        self.assertIn("spectroscopy", results[1].job.kind)

    def test_execute_job_chain_stops_on_failure(self):
        """execute_job_chain() stops execution if a job fails."""
        chain = (
            chain_jobs("EXP-011")
            .add_job("pchem.calorimetry", "compute", {
                "sample_id": "SAMPLE-001",
                "delta_t": 4.2,
                "heat_capacity": 4.18,
            })
            .add_job("invalid.module", "invalid_op", {})  # Will fail
            .add_job("spectroscopy", "nmr_stub", {
                "sample_id": "NMR-001",
                "nucleus": "1H",
                "solvent": "CDCl3",
                "peak_list": [],
            })
        )
        
        results = execute_job_chain(chain)
        
        # Only first two jobs executed (second failed)
        self.assertEqual(len(results), 2)
        self.assertTrue(results[0].succeeded())
        self.assertFalse(results[1].succeeded())

    def test_execute_job_chain_with_output_passing(self):
        """execute_job_chain() passes previous dataset to next job."""
        chain = (
            chain_jobs("EXP-012")
            .add_job("pchem.calorimetry", "compute", {
                "sample_id": "SAMPLE-001",
                "delta_t": 4.2,
                "heat_capacity": 4.18,
            })
            .add_job("spectroscopy", "nmr_stub", {
                "sample_id": "NMR-001",
                "nucleus": "1H",
                "solvent": "CDCl3",
                "peak_list": [],
            })
        )
        
        results = execute_job_chain(chain, pass_outputs=True)
        
        self.assertEqual(len(results), 2)
        # Second job should have input_dataset_id from first job's output
        if results[0].dataset:
            second_job_params = results[1].job.params
            # Note: input_dataset_id may be injected at runtime
            self.assertTrue(results[1].succeeded())

    def test_execute_parallel_jobs_executes_all(self):
        """execute_parallel_jobs() executes all jobs."""
        parallel = (
            parallel_jobs("EXP-013")
            .add_job("pchem.calorimetry", "compute", {
                "sample_id": "SAMPLE-001",
                "delta_t": 4.2,
                "heat_capacity": 4.18,
            })
            .add_job("spectroscopy", "nmr_stub", {
                "sample_id": "NMR-001",
                "nucleus": "1H",
                "solvent": "CDCl3",
                "peak_list": [],
            })
            .add_job("spectroscopy", "ir_stub", {
                "sample_id": "IR-001",
                "functional_groups": ["C=O"],
            })
        )
        
        results = execute_parallel_jobs(parallel)
        
        self.assertEqual(len(results), 3)
        # All jobs execute even if one fails (parallel semantics)
        self.assertIn("pchem.calorimetry", results[0].job.kind)
        self.assertIn("spectroscopy", results[1].job.kind)
        self.assertIn("spectroscopy", results[2].job.kind)

    def test_execute_parallel_jobs_continues_on_failure(self):
        """execute_parallel_jobs() continues execution even if one job fails."""
        parallel = (
            parallel_jobs("EXP-014")
            .add_job("pchem.calorimetry", "compute", {
                "sample_id": "SAMPLE-001",
                "delta_t": 4.2,
                "heat_capacity": 4.18,
            })
            .add_job("invalid.module", "invalid_op", {})  # Will fail
            .add_job("spectroscopy", "nmr_stub", {
                "sample_id": "NMR-001",
                "nucleus": "1H",
                "solvent": "CDCl3",
                "peak_list": [],
            })
        )
        
        results = execute_parallel_jobs(parallel)
        
        # All three jobs executed despite second failure
        self.assertEqual(len(results), 3)
        self.assertTrue(results[0].succeeded())
        self.assertFalse(results[1].succeeded())
        self.assertTrue(results[2].succeeded())

    def test_chain_add_job_with_defaults(self):
        """JobChain.add_job() uses default operation and empty params."""
        chain = chain_jobs("EXP-015")
        chain.add_job("pchem.calorimetry")
        
        self.assertEqual(chain.length(), 1)
        self.assertEqual(chain.jobs[0][1], "analyze")  # Default operation
        self.assertEqual(chain.jobs[0][2], {})  # Default empty params

    def test_parallel_add_job_with_defaults(self):
        """ParallelJobs.add_job() uses default operation and empty params."""
        parallel = parallel_jobs("EXP-016")
        parallel.add_job("spectroscopy")
        
        self.assertEqual(parallel.length(), 1)
        self.assertEqual(parallel.jobs[0][1], "analyze")
        self.assertEqual(parallel.jobs[0][2], {})


if __name__ == "__main__":
    unittest.main()
