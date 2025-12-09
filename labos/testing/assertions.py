"""
Custom Test Assertions

Specialized assertion functions for testing LabOS components.
"""

from typing import Dict, Any, List, Optional


class ValidationAssertion:
    """
    Base class for custom assertions
    
    Educational Note:
        Custom assertions provide clear, domain-specific
        error messages that help diagnose test failures quickly.
    """
    
    @staticmethod
    def assert_dict_contains(
        data: Dict[str, Any],
        required_keys: List[str],
        message: Optional[str] = None
    ):
        """
        Assert dictionary contains required keys
        
        Args:
            data: Dictionary to check
            required_keys: Required key names
            message: Optional error message
            
        Raises:
            AssertionError: If any key is missing
        """
        missing = [key for key in required_keys if key not in data]
        
        if missing:
            error_msg = f"Missing required keys: {missing}"
            if message:
                error_msg = f"{message}: {error_msg}"
            raise AssertionError(error_msg)
    
    @staticmethod
    def assert_valid_timestamp(timestamp: str, message: Optional[str] = None):
        """
        Assert string is valid ISO timestamp
        
        Args:
            timestamp: Timestamp string
            message: Optional error message
            
        Raises:
            AssertionError: If timestamp is invalid
        """
        from datetime import datetime
        
        try:
            datetime.fromisoformat(timestamp.rstrip('Z'))
        except (ValueError, AttributeError) as e:
            error_msg = f"Invalid timestamp format: {timestamp}"
            if message:
                error_msg = f"{message}: {error_msg}"
            raise AssertionError(error_msg) from e
    
    @staticmethod
    def assert_numeric_range(
        value: float,
        min_val: float,
        max_val: float,
        message: Optional[str] = None
    ):
        """
        Assert value is within numeric range
        
        Args:
            value: Value to check
            min_val: Minimum value (inclusive)
            max_val: Maximum value (inclusive)
            message: Optional error message
            
        Raises:
            AssertionError: If value is out of range
        """
        if not (min_val <= value <= max_val):
            error_msg = f"Value {value} not in range [{min_val}, {max_val}]"
            if message:
                error_msg = f"{message}: {error_msg}"
            raise AssertionError(error_msg)


def assert_valid_experiment(experiment: Dict[str, Any]):
    """
    Assert experiment has valid structure
    
    Args:
        experiment: Experiment dictionary
        
    Raises:
        AssertionError: If validation fails
        
    Educational Note:
        Validation assertions catch schema violations early,
        preventing invalid data from propagating through system.
    """
    required_keys = ["id", "title", "status", "created_at", "updated_at"]
    ValidationAssertion.assert_dict_contains(
        experiment,
        required_keys,
        "Invalid experiment"
    )
    
    # Validate timestamps
    ValidationAssertion.assert_valid_timestamp(
        experiment["created_at"],
        "Experiment created_at"
    )
    ValidationAssertion.assert_valid_timestamp(
        experiment["updated_at"],
        "Experiment updated_at"
    )
    
    # Validate status
    valid_statuses = ["draft", "running", "completed", "failed", "archived"]
    if experiment["status"] not in valid_statuses:
        raise AssertionError(
            f"Invalid status '{experiment['status']}'. "
            f"Must be one of {valid_statuses}"
        )


def assert_valid_dataset(dataset: Dict[str, Any]):
    """
    Assert dataset has valid structure
    
    Args:
        dataset: Dataset dictionary
        
    Raises:
        AssertionError: If validation fails
    """
    required_keys = ["id", "label", "kind", "data", "created_at"]
    ValidationAssertion.assert_dict_contains(
        dataset,
        required_keys,
        "Invalid dataset"
    )
    
    # Validate timestamp
    ValidationAssertion.assert_valid_timestamp(
        dataset["created_at"],
        "Dataset created_at"
    )
    
    # Validate data is dictionary
    if not isinstance(dataset["data"], dict):
        raise AssertionError(
            f"Dataset data must be dictionary, got {type(dataset['data'])}"
        )


