"""
Tests for Testing Infrastructure

Comprehensive tests for test utilities.
"""

import pytest
from labos.testing.fixtures import (
    ExperimentFactory, DatasetFactory, JobFactory,
    generate_test_spectrum, generate_test_dataset, create_test_molecule
)
from labos.testing.performance import (
    PerformanceBenchmark, measure_execution_time, measure_memory_usage,
    profile_function, benchmark_comparison
)
from labos.testing.data_generators import (
    DataGenerator, generate_molecular_formula, generate_spectrum_data,
    generate_kinetics_data, generate_proteomics_data, generate_timeseries_data
)
from labos.testing.assertions import (
    ValidationAssertion, assert_valid_experiment, assert_valid_dataset,
    assert_valid_job, assert_schema_compliant, assert_workflow_valid,
    assert_spectrum_valid
)


class TestExperimentFactory:
    """Test experiment factory"""
    
    def test_create_default_experiment(self):
        """Test creating experiment with defaults"""
        exp = ExperimentFactory.create()
        assert "id" in exp
        assert exp["title"] == "Test Experiment"
        assert exp["status"] == "draft"
        assert "created_at" in exp
    
    def test_create_custom_experiment(self):
        """Test creating experiment with custom values"""
        exp = ExperimentFactory.create(
            exp_id="custom-123",
            title="Custom Experiment",
            status="running"
        )
        assert exp["id"] == "custom-123"
        assert exp["title"] == "Custom Experiment"
        assert exp["status"] == "running"
    
    def test_create_batch(self):
        """Test creating multiple experiments"""
        experiments = ExperimentFactory.create_batch(5)
        assert len(experiments) == 5
        assert all("id" in exp for exp in experiments)
        # IDs should be unique
        ids = [exp["id"] for exp in experiments]
        assert len(set(ids)) == 5


class TestDatasetFactory:
    """Test dataset factory"""
    
    def test_create_default_dataset(self):
        """Test creating dataset with defaults"""
        ds = DatasetFactory.create()
        assert "id" in ds
        assert ds["label"] == "Test Dataset"
        assert ds["kind"] == "experimental"
        assert "data" in ds
    
    def test_create_with_data(self):
        """Test creating dataset with custom data"""
        data = {"measurements": [1, 2, 3]}
        ds = DatasetFactory.create(data=data)
        assert ds["data"] == data
    
    def test_create_with_spectrum(self):
        """Test creating dataset with spectrum"""
        ds = DatasetFactory.create_with_spectrum(n_peaks=5)
        assert ds["kind"] == "spectrum"
        assert "spectrum" in ds["data"]
        assert len(ds["data"]["spectrum"]) == 5


class TestJobFactory:
    """Test job factory"""
    
    def test_create_default_job(self):
        """Test creating job with defaults"""
        job = JobFactory.create()
        assert "id" in job
        assert job["module_key"] == "test.module"
        assert job["status"] == "queued"
    
    def test_create_with_experiment(self):
        """Test creating job linked to experiment"""
        exp_id = "exp-123"
        job = JobFactory.create(experiment_id=exp_id)
        assert job["experiment_id"] == exp_id
    
    def test_create_workflow(self):
        """Test creating workflow of jobs"""
        workflow = JobFactory.create_workflow(n_jobs=3)
        assert len(workflow) == 3
        # All jobs should share experiment ID
        exp_ids = [j["experiment_id"] for j in workflow]
        assert len(set(exp_ids)) == 1


class TestSpectrumGeneration:
    """Test spectrum generation"""
    
    def test_generate_spectrum(self):
        """Test generating test spectrum"""
        spectrum = generate_test_spectrum(n_peaks=10)
        assert len(spectrum) == 10
        assert all("mz" in peak for peak in spectrum)
        assert all("intensity" in peak for peak in spectrum)
    
    def test_spectrum_sorted(self):
        """Test spectrum is sorted by m/z"""
        spectrum = generate_test_spectrum(n_peaks=20)
        mz_values = [peak["mz"] for peak in spectrum]
        assert mz_values == sorted(mz_values)
    
    def test_spectrum_reproducible(self):
        """Test spectrum generation is reproducible with seed"""
        spec1 = generate_test_spectrum(n_peaks=10, seed=42)
        spec2 = generate_test_spectrum(n_peaks=10, seed=42)
        assert spec1 == spec2


