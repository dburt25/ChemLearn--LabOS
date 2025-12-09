"""
Schema Validation Module

Define and validate data schemas for experimental datasets.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Set
from enum import Enum


class FieldType(Enum):
    """Data types for schema fields"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    CATEGORICAL = "categorical"


class SeverityLevel(Enum):
    """Issue severity levels"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class FieldRule:
    """Validation rule for a field"""
    field_name: str
    field_type: FieldType
    required: bool = False
    nullable: bool = False
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    allowed_values: Optional[Set[Any]] = None
    pattern: Optional[str] = None
    description: str = ""


@dataclass
class DataSchema:
    """Complete schema definition"""
    name: str
    version: str
    fields: List[FieldRule]
    description: str = ""
    
    def get_field(self, field_name: str) -> Optional[FieldRule]:
        """Get field rule by name"""
        for field in self.fields:
            if field.field_name == field_name:
                return field
        return None


@dataclass
class ValidationIssue:
    """Single validation issue"""
    severity: SeverityLevel
    field_name: str
    row_index: Optional[int]
    message: str
    actual_value: Any
    expected: str


@dataclass
class ValidationResult:
    """Complete validation result"""
    is_valid: bool
    issues: List[ValidationIssue]
    total_rows: int
    valid_rows: int
    error_count: int
    warning_count: int
    info_count: int
    summary: str


def validate_field_value(
    value: Any,
    rule: FieldRule
) -> List[ValidationIssue]:
    """
    Validate a single field value against its rule.
    
    Args:
        value: Value to validate
        rule: Field rule
        
    Returns:
        List of validation issues
    """
    issues = []
    
    # Check required
    if value is None:
        if rule.required and not rule.nullable:
            issues.append(ValidationIssue(
                severity=SeverityLevel.ERROR,
                field_name=rule.field_name,
                row_index=None,
                message=f"Required field is missing",
                actual_value=None,
                expected=f"{rule.field_type.value} value"
            ))
        return issues
    
    # Type validation
    if rule.field_type == FieldType.INTEGER:
        if not isinstance(value, int):
            try:
                int(value)
            except (ValueError, TypeError):
                issues.append(ValidationIssue(
                    severity=SeverityLevel.ERROR,
                    field_name=rule.field_name,
                    row_index=None,
                    message="Invalid integer value",
                    actual_value=value,
                    expected="integer"
                ))
                return issues
        value = int(value)
    
    elif rule.field_type == FieldType.FLOAT:
        if not isinstance(value, (int, float)):
            try:
                float(value)
            except (ValueError, TypeError):
                issues.append(ValidationIssue(
                    severity=SeverityLevel.ERROR,
                    field_name=rule.field_name,
                    row_index=None,
                    message="Invalid numeric value",
                    actual_value=value,
                    expected="number"
                ))
                return issues
        value = float(value)
    
    elif rule.field_type == FieldType.STRING:
        if not isinstance(value, str):
            issues.append(ValidationIssue(
                severity=SeverityLevel.WARNING,
                field_name=rule.field_name,
                row_index=None,
                message="Value coerced to string",
                actual_value=value,
                expected="string"
            ))
    
    # Range validation
    if rule.field_type in [FieldType.INTEGER, FieldType.FLOAT]:
        if rule.min_value is not None and value < rule.min_value:
            issues.append(ValidationIssue(
                severity=SeverityLevel.ERROR,
                field_name=rule.field_name,
                row_index=None,
                message=f"Value below minimum",
                actual_value=value,
                expected=f">= {rule.min_value}"
            ))
        
        if rule.max_value is not None and value > rule.max_value:
            issues.append(ValidationIssue(
                severity=SeverityLevel.ERROR,
                field_name=rule.field_name,
                row_index=None,
                message=f"Value above maximum",
                actual_value=value,
                expected=f"<= {rule.max_value}"
            ))
    
    # Categorical validation
    if rule.allowed_values is not None:
        if value not in rule.allowed_values:
            issues.append(ValidationIssue(
                severity=SeverityLevel.ERROR,
                field_name=rule.field_name,
                row_index=None,
                message="Value not in allowed set",
                actual_value=value,
                expected=f"One of {rule.allowed_values}"
            ))
    
    return issues


def validate_schema(
    data: List[Dict[str, Any]],
    schema: DataSchema
) -> ValidationResult:
    """
    Validate dataset against schema.
    
    Args:
        data: List of data records
        schema: Schema to validate against
        
    Returns:
        ValidationResult
    """
    all_issues = []
    valid_rows = 0
    
    for row_idx, row in enumerate(data):
        row_valid = True
        
        # Check each field in schema
        for field_rule in schema.fields:
            value = row.get(field_rule.field_name)
            
            field_issues = validate_field_value(value, field_rule)
            
            for issue in field_issues:
                issue.row_index = row_idx
                all_issues.append(issue)
                
                if issue.severity == SeverityLevel.ERROR:
                    row_valid = False
        
        # Check for unexpected fields
        for field_name in row.keys():
            if schema.get_field(field_name) is None:
                all_issues.append(ValidationIssue(
                    severity=SeverityLevel.WARNING,
                    field_name=field_name,
                    row_index=row_idx,
                    message="Unexpected field not in schema",
                    actual_value=row[field_name],
                    expected="Known field"
                ))
        
        if row_valid:
            valid_rows += 1
    
    # Count by severity
    error_count = sum(1 for i in all_issues if i.severity == SeverityLevel.ERROR)
    warning_count = sum(1 for i in all_issues if i.severity == SeverityLevel.WARNING)
    info_count = sum(1 for i in all_issues if i.severity == SeverityLevel.INFO)
    
    is_valid = error_count == 0
    
    summary = f"Validated {len(data)} rows: {valid_rows} valid, "
    summary += f"{error_count} errors, {warning_count} warnings"
    
    return ValidationResult(
        is_valid=is_valid,
        issues=all_issues,
        total_rows=len(data),
        valid_rows=valid_rows,
        error_count=error_count,
        warning_count=warning_count,
        info_count=info_count,
        summary=summary
    )


def infer_schema(
    data: List[Dict[str, Any]],
    sample_size: int = 100
) -> DataSchema:
    """
    Infer schema from data sample.
    
    Args:
        data: Data records
        sample_size: Number of rows to sample
        
    Returns:
        Inferred DataSchema
    """
    if not data:
        return DataSchema(name="empty", version="1.0", fields=[])
    
    # Sample data
    sample = data[:min(sample_size, len(data))]
    
    # Collect all field names
    all_fields = set()
    for row in sample:
        all_fields.update(row.keys())
    
    # Infer type and properties for each field
    fields = []
    
    for field_name in sorted(all_fields):
        values = [row.get(field_name) for row in sample if field_name in row]
        non_null_values = [v for v in values if v is not None]
        
        # Determine if required
        required = len(non_null_values) == len(sample)
        nullable = len(values) > len(non_null_values)
        
        # Infer type
        if not non_null_values:
            field_type = FieldType.STRING
        else:
            # Check if all are integers
            if all(isinstance(v, int) or (isinstance(v, str) and v.isdigit()) 
                   for v in non_null_values):
                field_type = FieldType.INTEGER
                numeric_values = [int(v) if isinstance(v, str) else v 
                                for v in non_null_values]
                min_value = float(min(numeric_values))
                max_value = float(max(numeric_values))
            
            # Check if all are floats
            elif all(isinstance(v, (int, float)) for v in non_null_values):
                field_type = FieldType.FLOAT
                min_value = float(min(non_null_values))
                max_value = float(max(non_null_values))
            
            # Check if categorical (small unique set)
            elif len(set(non_null_values)) <= 10:
                field_type = FieldType.CATEGORICAL
                allowed_values = set(non_null_values)
                min_value = None
                max_value = None
            
            else:
                field_type = FieldType.STRING
                min_value = None
                max_value = None
        
        # Create field rule
        rule = FieldRule(
            field_name=field_name,
            field_type=field_type,
            required=required,
            nullable=nullable,
            min_value=min_value if field_type in [FieldType.INTEGER, FieldType.FLOAT] else None,
            max_value=max_value if field_type in [FieldType.INTEGER, FieldType.FLOAT] else None,
            allowed_values=allowed_values if field_type == FieldType.CATEGORICAL else None,
            description=f"Inferred from {len(non_null_values)} samples"
        )
        fields.append(rule)
    
    return DataSchema(
        name="inferred_schema",
        version="1.0",
        fields=fields,
        description=f"Inferred from {len(sample)} data records"
    )


def compare_schemas(
    schema1: DataSchema,
    schema2: DataSchema
) -> List[str]:
    """
    Compare two schemas and return differences.
    
    Args:
        schema1: First schema
        schema2: Second schema
        
    Returns:
        List of difference descriptions
    """
    differences = []
    
    # Get field sets
    fields1 = {f.field_name: f for f in schema1.fields}
    fields2 = {f.field_name: f for f in schema2.fields}
    
    # Fields only in schema1
    only_in_1 = set(fields1.keys()) - set(fields2.keys())
    if only_in_1:
        differences.append(f"Fields only in {schema1.name}: {only_in_1}")
    
    # Fields only in schema2
    only_in_2 = set(fields2.keys()) - set(fields1.keys())
    if only_in_2:
        differences.append(f"Fields only in {schema2.name}: {only_in_2}")
    
    # Compare common fields
    common_fields = set(fields1.keys()) & set(fields2.keys())
    for field_name in common_fields:
        f1 = fields1[field_name]
        f2 = fields2[field_name]
        
        if f1.field_type != f2.field_type:
            differences.append(
                f"{field_name}: type mismatch ({f1.field_type.value} vs {f2.field_type.value})"
            )
        
        if f1.required != f2.required:
            differences.append(
                f"{field_name}: required mismatch ({f1.required} vs {f2.required})"
            )
        
        if f1.min_value != f2.min_value or f1.max_value != f2.max_value:
            differences.append(
                f"{field_name}: range mismatch"
            )
    
    return differences
