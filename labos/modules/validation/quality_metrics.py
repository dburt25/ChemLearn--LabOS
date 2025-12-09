"""
Quality Metrics Module

Calculate data quality metrics aligned with ALCOA+ principles.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import math


@dataclass
class DataQualityMetrics:
    """Comprehensive data quality metrics"""
    completeness: float  # 0-1
    consistency: float  # 0-1
    accuracy: float  # 0-1
    timeliness: float  # 0-1
    validity: float  # 0-1
    uniqueness: float  # 0-1
    overall_score: float  # 0-1


@dataclass
class QualityReport:
    """Detailed quality report"""
    metrics: DataQualityMetrics
    total_records: int
    complete_records: int
    missing_value_counts: Dict[str, int]
    duplicate_count: int
    validation_errors: int
    recommendations: List[str]
    summary: str


def calculate_completeness(
    data: List[Dict[str, Any]],
    required_fields: List[str] = None
) -> float:
    """
    Calculate data completeness score.
    
    Args:
        data: List of data records
        required_fields: List of required field names
        
    Returns:
        Completeness score (0-1)
    """
    if not data:
        return 0.0
    
    if required_fields is None:
        # Consider all fields
        all_fields = set()
        for record in data:
            all_fields.update(record.keys())
        required_fields = list(all_fields)
    
    if not required_fields:
        return 1.0
    
    # Count non-null values
    total_cells = len(data) * len(required_fields)
    filled_cells = 0
    
    for record in data:
        for field in required_fields:
            value = record.get(field)
            if value is not None and value != "":
                filled_cells += 1
    
    return filled_cells / total_cells if total_cells > 0 else 0.0


def calculate_consistency(
    data: List[Dict[str, Any]],
    consistency_rules: List[Dict[str, Any]] = None
) -> float:
    """
    Calculate data consistency score.
    
    Args:
        data: List of data records
        consistency_rules: List of consistency rules to check
        
    Returns:
        Consistency score (0-1)
    """
    if not data:
        return 1.0
    
    # Default consistency checks
    violations = 0
    total_checks = 0
    
    # Check 1: Numeric fields have consistent types
    numeric_fields = {}
    for record in data:
        for key, value in record.items():
            if value is not None:
                if isinstance(value, (int, float)):
                    if key not in numeric_fields:
                        numeric_fields[key] = []
                    numeric_fields[key].append(type(value).__name__)
    
    for field, types in numeric_fields.items():
        total_checks += 1
        # Check if all same type
        if len(set(types)) > 1:
            violations += 1
    
    # Check 2: Categorical fields have reasonable cardinality
    for record in data:
        for key, value in record.items():
            if isinstance(value, str):
                total_checks += 1
                # Check for reasonable string length
                if len(value) > 1000:
                    violations += 1
    
    # Check 3: Date fields are properly formatted
    # (simplified - just check they're not obviously wrong)
    for record in data:
        for key in record.keys():
            if "date" in key.lower() or "time" in key.lower():
                total_checks += 1
                value = record[key]
                if value is not None and not isinstance(value, str):
                    violations += 1
    
    if total_checks == 0:
        return 1.0
    
    return 1.0 - (violations / total_checks)


def calculate_accuracy_proxies(
    data: List[Dict[str, Any]]
) -> float:
    """
    Calculate accuracy proxies (without ground truth).
    
    Args:
        data: List of data records
        
    Returns:
        Accuracy proxy score (0-1)
    """
    if not data:
        return 1.0
    
    issues = 0
    total_checks = 0
    
    for record in data:
        for key, value in record.items():
            total_checks += 1
            
            # Check for obvious errors
            if value is None:
                continue
            
            # Negative values where they shouldn't be
            if "count" in key.lower() or "amount" in key.lower():
                if isinstance(value, (int, float)) and value < 0:
                    issues += 1
            
            # Percentages out of range
            if "percent" in key.lower() or "pct" in key.lower():
                if isinstance(value, (int, float)) and (value < 0 or value > 100):
                    issues += 1
            
            # Extremely large values (potential data entry errors)
            if isinstance(value, (int, float)):
                if abs(value) > 1e10:
                    issues += 1
    
    if total_checks == 0:
        return 1.0
    
    return 1.0 - (issues / total_checks)


def calculate_timeliness(
    data: List[Dict[str, Any]],
    timestamp_field: str = "timestamp"
) -> float:
    """
    Calculate data timeliness score.
    
    Args:
        data: List of data records
        timestamp_field: Name of timestamp field
        
    Returns:
        Timeliness score (0-1)
    """
    # Simplified: check if timestamp field exists and is populated
    if not data:
        return 1.0
    
    has_timestamp = 0
    for record in data:
        if timestamp_field in record and record[timestamp_field] is not None:
            has_timestamp += 1
    
    return has_timestamp / len(data)


def calculate_validity(
    data: List[Dict[str, Any]],
    validation_rules: Dict[str, Any] = None
) -> float:
    """
    Calculate data validity score.
    
    Args:
        data: List of data records
        validation_rules: Validation rules
        
    Returns:
        Validity score (0-1)
    """
    if not data:
        return 1.0
    
    valid_records = 0
    
    for record in data:
        is_valid = True
        
        # Basic validity checks
        for key, value in record.items():
            if value is not None:
                # Check for suspicious patterns
                if isinstance(value, str):
                    # Empty strings
                    if value.strip() == "":
                        is_valid = False
                        break
                    
                    # Placeholder values
                    if value.lower() in ["n/a", "null", "none", "unknown", "todo"]:
                        is_valid = False
                        break
        
        if is_valid:
            valid_records += 1
    
    return valid_records / len(data)


def calculate_uniqueness(
    data: List[Dict[str, Any]],
    key_fields: List[str] = None
) -> float:
    """
    Calculate data uniqueness score.
    
    Args:
        data: List of data records
        key_fields: Fields that should be unique
        
    Returns:
        Uniqueness score (0-1)
    """
    if not data:
        return 1.0
    
    # Count duplicates
    if key_fields:
        # Check uniqueness of key fields
        seen = set()
        duplicates = 0
        
        for record in data:
            key = tuple(record.get(field) for field in key_fields)
            if key in seen:
                duplicates += 1
            seen.add(key)
        
        return 1.0 - (duplicates / len(data))
    else:
        # Check overall record uniqueness
        seen = set()
        duplicates = 0
        
        for record in data:
            # Convert to hashable
            record_tuple = tuple(sorted(record.items()))
            if record_tuple in seen:
                duplicates += 1
            seen.add(record_tuple)
        
        return 1.0 - (duplicates / len(data))


def assess_data_quality(
    data: List[Dict[str, Any]],
    required_fields: List[str] = None,
    key_fields: List[str] = None,
    timestamp_field: str = "timestamp"
) -> QualityReport:
    """
    Comprehensive data quality assessment.
    
    Args:
        data: List of data records
        required_fields: Required field names
        key_fields: Fields that should be unique
        timestamp_field: Timestamp field name
        
    Returns:
        QualityReport
    """
    # Calculate all metrics
    completeness = calculate_completeness(data, required_fields)
    consistency = calculate_consistency(data)
    accuracy = calculate_accuracy_proxies(data)
    timeliness = calculate_timeliness(data, timestamp_field)
    validity = calculate_validity(data)
    uniqueness = calculate_uniqueness(data, key_fields)
    
    # Overall score (weighted average)
    overall = (
        completeness * 0.25 +
        consistency * 0.20 +
        accuracy * 0.20 +
        validity * 0.20 +
        uniqueness * 0.15
    )
    
    metrics = DataQualityMetrics(
        completeness=completeness,
        consistency=consistency,
        accuracy=accuracy,
        timeliness=timeliness,
        validity=validity,
        uniqueness=uniqueness,
        overall_score=overall
    )
    
    # Count missing values
    missing_counts = {}
    if required_fields:
        for field in required_fields:
            missing = sum(1 for record in data 
                         if record.get(field) is None or record.get(field) == "")
            if missing > 0:
                missing_counts[field] = missing
    
    # Count complete records
    complete = sum(
        1 for record in data
        if all(record.get(field) not in [None, ""] for field in (required_fields or record.keys()))
    )
    
    # Count duplicates
    seen = set()
    duplicates = 0
    for record in data:
        record_tuple = tuple(sorted(record.items()))
        if record_tuple in seen:
            duplicates += 1
        seen.add(record_tuple)
    
    # Generate recommendations
    recommendations = []
    
    if completeness < 0.8:
        recommendations.append(
            f"Low completeness ({completeness:.1%}). Review data collection procedures."
        )
    
    if consistency < 0.9:
        recommendations.append(
            f"Consistency issues detected ({consistency:.1%}). Check data types and formats."
        )
    
    if accuracy < 0.95:
        recommendations.append(
            f"Potential accuracy issues ({accuracy:.1%}). Validate suspicious values."
        )
    
    if validity < 0.9:
        recommendations.append(
            f"Invalid records found ({validity:.1%}). Remove placeholder values."
        )
    
    if uniqueness < 0.95:
        recommendations.append(
            f"Duplicate records detected ({uniqueness:.1%}). Deduplicate dataset."
        )
    
    if not recommendations:
        recommendations.append("Data quality is good. Continue monitoring.")
    
    # Summary
    summary = f"Quality Score: {overall:.1%}. "
    summary += f"{complete}/{len(data)} complete records. "
    if duplicates > 0:
        summary += f"{duplicates} duplicates. "
    if missing_counts:
        summary += f"Missing values in {len(missing_counts)} fields."
    
    return QualityReport(
        metrics=metrics,
        total_records=len(data),
        complete_records=complete,
        missing_value_counts=missing_counts,
        duplicate_count=duplicates,
        validation_errors=int((1 - validity) * len(data)),
        recommendations=recommendations,
        summary=summary
    )


def compare_quality_over_time(
    reports: List[QualityReport]
) -> Dict[str, List[float]]:
    """
    Track quality metrics over time.
    
    Args:
        reports: List of QualityReport objects over time
        
    Returns:
        Dictionary of metric trends
    """
    trends = {
        "completeness": [r.metrics.completeness for r in reports],
        "consistency": [r.metrics.consistency for r in reports],
        "accuracy": [r.metrics.accuracy for r in reports],
        "validity": [r.metrics.validity for r in reports],
        "uniqueness": [r.metrics.uniqueness for r in reports],
        "overall": [r.metrics.overall_score for r in reports]
    }
    
    return trends
