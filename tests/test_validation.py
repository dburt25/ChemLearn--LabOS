"""
Tests for Data Validation module

Comprehensive tests for data quality validation.
"""

import pytest
from labos.modules.validation.schema_validation import (
    FieldType, FieldRule, DataSchema, validate_schema, infer_schema, compare_schemas
)
from labos.modules.validation.outlier_detection import (
    detect_outliers_zscore, detect_outliers_iqr, detect_outliers_isolation_forest,
    detect_multivariate_outliers, compare_outlier_methods, consensus_outliers
)
from labos.modules.validation.quality_metrics import (
    calculate_completeness, calculate_consistency, calculate_accuracy_proxies,
    calculate_uniqueness, assess_data_quality
)
from labos.modules.validation.consistency_checks import (
    check_value_ranges, check_relationships, check_temporal_consistency,
    validate_dataset_consistency
)


class TestSchemaValidation:
    """Test schema validation"""
    
    def test_field_rule_creation(self):
        """Test creating field rules"""
        rule = FieldRule(
            field_name="temperature",
            field_type=FieldType.FLOAT,
            required=True,
            min_value=0.0,
            max_value=100.0
        )
        assert rule.field_name == "temperature"
        assert rule.field_type == FieldType.FLOAT
        assert rule.required is True
    
    def test_schema_creation(self):
        """Test creating data schema"""
        fields = [
            FieldRule("id", FieldType.INTEGER, required=True),
            FieldRule("name", FieldType.STRING, required=True)
        ]
        schema = DataSchema(name="test_schema", version="1.0", fields=fields)
        assert len(schema.fields) == 2
        assert schema.get_field("id") is not None
    
    def test_validate_valid_data(self):
        """Test validating correct data"""
        schema = DataSchema(
            name="test",
            version="1.0",
            fields=[
                FieldRule("age", FieldType.INTEGER, required=True, min_value=0, max_value=150)
            ]
        )
        data = [{"age": 25}, {"age": 30}]
        result = validate_schema(data, schema)
        assert result.is_valid
        assert result.error_count == 0
    
    def test_validate_missing_required(self):
        """Test validation catches missing required fields"""
        schema = DataSchema(
            name="test",
            version="1.0",
            fields=[
                FieldRule("name", FieldType.STRING, required=True)
            ]
        )
        data = [{"name": "Alice"}, {}]
        result = validate_schema(data, schema)
        assert not result.is_valid
        assert result.error_count > 0
    
    def test_validate_out_of_range(self):
        """Test validation catches out of range values"""
        schema = DataSchema(
            name="test",
            version="1.0",
            fields=[
                FieldRule("score", FieldType.FLOAT, min_value=0.0, max_value=100.0)
            ]
        )
        data = [{"score": 50.0}, {"score": 150.0}]
        result = validate_schema(data, schema)
        assert not result.is_valid
        assert result.error_count > 0
    
    def test_infer_schema(self):
        """Test schema inference"""
        data = [
            {"id": 1, "name": "Alice", "score": 95.5},
            {"id": 2, "name": "Bob", "score": 87.3}
        ]
        schema = infer_schema(data)
        assert len(schema.fields) == 3
        assert schema.get_field("id") is not None
        assert schema.get_field("name") is not None
    
    def test_infer_categorical(self):
        """Test categorical field inference"""
        data = [
            {"status": "active"},
            {"status": "inactive"},
            {"status": "active"}
        ]
        schema = infer_schema(data)
        status_field = schema.get_field("status")
        assert status_field.field_type == FieldType.CATEGORICAL
        assert status_field.allowed_values is not None
    
    def test_compare_schemas(self):
        """Test schema comparison"""
        schema1 = DataSchema("v1", "1.0", [
            FieldRule("field1", FieldType.INTEGER)
        ])
        schema2 = DataSchema("v2", "2.0", [
            FieldRule("field1", FieldType.STRING),
            FieldRule("field2", FieldType.FLOAT)
        ])
        differences = compare_schemas(schema1, schema2)
        assert len(differences) > 0