class TestPerformanceBenchmark:
    """Test performance benchmarking"""
    
    def test_benchmark_simple_function(self):
        """Test benchmarking a function"""
        def simple_func():
            return sum(range(1000))
        
        bench = PerformanceBenchmark("test")
        result = bench.run(simple_func, iterations=10, warmup=2)
        
        assert result.name == "test"
        assert result.iterations == 10
        assert result.execution_time > 0
        assert result.avg_time_per_iteration > 0
    
    def test_benchmark_comparison(self):
        """Test comparing benchmarks"""
        def func1():
            return sum(range(100))
        
        def func2():
            return sum(range(1000))
        
        bench1 = PerformanceBenchmark("fast")
        result1 = bench1.run(func1, iterations=10)
        
        bench2 = PerformanceBenchmark("slow")
        result2 = bench2.run(func2, iterations=10)
        
        comparison = bench1.compare(result1, result2)
        assert "time_ratio" in comparison
        assert result2.avg_time_per_iteration > result1.avg_time_per_iteration
    
    def test_measure_execution_time(self):
        """Test execution time context manager"""
        with measure_execution_time("test") as timer:
            sum(range(1000))
        
        assert timer["elapsed"] > 0
        assert timer["name"] == "test"
    
    def test_measure_memory_usage(self):
        """Test memory usage context manager"""
        with measure_memory_usage("test") as mem:
            data = [i for i in range(10000)]
        
        assert mem["peak_mb"] > 0


class TestProfileFunction:
    """Test function profiling"""
    
    def test_profile_simple_function(self):
        """Test profiling a function"""
        def func():
            return sum(range(100))
        
        profile = profile_function(func, iterations=20)
        
        assert profile["function"] == "func"
        assert profile["iterations"] == 20
        assert profile["avg_time"] > 0
        assert profile["min_time"] > 0
        assert profile["max_time"] > 0
    
    def test_benchmark_comparison_multiple(self):
        """Test comparing multiple functions"""
        def fast():
            return sum(range(10))
        
        def medium():
            return sum(range(100))
        
        def slow():
            return sum(range(1000))
        
        functions = [
            ("fast", fast, (), {}),
            ("medium", medium, (), {}),
            ("slow", slow, (), {})
        ]
        
        results = benchmark_comparison(functions, iterations=10)
        
        assert len(results) == 3
        # Should be sorted by speed
        assert results[0]["name"] == "fast"
        assert results[2]["name"] == "slow"


class TestDataGenerator:
    """Test data generator"""
    
    def test_random_string(self):
        """Test random string generation"""
        s = DataGenerator.random_string(length=10)
        assert len(s) == 10
        assert s.isalpha()
    
    def test_random_timestamp(self):
        """Test random timestamp generation"""
        ts = DataGenerator.random_timestamp()
        assert ts.endswith("Z")
        assert "T" in ts


class TestMolecularFormulaGeneration:
    """Test molecular formula generation"""
    
    def test_generate_formula(self):
        """Test generating molecular formula"""
        formula = generate_molecular_formula()
        assert "C" in formula
        assert any(char.isdigit() for char in formula)
    
    def test_formula_reproducible(self):
        """Test formula generation is reproducible"""
        formula1 = generate_molecular_formula(seed=42)
        formula2 = generate_molecular_formula(seed=42)
        assert formula1 == formula2


class TestSpectrumDataGeneration:
    """Test spectrum data generation"""
    
    def test_generate_spectrum_data(self):
        """Test generating spectrum data"""
        spec = generate_spectrum_data(n_peaks=10)
        assert "peaks" in spec
        assert "molecular_ion" in spec
        assert len(spec["peaks"]) >= 10
    
    def test_spectrum_with_isotopes(self):
        """Test spectrum includes isotope peaks"""
        spec = generate_spectrum_data(include_isotopes=True)
        labels = [p.get("label", "") for p in spec["peaks"]]
        assert "M+" in labels
        assert "M+1" in labels


