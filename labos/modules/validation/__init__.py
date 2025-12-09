"""
Data Validation Module

Comprehensive data quality validation for experimental datasets.
Implements GMLP/FDA-aligned validation checks.
"""

from .schema_validation import (
    DataSchema, FieldRule, ValidationResult, ValidationIssue,
    validate_schema, infer_schema, compare_schemas
)

from .outlier_detection import (
    OutlierResult, OutlierMethod,
    detect_outliers_zscore, detect_outliers_iqr,
    detect_outliers_isolation_forest, detect_multivariate_outliers
)

from .quality_metrics import (
    QualityReport, DataQualityMetrics,
    calculate_completeness, calculate_consistency,
    calculate_accuracy_proxies, assess_data_quality
)

from .consistency_checks import (
    ConsistencyCheck, ConsistencyResult,
    check_value_ranges, check_relationships,
    check_temporal_consistency, validate_dataset_consistency
)

__all__ = [
    # Schema validation
    "DataSchema", "FieldRule", "ValidationResult", "ValidationIssue",
    "validate_schema", "infer_schema", "compare_schemas",
    
    # Outlier detection
    "OutlierResult", "OutlierMethod",
    "detect_outliers_zscore", "detect_outliers_iqr",
    "detect_outliers_isolation_forest", "detect_multivariate_outliers",
    
    # Quality metrics
    "QualityReport", "DataQualityMetrics",
    "calculate_completeness", "calculate_consistency",
    "calculate_accuracy_proxies", "assess_data_quality",
    
    # Consistency checks
    "ConsistencyCheck", "ConsistencyResult",
    "check_value_ranges", "check_relationships",
    "check_temporal_consistency", "validate_dataset_consistency"
]