class TestOutlierDetection:
    """Test outlier detection methods"""
    
    def test_zscore_no_outliers(self):
        """Test Z-score with normal data"""
        data = [10.0, 11.0, 10.5, 10.2, 10.8]
        result = detect_outliers_zscore(data, threshold=3.0)
        assert result.n_outliers == 0
    
    def test_zscore_with_outliers(self):
        """Test Z-score with outliers"""
        data = [10.0, 11.0, 10.5, 10.2, 10.8, 200.0]  # 200.0 is extreme outlier
        result = detect_outliers_zscore(data, threshold=1.5)  # Lower threshold needed due to mean shift
        assert result.n_outliers > 0
        assert 5 in result.indices  # The 200.0 value
    
    def test_iqr_detection(self):
        """Test IQR method"""
        data = [1.0, 2.0, 3.0, 4.0, 5.0, 100.0]
        result = detect_outliers_iqr(data, k=1.5)
        assert result.n_outliers > 0
        assert 5 in result.indices  # The 100.0 value
    
    def test_iqr_no_outliers(self):
        """Test IQR with uniform data"""
        data = [10.0] * 10
        result = detect_outliers_iqr(data)
        assert result.n_outliers == 0
    
    def test_isolation_forest(self):
        """Test isolation forest"""
        data = [1.0, 2.0, 3.0, 4.0, 5.0, 100.0]
        result = detect_outliers_isolation_forest(data, contamination=0.2)
        assert result.n_outliers > 0
    
    def test_multivariate_outliers(self):
        """Test multivariate outlier detection"""
        data = [
            [1.0, 2.0],
            [1.5, 2.5],
            [1.2, 2.2],
            [1.3, 2.3],
            [100.0, 200.0]  # Extreme outlier
        ]
        result = detect_multivariate_outliers(data, threshold=2.5)  # Lower threshold to catch outlier
        assert result.n_outliers > 0
    
    def test_compare_methods(self):
        """Test comparing multiple methods"""
        data = [1.0, 2.0, 3.0, 4.0, 5.0, 100.0]
        results = compare_outlier_methods(data)
        assert "zscore" in results
        assert "iqr" in results
        assert "isolation_forest" in results
    
    def test_consensus_outliers(self):
        """Test consensus outlier detection"""
        data = [1.0, 2.0, 3.0, 4.0, 5.0, 100.0]
        results = compare_outlier_methods(data)
        consensus = consensus_outliers(results, min_methods=2)
        assert len(consensus) > 0


class TestQualityMetrics:
    """Test data quality metrics"""
    
    def test_completeness_full(self):
        """Test completeness with complete data"""
        data = [
            {"name": "Alice", "age": 25},
            {"name": "Bob", "age": 30}
        ]
        score = calculate_completeness(data, ["name", "age"])
        assert score == 1.0
    
    def test_completeness_partial(self):
        """Test completeness with missing data"""
        data = [
            {"name": "Alice", "age": 25},
            {"name": "Bob"}  # Missing age
        ]
        score = calculate_completeness(data, ["name", "age"])
        assert score < 1.0
    
    def test_consistency(self):
        """Test consistency calculation"""
        data = [
            {"value": 10.5},
            {"value": 20.3},
            {"value": 15.7}
        ]
        score = calculate_consistency(data)
        assert 0.0 <= score <= 1.0
    
    def test_accuracy_proxies(self):
        """Test accuracy proxy calculation"""
        data = [
            {"count": 10, "percent": 50},
            {"count": -5, "percent": 150}  # Invalid
        ]
        score = calculate_accuracy_proxies(data)
        assert score < 1.0
    
    def test_uniqueness_all_unique(self):
        """Test uniqueness with unique records"""
        data = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"}
        ]
        score = calculate_uniqueness(data, key_fields=["id"])
        assert score == 1.0
    
    def test_uniqueness_with_duplicates(self):
        """Test uniqueness with duplicates"""
        data = [
            {"id": 1, "name": "Alice"},
            {"id": 1, "name": "Alice"}  # Duplicate
        ]
        score = calculate_uniqueness(data, key_fields=["id"])
        assert score < 1.0
    
    def test_assess_data_quality(self):
        """Test comprehensive quality assessment"""
        data = [
            {"id": 1, "name": "Alice", "score": 95},
            {"id": 2, "name": "Bob", "score": 87}
        ]
        report = assess_data_quality(data, required_fields=["id", "name", "score"])
        assert report.metrics.overall_score > 0.0
        assert report.total_records == 2
    
    def test_quality_report_completeness(self):
        """Test quality report structure"""
        data = [{"field": "value"}]
        report = assess_data_quality(data)
        assert hasattr(report, "metrics")
        assert hasattr(report, "summary")
        assert len(report.recommendations) > 0