class TestKineticsDataGeneration:
    """Test kinetics data generation"""
    
    def test_generate_first_order(self):
        """Test first order kinetics data"""
        data = generate_kinetics_data(reaction_order=1)
        assert "times" in data
        assert "concentrations" in data
        assert data["reaction_order"] == 1
        # Concentration should decrease
        assert data["concentrations"][0] > data["concentrations"][-1]
    
    def test_generate_zero_order(self):
        """Test zero order kinetics data"""
        data = generate_kinetics_data(reaction_order=0)
        assert data["reaction_order"] == 0


class TestProteomicsDataGeneration:
    """Test proteomics data generation"""
    
    def test_generate_proteomics(self):
        """Test generating proteomics data"""
        data = generate_proteomics_data(n_peptides=5)
        assert "peptides" in data
        assert len(data["peptides"]) == 5
        
        # Check peptide structure
        peptide = data["peptides"][0]
        assert "sequence" in peptide
        assert "mass" in peptide
        assert "charge" in peptide
    
    def test_peptide_sequences_valid(self):
        """Test peptide sequences use valid amino acids"""
        data = generate_proteomics_data(n_peptides=10)
        amino_acids = "ACDEFGHIKLMNPQRSTVWY"
        
        for peptide in data["peptides"]:
            seq = peptide["sequence"]
            assert all(aa in amino_acids for aa in seq)


class TestTimeseriesGeneration:
    """Test timeseries generation"""
    
    def test_generate_linear_trend(self):
        """Test linear trend timeseries"""
        data = generate_timeseries_data(n_points=50, trend="linear")
        assert len(data["times"]) == 50
        assert len(data["values"]) == 50
        assert data["trend"] == "linear"
    
    def test_generate_periodic_trend(self):
        """Test periodic trend timeseries"""
        data = generate_timeseries_data(n_points=100, trend="periodic")
        assert data["trend"] == "periodic"


class TestValidationAssertion:
    """Test validation assertions"""
    
    def test_assert_dict_contains_valid(self):
        """Test dict contains assertion passes"""
        data = {"a": 1, "b": 2, "c": 3}
        ValidationAssertion.assert_dict_contains(data, ["a", "b"])
        # Should not raise
    
    def test_assert_dict_contains_invalid(self):
        """Test dict contains assertion fails"""
        data = {"a": 1, "b": 2}
        with pytest.raises(AssertionError, match="Missing required keys"):
            ValidationAssertion.assert_dict_contains(data, ["a", "b", "c"])
    
    def test_assert_valid_timestamp(self):
        """Test timestamp validation"""
        ValidationAssertion.assert_valid_timestamp("2025-01-01T00:00:00Z")
        
        with pytest.raises(AssertionError, match="Invalid timestamp"):
            ValidationAssertion.assert_valid_timestamp("not-a-timestamp")
    
    def test_assert_numeric_range(self):
        """Test numeric range validation"""
        ValidationAssertion.assert_numeric_range(5.0, 0.0, 10.0)
        
        with pytest.raises(AssertionError, match="not in range"):
            ValidationAssertion.assert_numeric_range(15.0, 0.0, 10.0)


class TestExperimentValidation:
    """Test experiment validation"""
    
    def test_valid_experiment(self):
        """Test valid experiment passes"""
        exp = ExperimentFactory.create()
        assert_valid_experiment(exp)
    
    def test_missing_required_field(self):
        """Test experiment missing required field fails"""
        exp = {"id": "123", "title": "Test"}
        with pytest.raises(AssertionError, match="Invalid experiment"):
            assert_valid_experiment(exp)
    
    def test_invalid_status(self):
        """Test invalid status fails"""
        exp = ExperimentFactory.create(status="invalid")
        with pytest.raises(AssertionError, match="Invalid status"):
            assert_valid_experiment(exp)


