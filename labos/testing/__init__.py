"""
Testing Infrastructure

Comprehensive testing utilities for LabOS.
"""

from labos.testing.fixtures import (
    ExperimentFactory,
    DatasetFactory,
    JobFactory,
    generate_test_spectrum,
    generate_test_dataset
)
from labos.testing.performance import (
    PerformanceBenchmark,
    measure_execution_time,
    measure_memory_usage,
    BenchmarkResult
)
from labos.testing.data_generators import (
    generate_molecular_formula,
    generate_spectrum_data,
    generate_kinetics_data,
    generate_proteomics_data,
    DataGenerator
)
from labos.testing.assertions import (
    assert_valid_experiment,
    assert_valid_dataset,
    assert_valid_job,
    assert_schema_compliant,
    ValidationAssertion
)

__all__ = [
    # Fixtures
    "ExperimentFactory",
    "DatasetFactory", 
    "JobFactory",
    "generate_test_spectrum",
    "generate_test_dataset",
    
    # Performance
    "PerformanceBenchmark",
    "measure_execution_time",
    "measure_memory_usage",
    "BenchmarkResult",
    
    # Data generators
    "generate_molecular_formula",
    "generate_spectrum_data",
    "generate_kinetics_data",
    "generate_proteomics_data",
    "DataGenerator",
    
    # Assertions
    "assert_valid_experiment",
    "assert_valid_dataset",
    "assert_valid_job",
    "assert_schema_compliant",
    "ValidationAssertion"
]
