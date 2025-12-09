"""
Consistency Checks Module

Validate data consistency across records and relationships.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Callable
from enum import Enum


class CheckType(Enum):
    """Types of consistency checks"""
    RANGE = "range"
    RELATIONSHIP = "relationship"
    TEMPORAL = "temporal"
    CROSS_FIELD = "cross_field"
    REFERENTIAL = "referential"


@dataclass
class ConsistencyCheck:
    """Definition of a consistency check"""
    name: str
    check_type: CheckType
    description: str
    check_function: Callable
    severity: str = "error"  # error, warning, info


@dataclass
class ConsistencyResult:
    """Result of consistency validation"""
    check_name: str
    passed: bool
    violations: List[Dict[str, Any]]
    total_checked: int
    pass_rate: float
    explanation: str


def check_value_ranges(
    data: List[Dict[str, Any]],
    range_rules: Dict[str, tuple]
) -> ConsistencyResult:
    """
    Check if values fall within expected ranges.
    
    Args:
        data: List of data records
        range_rules: Dict of field_name -> (min, max)
        
    Returns:
        ConsistencyResult
    """
    violations = []
    total_checks = 0
    
    for idx, record in enumerate(data):
        for field, (min_val, max_val) in range_rules.items():
            if field in record:
                value = record[field]
                total_checks += 1
                
                if value is not None:
                    try:
                        value_float = float(value)
                        if value_float < min_val or value_float > max_val:
                            violations.append({
                                "row_index": idx,
                                "field": field,
                                "value": value,
                                "expected_range": f"[{min_val}, {max_val}]",
                                "reason": "Out of range"
                            })
                    except (ValueError, TypeError):
                        violations.append({
                            "row_index": idx,
                            "field": field,
                            "value": value,
                            "expected_range": f"[{min_val}, {max_val}]",
                            "reason": "Non-numeric value"
                        })
    
    pass_rate = (total_checks - len(violations)) / total_checks if total_checks > 0 else 1.0
    
    explanation = f"Checked {total_checks} values against {len(range_rules)} range rules. "
    explanation += f"{len(violations)} violations found ({pass_rate:.1%} pass rate)."
    
    return ConsistencyResult(
        check_name="Value Range Check",
        passed=len(violations) == 0,
        violations=violations,
        total_checked=total_checks,
        pass_rate=pass_rate,
        explanation=explanation
    )


def check_relationships(
    data: List[Dict[str, Any]],
    relationship_rules: List[Dict[str, Any]]
) -> ConsistencyResult:
    """
    Check relationships between fields.
    
    Args:
        data: List of data records
        relationship_rules: List of relationship definitions
            Example: {"field1": "A", "operator": "<=", "field2": "B"}
        
    Returns:
        ConsistencyResult
    """
    violations = []
    total_checks = 0
    
    for idx, record in enumerate(data):
        for rule in relationship_rules:
            field1 = rule.get("field1")
            field2 = rule.get("field2")
            operator = rule.get("operator", "==")
            
            if field1 in record and field2 in record:
                val1 = record[field1]
                val2 = record[field2]
                total_checks += 1
                
                if val1 is not None and val2 is not None:
                    try:
                        val1_num = float(val1)
                        val2_num = float(val2)
                        
                        valid = False
                        if operator == "==":
                            valid = val1_num == val2_num
                        elif operator == "!=":
                            valid = val1_num != val2_num
                        elif operator == "<":
                            valid = val1_num < val2_num
                        elif operator == "<=":
                            valid = val1_num <= val2_num
                        elif operator == ">":
                            valid = val1_num > val2_num
                        elif operator == ">=":
                            valid = val1_num >= val2_num
                        
                        if not valid:
                            violations.append({
                                "row_index": idx,
                                "field1": field1,
                                "value1": val1,
                                "operator": operator,
                                "field2": field2,
                                "value2": val2,
                                "reason": f"Relationship {field1} {operator} {field2} violated"
                            })
                    except (ValueError, TypeError):
                        violations.append({
                            "row_index": idx,
                            "field1": field1,
                            "value1": val1,
                            "operator": operator,
                            "field2": field2,
                            "value2": val2,
                            "reason": "Non-numeric values in comparison"
                        })
    
    pass_rate = (total_checks - len(violations)) / total_checks if total_checks > 0 else 1.0
    
    explanation = f"Checked {total_checks} relationships. "
    explanation += f"{len(violations)} violations found ({pass_rate:.1%} pass rate)."
    
    return ConsistencyResult(
        check_name="Relationship Check",
        passed=len(violations) == 0,
        violations=violations,
        total_checked=total_checks,
        pass_rate=pass_rate,
        explanation=explanation
    )


def check_temporal_consistency(
    data: List[Dict[str, Any]],
    temporal_fields: List[str]
) -> ConsistencyResult:
    """
    Check temporal consistency (chronological order).
    
    Args:
        data: List of data records
        temporal_fields: List of timestamp/date field names
        
    Returns:
        ConsistencyResult
    """
    violations = []
    total_checks = 0
    
    # Check if timestamps are in order
    for field in temporal_fields:
        prev_value = None
        
        for idx, record in enumerate(data):
            if field in record:
                value = record[field]
                total_checks += 1
                
                if value is not None and prev_value is not None:
                    # Simple string comparison (assumes ISO format)
                    if isinstance(value, str) and isinstance(prev_value, str):
                        if value < prev_value:
                            violations.append({
                                "row_index": idx,
                                "field": field,
                                "value": value,
                                "previous_value": prev_value,
                                "reason": "Timestamp out of chronological order"
                            })
                
                prev_value = value
    
    pass_rate = (total_checks - len(violations)) / total_checks if total_checks > 0 else 1.0
    
    explanation = f"Checked {total_checks} temporal values across {len(temporal_fields)} fields. "
    explanation += f"{len(violations)} violations found ({pass_rate:.1%} pass rate)."
    
    return ConsistencyResult(
        check_name="Temporal Consistency Check",
        passed=len(violations) == 0,
        violations=violations,
        total_checked=total_checks,
        pass_rate=pass_rate,
        explanation=explanation
    )


def check_cross_field_logic(
    data: List[Dict[str, Any]],
    logic_rules: List[Dict[str, Any]]
) -> ConsistencyResult:
    """
    Check complex cross-field logical constraints.
    
    Args:
        data: List of data records
        logic_rules: List of logic rule definitions
            Example: {"condition": "status=='active'", "then": "end_date==null"}
        
    Returns:
        ConsistencyResult
    """
    violations = []
    total_checks = 0
    
    for idx, record in enumerate(data):
        for rule in logic_rules:
            total_checks += 1
            
            # Simplified logic evaluation
            condition = rule.get("condition", "")
            then_clause = rule.get("then", "")
            
            # Very basic evaluation (for demonstration)
            # In production, would use safer evaluation
            try:
                # Check if condition is met
                condition_met = False
                if "==" in condition:
                    field, value = condition.split("==")
                    field = field.strip()
                    value = value.strip().strip("'\"")
                    if field in record and str(record[field]) == value:
                        condition_met = True
                
                # If condition met, check consequence
                if condition_met:
                    consequence_met = False
                    if "==" in then_clause:
                        field, value = then_clause.split("==")
                        field = field.strip()
                        value = value.strip().strip("'\"")
                        
                        if value.lower() == "null":
                            consequence_met = record.get(field) is None
                        else:
                            consequence_met = str(record.get(field)) == value
                    
                    if not consequence_met:
                        violations.append({
                            "row_index": idx,
                            "rule": rule,
                            "reason": f"Logic rule violated: if {condition} then {then_clause}"
                        })
            except Exception:
                # Skip malformed rules
                pass
    
    pass_rate = (total_checks - len(violations)) / total_checks if total_checks > 0 else 1.0
    
    explanation = f"Checked {total_checks} logic rules. "
    explanation += f"{len(violations)} violations found ({pass_rate:.1%} pass rate)."
    
    return ConsistencyResult(
        check_name="Cross-field Logic Check",
        passed=len(violations) == 0,
        violations=violations,
        total_checked=total_checks,
        pass_rate=pass_rate,
        explanation=explanation
    )


def check_referential_integrity(
    data: List[Dict[str, Any]],
    reference_data: Dict[str, List[Any]],
    foreign_keys: Dict[str, str]
) -> ConsistencyResult:
    """
    Check referential integrity (foreign key constraints).
    
    Args:
        data: List of data records
        reference_data: Dict of table_name -> list of valid IDs
        foreign_keys: Dict of field_name -> reference_table_name
        
    Returns:
        ConsistencyResult
    """
    violations = []
    total_checks = 0
    
    for idx, record in enumerate(data):
        for field, ref_table in foreign_keys.items():
            if field in record:
                value = record[field]
                total_checks += 1
                
                if value is not None:
                    valid_ids = reference_data.get(ref_table, [])
                    if value not in valid_ids:
                        violations.append({
                            "row_index": idx,
                            "field": field,
                            "value": value,
                            "reference_table": ref_table,
                            "reason": "Foreign key constraint violated"
                        })
    
    pass_rate = (total_checks - len(violations)) / total_checks if total_checks > 0 else 1.0
    
    explanation = f"Checked {total_checks} foreign key references. "
    explanation += f"{len(violations)} violations found ({pass_rate:.1%} pass rate)."
    
    return ConsistencyResult(
        check_name="Referential Integrity Check",
        passed=len(violations) == 0,
        violations=violations,
        total_checked=total_checks,
        pass_rate=pass_rate,
        explanation=explanation
    )


def validate_dataset_consistency(
    data: List[Dict[str, Any]],
    range_rules: Dict[str, tuple] = None,
    relationship_rules: List[Dict[str, Any]] = None,
    temporal_fields: List[str] = None,
    logic_rules: List[Dict[str, Any]] = None
) -> Dict[str, ConsistencyResult]:
    """
    Run comprehensive consistency validation.
    
    Args:
        data: List of data records
        range_rules: Value range rules
        relationship_rules: Field relationship rules
        temporal_fields: Temporal field names
        logic_rules: Cross-field logic rules
        
    Returns:
        Dictionary of check results
    """
    results = {}
    
    if range_rules:
        results["range"] = check_value_ranges(data, range_rules)
    
    if relationship_rules:
        results["relationship"] = check_relationships(data, relationship_rules)
    
    if temporal_fields:
        results["temporal"] = check_temporal_consistency(data, temporal_fields)
    
    if logic_rules:
        results["logic"] = check_cross_field_logic(data, logic_rules)
    
    return results


def generate_consistency_report(
    results: Dict[str, ConsistencyResult]
) -> str:
    """
    Generate human-readable consistency report.
    
    Args:
        results: Dictionary of check results
        
    Returns:
        Formatted report string
    """
    report = "Data Consistency Report\n"
    report += "=" * 50 + "\n\n"
    
    total_checks = sum(r.total_checked for r in results.values())
    total_violations = sum(len(r.violations) for r in results.values())
    overall_pass_rate = (total_checks - total_violations) / total_checks if total_checks > 0 else 1.0
    
    report += f"Overall: {total_checks} checks performed\n"
    report += f"Pass Rate: {overall_pass_rate:.1%}\n"
    report += f"Violations: {total_violations}\n\n"
    
    for check_name, result in results.items():
        report += f"{result.check_name}\n"
        report += "-" * 40 + "\n"
        report += f"Status: {'PASSED' if result.passed else 'FAILED'}\n"
        report += f"{result.explanation}\n"
        
        if result.violations and len(result.violations) <= 5:
            report += "Violations:\n"
            for violation in result.violations[:5]:
                report += f"  - Row {violation.get('row_index', '?')}: {violation.get('reason', 'Unknown')}\n"
        elif result.violations:
            report += f"First 5 of {len(result.violations)} violations:\n"
            for violation in result.violations[:5]:
                report += f"  - Row {violation.get('row_index', '?')}: {violation.get('reason', 'Unknown')}\n"
        
        report += "\n"
    
    return report