class TestDatasetValidation:
    """Test dataset validation"""
    
    def test_valid_dataset(self):
        """Test valid dataset passes"""
        ds = DatasetFactory.create()
        assert_valid_dataset(ds)
    
    def test_missing_data_field(self):
        """Test dataset missing data fails"""
        ds = {"id": "123", "label": "Test", "kind": "test", "created_at": "2025-01-01T00:00:00Z"}
        with pytest.raises(AssertionError, match="Invalid dataset"):
            assert_valid_dataset(ds)


class TestJobValidation:
    """Test job validation"""
    
    def test_valid_job(self):
        """Test valid job passes"""
        job = JobFactory.create()
        assert_valid_job(job)
    
    def test_invalid_job_status(self):
        """Test invalid job status fails"""
        job = JobFactory.create(status="invalid")
        with pytest.raises(AssertionError, match="Invalid job status"):
            assert_valid_job(job)


class TestSchemaValidation:
    """Test schema compliance"""
    
    def test_schema_compliant(self):
        """Test schema compliant data passes"""
        data = {"name": "Test", "value": 42}
        schema = {
            "name": {"type": "string", "required": True},
            "value": {"type": "integer", "required": False}
        }
        assert_schema_compliant(data, schema)
    
    def test_missing_required_field(self):
        """Test missing required field fails"""
        data = {"value": 42}
        schema = {
            "name": {"type": "string", "required": True},
            "value": {"type": "integer"}
        }
        with pytest.raises(AssertionError, match="Missing required field"):
            assert_schema_compliant(data, schema)
    
    def test_wrong_type(self):
        """Test wrong type fails"""
        data = {"name": 123}
        schema = {"name": {"type": "string"}}
        with pytest.raises(AssertionError, match="has type"):
            assert_schema_compliant(data, schema)


class TestWorkflowValidation:
    """Test workflow validation"""
    
    def test_valid_workflow(self):
        """Test valid workflow passes"""
        workflow = JobFactory.create_workflow(n_jobs=3)
        assert_workflow_valid(workflow)
    
    def test_empty_workflow(self):
        """Test empty workflow fails"""
        with pytest.raises(AssertionError, match="cannot be empty"):
            assert_workflow_valid([])


class TestSpectrumValidation:
    """Test spectrum validation"""
    
    def test_valid_spectrum(self):
        """Test valid spectrum passes"""
        spectrum = generate_test_spectrum(n_peaks=10)
        assert_spectrum_valid(spectrum)
    
    def test_empty_spectrum(self):
        """Test empty spectrum fails"""
        with pytest.raises(AssertionError, match="cannot be empty"):
            assert_spectrum_valid([])
    
    def test_missing_mz(self):
        """Test peak missing m/z fails"""
        spectrum = [{"intensity": 100.0}]
        with pytest.raises(AssertionError, match="missing 'mz' field"):
            assert_spectrum_valid(spectrum)
    
    def test_unsorted_spectrum(self):
        """Test unsorted spectrum fails"""
        spectrum = [
            {"mz": 200.0, "intensity": 50.0},
            {"mz": 100.0, "intensity": 100.0}
        ]
        with pytest.raises(AssertionError, match="must be sorted"):
            assert_spectrum_valid(spectrum, require_sorted=True)


class TestTestingIntegration:
    """Test integrated testing utilities"""
    
    def test_factory_to_validation(self):
        """Test factory output validates correctly"""
        exp = ExperimentFactory.create()
        assert_valid_experiment(exp)
        
        ds = DatasetFactory.create()
        assert_valid_dataset(ds)
        
        job = JobFactory.create()
        assert_valid_job(job)
    
    def test_generated_spectrum_validates(self):
        """Test generated spectrum passes validation"""
        spectrum = generate_test_spectrum(n_peaks=20)
        assert_spectrum_valid(spectrum)
    
    def test_performance_with_generated_data(self):
        """Test benchmarking with generated data"""
        def process_spectrum():
            spec = generate_test_spectrum(n_peaks=100, seed=42)
            return sum(p["intensity"] for p in spec)
        
        bench = PerformanceBenchmark("spectrum_processing")
        result = bench.run(process_spectrum, iterations=50)
        
        assert result.iterations == 50
        assert result.execution_time > 0