class TestConsistencyChecks:
    """Test consistency validation"""
    
    def test_value_ranges_valid(self):
        """Test range check with valid data"""
        data = [
            {"temperature": 25.0},
            {"temperature": 30.0}
        ]
        result = check_value_ranges(data, {"temperature": (0.0, 100.0)})
        assert result.passed
        assert len(result.violations) == 0
    
    def test_value_ranges_invalid(self):
        """Test range check with invalid data"""
        data = [
            {"temperature": 25.0},
            {"temperature": 150.0}  # Out of range
        ]
        result = check_value_ranges(data, {"temperature": (0.0, 100.0)})
        assert not result.passed
        assert len(result.violations) > 0
    
    def test_relationships_valid(self):
        """Test relationship check"""
        data = [
            {"start": 10, "end": 20},
            {"start": 5, "end": 15}
        ]
        rules = [{"field1": "start", "operator": "<", "field2": "end"}]
        result = check_relationships(data, rules)
        assert result.passed
    
    def test_relationships_invalid(self):
        """Test relationship violation"""
        data = [
            {"start": 20, "end": 10}  # start > end
        ]
        rules = [{"field1": "start", "operator": "<", "field2": "end"}]
        result = check_relationships(data, rules)
        assert not result.passed
    
    def test_temporal_consistency(self):
        """Test temporal order checking"""
        data = [
            {"timestamp": "2025-01-01T00:00:00"},
            {"timestamp": "2025-01-02T00:00:00"},
            {"timestamp": "2025-01-03T00:00:00"}
        ]
        result = check_temporal_consistency(data, ["timestamp"])
        assert result.passed
    
    def test_temporal_inconsistency(self):
        """Test temporal disorder detection"""
        data = [
            {"timestamp": "2025-01-03T00:00:00"},
            {"timestamp": "2025-01-01T00:00:00"}  # Out of order
        ]
        result = check_temporal_consistency(data, ["timestamp"])
        assert not result.passed
    
    def test_validate_dataset_consistency(self):
        """Test comprehensive consistency validation"""
        data = [
            {"value": 50.0, "timestamp": "2025-01-01"}
        ]
        results = validate_dataset_consistency(
            data,
            range_rules={"value": (0.0, 100.0)},
            temporal_fields=["timestamp"]
        )
        assert "range" in results
        assert "temporal" in results


class TestValidationIntegration:
    """Test integrated validation workflows"""
    
    def test_schema_and_quality(self):
        """Test combining schema validation and quality assessment"""
        data = [
            {"id": 1, "name": "Alice", "score": 95},
            {"id": 2, "name": "Bob", "score": 87}
        ]
        
        # Infer schema
        schema = infer_schema(data)
        assert len(schema.fields) == 3
        
        # Validate against schema
        validation = validate_schema(data, schema)
        assert validation.is_valid
        
        # Assess quality
        quality = assess_data_quality(data)
        assert quality.metrics.overall_score > 0.8
    
    def test_outliers_and_consistency(self):
        """Test outlier detection with consistency checks"""
        data = [
            {"value": 10.0, "status": "normal"},
            {"value": 11.0, "status": "normal"},
            {"value": 12.0, "status": "normal"},
            {"value": 500.0, "status": "normal"}  # Extreme outlier
        ]
        
        # Detect outliers
        values = [r["value"] for r in data]
        outliers = detect_outliers_zscore(values, threshold=1.5)  # Lower threshold due to mean shift
        assert outliers.n_outliers > 0
        
        # Check consistency
        result = check_value_ranges(data, {"value": (0.0, 50.0)})
        assert not result.passed
    
    def test_complete_validation_pipeline(self):
        """Test full validation pipeline"""
        data = [
            {"id": 1, "measurement": 25.5, "timestamp": "2025-01-01"},
            {"id": 2, "measurement": 26.2, "timestamp": "2025-01-02"},
            {"id": 3, "measurement": 100.0, "timestamp": "2025-01-03"}  # Potential outlier
        ]
        
        # Step 1: Schema validation
        schema = infer_schema(data)
        validation = validate_schema(data, schema)
        assert validation.is_valid
        
        # Step 2: Quality assessment
        quality = assess_data_quality(data, required_fields=["id", "measurement", "timestamp"])
        assert quality.metrics.completeness == 1.0
        
        # Step 3: Outlier detection
        measurements = [r["measurement"] for r in data]
        outliers = detect_outliers_zscore(measurements)
        assert outliers.n_outliers >= 0
        
        # Step 4: Consistency checks
        consistency = validate_dataset_consistency(
            data,
            range_rules={"measurement": (0.0, 50.0)},
            temporal_fields=["timestamp"]
        )
        assert "range" in consistency