def assert_valid_job(job: Dict[str, Any]):
    """
    Assert job has valid structure
    
    Args:
        job: Job dictionary
        
    Raises:
        AssertionError: If validation fails
    """
    required_keys = ["id", "module_key", "status", "params", "created_at"]
    ValidationAssertion.assert_dict_contains(
        job,
        required_keys,
        "Invalid job"
    )
    
    # Validate timestamp
    ValidationAssertion.assert_valid_timestamp(
        job["created_at"],
        "Job created_at"
    )
    
    # Validate status
    valid_statuses = ["queued", "running", "completed", "failed"]
    if job["status"] not in valid_statuses:
        raise AssertionError(
            f"Invalid job status '{job['status']}'. "
            f"Must be one of {valid_statuses}"
        )
    
    # Validate params is dictionary
    if not isinstance(job["params"], dict):
        raise AssertionError(
            f"Job params must be dictionary, got {type(job['params'])}"
        )


def assert_schema_compliant(
    data: Dict[str, Any],
    schema: Dict[str, Any]
):
    """
    Assert data matches schema definition
    
    Args:
        data: Data to validate
        schema: Schema definition with field types
        
    Raises:
        AssertionError: If data doesn't match schema
        
    Educational Note:
        Schema validation ensures data consistency across
        system boundaries and storage layers.
    """
    for field_name, field_def in schema.items():
        # Check required fields
        if field_def.get("required", False) and field_name not in data:
            raise AssertionError(f"Missing required field: {field_name}")
        
        # Check field type if present
        if field_name in data:
            value = data[field_name]
            expected_type = field_def.get("type")
            
            if expected_type:
                type_map = {
                    "string": str,
                    "integer": int,
                    "float": float,
                    "boolean": bool,
                    "dict": dict,
                    "list": list
                }
                
                python_type = type_map.get(expected_type)
                if python_type and not isinstance(value, python_type):
                    raise AssertionError(
                        f"Field '{field_name}' has type {type(value).__name__}, "
                        f"expected {expected_type}"
                    )


def assert_workflow_valid(workflow: List[Dict[str, Any]]):
    """
    Assert workflow has valid structure
    
    Args:
        workflow: List of job dictionaries
        
    Raises:
        AssertionError: If workflow is invalid
    """
    if not workflow:
        raise AssertionError("Workflow cannot be empty")
    
    # Validate each job
    for i, job in enumerate(workflow):
        try:
            assert_valid_job(job)
        except AssertionError as e:
            raise AssertionError(f"Invalid job at position {i}: {e}") from e
    
    # Check experiment ID consistency
    exp_ids = [job.get("experiment_id") for job in workflow if "experiment_id" in job]
    if exp_ids and len(set(exp_ids)) > 1:
        raise AssertionError(
            f"Workflow has inconsistent experiment IDs: {set(exp_ids)}"
        )


def assert_spectrum_valid(
    spectrum: List[Dict[str, float]],
    require_sorted: bool = True
):
    """
    Assert spectrum data has valid structure
    
    Args:
        spectrum: List of peak dictionaries
        require_sorted: Whether peaks must be sorted by m/z
        
    Raises:
        AssertionError: If spectrum is invalid
    """
    if not spectrum:
        raise AssertionError("Spectrum cannot be empty")
    
    for i, peak in enumerate(spectrum):
        # Check required fields
        if "mz" not in peak:
            raise AssertionError(f"Peak {i} missing 'mz' field")
        if "intensity" not in peak:
            raise AssertionError(f"Peak {i} missing 'intensity' field")
        
        # Check numeric types
        if not isinstance(peak["mz"], (int, float)):
            raise AssertionError(f"Peak {i} 'mz' must be numeric")
        if not isinstance(peak["intensity"], (int, float)):
            raise AssertionError(f"Peak {i} 'intensity' must be numeric")
        
        # Check positive values
        if peak["mz"] <= 0:
            raise AssertionError(f"Peak {i} 'mz' must be positive")
        if peak["intensity"] < 0:
            raise AssertionError(f"Peak {i} 'intensity' must be non-negative")
    
    # Check sorting if required
    if require_sorted:
        mz_values = [p["mz"] for p in spectrum]
        if mz_values != sorted(mz_values):
            raise AssertionError("Spectrum peaks must be sorted by m/z")
