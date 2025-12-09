"""
Tests for ML module

Comprehensive tests for explainable ML features.
"""

import pytest
import math
from labos.modules.ml.feature_importance import (
    calculate_variance, calculate_correlation,
    permutation_importance, correlation_importance, variance_importance,
    select_features_by_importance, rank_features_by_multiple_methods
)
from labos.modules.ml.model_validation import (
    calculate_confusion_matrix, calculate_roc_curve,
    cross_validate, generate_learning_curve,
    calculate_regression_metrics, calculate_classification_report
)
from labos.modules.ml.prediction_models import (
    train_linear_regression, predict_with_linear_regression,
    train_knn, predict_knn,
    train_decision_tree, predict_decision_tree,
    normalize_features, apply_normalization
)
from labos.modules.ml.drift_detection import (
    calculate_distribution_stats, kolmogorov_smirnov_test,
    population_stability_index, detect_feature_drift,
    detect_dataset_drift, detect_performance_drift,
    generate_drift_report, simulate_drift_scenario
)


class TestFeatureImportance:
    """Test feature importance analysis"""
    
    def test_calculate_variance(self):
        """Test variance calculation"""
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        variance = calculate_variance(data)
        assert abs(variance - 2.0) < 0.01
    
    def test_calculate_correlation(self):
        """Test correlation calculation"""
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [2.0, 4.0, 6.0, 8.0, 10.0]  # Perfect correlation
        corr = calculate_correlation(x, y)
        assert abs(corr - 1.0) < 0.01
    
    def test_permutation_importance(self):
        """Test permutation importance"""
        feature_data = {
            "f1": [1.0, 2.0, 3.0, 4.0],
            "f2": [2.0, 4.0, 6.0, 8.0]
        }
        y = [3.0, 6.0, 9.0, 12.0]  # y = f1 + f2
        
        def model_predict(features):
            # Predict sum of features
            n = len(features["f1"])
            return [features["f1"][i] + features["f2"][i] for i in range(n)]
        
        def metric(y_true, y_pred):
            mae = sum(abs(y_true[i] - y_pred[i]) for i in range(len(y_true))) / len(y_true)
            return 1.0 / (1.0 + mae)
        
        result = permutation_importance(feature_data, y, model_predict, metric, n_repeats=5)
        assert len(result.feature_importances) == 2
        assert all(f.importance_score >= 0 for f in result.feature_importances)
    
    def test_correlation_importance(self):
        """Test correlation-based importance"""
        feature_data = {
            "f1": [1.0, 2.0, 3.0, 4.0],
            "f2": [5.0, 5.0, 5.0, 5.0]
        }
        y = [1.0, 2.0, 3.0, 4.0]  # Perfectly correlated with f1, not with f2
        
        result = correlation_importance(feature_data, y)
        assert len(result.feature_importances) == 2
        # f1 should have higher importance
        f1_score = next(f.importance_score for f in result.feature_importances if f.feature_name == "f1")
        f2_score = next(f.importance_score for f in result.feature_importances if f.feature_name == "f2")
        assert f1_score > f2_score
    
    def test_variance_importance(self):
        """Test variance-based importance"""
        feature_data = {
            "f1": [1.0, 2.0, 3.0, 4.0],
            "f2": [5.0, 5.0, 5.0, 5.0]
        }
        # f1 has variance, f2 is constant
        
        result = variance_importance(feature_data)
        assert len(result.feature_importances) == 2
        # f1 should have higher importance
        f1_score = next(f.importance_score for f in result.feature_importances if f.feature_name == "f1")
        f2_score = next(f.importance_score for f in result.feature_importances if f.feature_name == "f2")
        assert f1_score > f2_score
    
    def test_feature_selection(self):
        """Test feature selection"""
        feature_data = {
            "f1": [1.0, 2.0, 3.0, 4.0],
            "f2": [5.0, 5.0, 5.0, 5.0],
            "f3": [10.0, 20.0, 30.0, 40.0]
        }
        # f1 and f3 vary, f2 is constant
        
        result = variance_importance(feature_data)
        selection = select_features_by_importance(result, threshold=0.1)
        
        assert len(selection.selected_features) > 0
        assert len(selection.selected_features) <= 3
    
    def test_multi_method_ranking(self):
        """Test ranking with multiple methods"""
        feature_data = {
            "f1": [1.0, 2.0, 3.0, 4.0],
            "f2": [2.0, 4.0, 6.0, 8.0]
        }
        y = [3.0, 6.0, 9.0, 12.0]
        
        results_dict = rank_features_by_multiple_methods(feature_data, y)
        assert "correlation" in results_dict
        assert "variance" in results_dict
        
        # Test aggregation
        from labos.modules.ml.feature_importance import aggregate_feature_rankings
        aggregated = aggregate_feature_rankings(results_dict)
        assert len(aggregated) == 2
        assert all(isinstance(name, str) and score > 0 for name, score in aggregated)


class TestModelValidation:
    """Test model validation metrics"""
    
    def test_confusion_matrix(self):
        """Test confusion matrix calculation"""
        y_true = [1, 1, 0, 0, 1, 0]
        y_pred = [1, 0, 0, 0, 1, 1]
        
        cm = calculate_confusion_matrix(y_true, y_pred)
        assert cm.true_positives == 2
        assert cm.true_negatives == 2
        assert cm.false_positives == 1
        assert cm.false_negatives == 1
        assert 0 <= cm.accuracy <= 1
        assert 0 <= cm.precision <= 1
        assert 0 <= cm.recall <= 1
    
    def test_roc_curve(self):
        """Test ROC curve calculation"""
        y_true = [1, 1, 0, 0, 1, 0, 1, 0]
        y_scores = [0.9, 0.8, 0.4, 0.3, 0.7, 0.2, 0.85, 0.35]
        
        roc = calculate_roc_curve(y_true, y_scores, n_thresholds=10)
        assert 0 <= roc.auc <= 1
        assert len(roc.points) == 10
        assert roc.optimal_threshold is not None
    
    def test_cross_validation(self):
        """Test k-fold cross-validation"""
        X = [[i] for i in range(20)]
        y = [i * 2 for i in range(20)]
        
        def model_fn(X_train, y_train, X_val, y_val):
            # Simple average predictor
            predictions = [sum(y_train) / len(y_train)] * len(y_val)
            mae = sum(abs(predictions[i] - y_val[i]) for i in range(len(y_val))) / len(y_val)
            return 1.0 / (1.0 + mae)
        
        result = cross_validate(X, y, model_fn, n_folds=4)
        assert len(result.fold_scores) == 4
        assert result.mean_score > 0
        assert result.std_score >= 0
    
    def test_regression_metrics(self):
        """Test regression metrics"""
        y_true = [3.0, -0.5, 2.0, 7.0]
        y_pred = [2.5, 0.0, 2.0, 8.0]
        
        metrics = calculate_regression_metrics(y_true, y_pred)
        assert metrics.mae > 0
        assert metrics.rmse > 0
        assert 0 <= metrics.r_squared <= 1
        assert len(metrics.residuals) == len(y_true)
    
    def test_learning_curve(self):
        """Test learning curve generation"""
        X = [[i] for i in range(50)]
        y = [i * 2 + 1 for i in range(50)]
        
        def model_fn(X_train, y_train):
            # Simple model that improves with more data
            train_score = 0.5 + len(X_train) / 100
            val_score = 0.4 + len(X_train) / 120
            return train_score, val_score
        
        curve = generate_learning_curve(X, y, model_fn, train_sizes=[10, 20, 30, 40, 50])
        assert len(curve.training_sizes) == 5
        assert len(curve.train_scores) == 5
        assert len(curve.validation_scores) == 5
    
    def test_classification_report(self):
        """Test multi-class classification report"""
        y_true = [0, 1, 2, 0, 1, 2, 0, 1]
        y_pred = [0, 1, 2, 0, 2, 2, 0, 1]
        
        report = calculate_classification_report(y_true, y_pred)
        assert len(report) == 3
        for class_metrics in report.values():
            assert 0 <= class_metrics.accuracy <= 1


class TestPredictionModels:
    """Test prediction models"""
    
    def test_linear_regression(self):
        """Test linear regression training"""
        X = [[1.0], [2.0], [3.0], [4.0]]
        y = [2.0, 4.0, 6.0, 8.0]  # y = 2x
        
        model = train_linear_regression(X, y, feature_names=["x"])
        assert model.trained_samples == 4
        assert abs(model.coefficients[0] - 2.0) < 0.5  # Should be close to 2
        assert model.r_squared > 0.9
    
    def test_linear_regression_prediction(self):
        """Test linear regression prediction"""
        X = [[1.0], [2.0], [3.0], [4.0]]
        y = [3.0, 5.0, 7.0, 9.0]  # y = 2x + 1
        
        model = train_linear_regression(X, y, feature_names=["x"])
        result = predict_with_linear_regression(model, [5.0])
        
        assert result.prediction > 10.0  # Should predict ~11
        assert 0 <= result.confidence <= 1
        assert "x" in result.feature_contributions
    
    def test_knn_model(self):
        """Test KNN model"""
        X = [[1.0], [2.0], [3.0], [4.0]]
        y = [2.0, 4.0, 6.0, 8.0]
        
        model = train_knn(X, y, k=2, feature_names=["x"])
        assert model.k == 2
        assert len(model.X_train) == 4
    
    def test_knn_prediction(self):
        """Test KNN prediction"""
        X = [[1.0], [2.0], [3.0], [4.0]]
        y = [2.0, 4.0, 6.0, 8.0]
        
        model = train_knn(X, y, k=2, feature_names=["x"])
        result = predict_knn(model, [2.5])
        
        # Should predict average of 2 nearest (2.0 and 3.0)
        assert 2.0 < result.prediction < 6.0
        assert len(result.similar_examples) == 2
    
    def test_decision_tree(self):
        """Test decision tree training"""
        X = [[1.0], [2.0], [3.0], [4.0], [5.0], [6.0]]
        y = [1.0, 1.0, 1.0, 2.0, 2.0, 2.0]
        
        model = train_decision_tree(X, y, feature_names=["x"], max_depth=2, min_samples_split=2)
        assert len(model.rules) >= 0
        assert model.max_depth == 2
    
    def test_decision_tree_prediction(self):
        """Test decision tree prediction"""
        X = [[1.0], [2.0], [3.0], [4.0], [5.0], [6.0]] * 3  # More samples
        y = [1.0, 1.0, 1.0, 2.0, 2.0, 2.0] * 3
        
        model = train_decision_tree(X, y, feature_names=["x"], max_depth=2, min_samples_split=4)
        result = predict_decision_tree(model, [2.5])
        
        # Should predict something reasonable
        assert result.prediction >= 0
        assert 0 <= result.confidence <= 1
    
    def test_feature_normalization(self):
        """Test feature normalization"""
        X = [[10.0, 100.0], [20.0, 200.0], [30.0, 300.0]]
        
        X_norm, means, stds = normalize_features(X)
        
        # Normalized features should have mean ~0 and std ~1
        for j in range(2):
            col = [row[j] for row in X_norm]
            col_mean = sum(col) / len(col)
            assert abs(col_mean) < 0.01  # Near zero
    
    def test_apply_normalization(self):
        """Test applying learned normalization"""
        X = [[10.0], [20.0], [30.0]]
        X_norm, means, stds = normalize_features(X)
        
        x_new = [25.0]
        x_new_norm = apply_normalization(x_new, means, stds)
        
        assert len(x_new_norm) == 1


class TestDriftDetection:
    """Test drift detection"""
    
    def test_distribution_stats(self):
        """Test distribution statistics"""
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        stats = calculate_distribution_stats(data)
        
        assert abs(stats.mean - 3.0) < 0.01
        assert stats.median == 3.0
        assert stats.min == 1.0
        assert stats.max == 5.0
    
    def test_kolmogorov_smirnov(self):
        """Test KS test"""
        ref = [1.0, 2.0, 3.0, 4.0, 5.0]
        cur_same = [1.0, 2.0, 3.0, 4.0, 5.0]
        cur_different = [10.0, 20.0, 30.0, 40.0, 50.0]
        
        ks_same = kolmogorov_smirnov_test(ref, cur_same)
        ks_diff = kolmogorov_smirnov_test(ref, cur_different)
        
        assert ks_same < 0.01  # Should be very small
        assert ks_diff > 0.5   # Should be large
    
    def test_population_stability_index(self):
        """Test PSI calculation"""
        ref = [1.0, 2.0, 3.0, 4.0, 5.0] * 10
        cur_same = [1.0, 2.0, 3.0, 4.0, 5.0] * 10
        cur_shifted = [2.0, 3.0, 4.0, 5.0, 6.0] * 10
        
        psi_same = population_stability_index(ref, cur_same)
        psi_shifted = population_stability_index(ref, cur_shifted)
        
        assert psi_same < 0.1  # Low drift
        assert psi_shifted > psi_same  # Higher drift
    
    def test_feature_drift_detection(self):
        """Test single feature drift detection"""
        ref = [1.0, 2.0, 3.0, 4.0, 5.0] * 10
        cur_drifted = [3.0, 4.0, 5.0, 6.0, 7.0] * 10
        
        drift = detect_feature_drift(ref, cur_drifted, "test_feature", method='psi')
        
        assert drift.drift_score > 0
        assert drift.feature_name == "test_feature"
        assert drift.reference_stats.mean < drift.current_stats.mean
    
    def test_dataset_drift_detection(self):
        """Test multi-feature drift detection"""
        ref_X = [[1.0, 10.0], [2.0, 20.0], [3.0, 30.0]] * 10
        cur_X = [[2.0, 10.0], [3.0, 20.0], [4.0, 30.0]] * 10  # First feature drifted
        
        drifts = detect_dataset_drift(ref_X, cur_X, feature_names=["f1", "f2"])
        
        assert len(drifts) == 2
        # f1 should show drift, f2 should not
        f1_drift = next(d for d in drifts if d.feature_name == "f1")
        f2_drift = next(d for d in drifts if d.feature_name == "f2")
        assert f1_drift.drift_score > f2_drift.drift_score
    
    def test_performance_drift(self):
        """Test performance drift detection"""
        ref_metric = 0.95
        cur_degraded = 0.85
        
        drift = detect_performance_drift(ref_metric, cur_degraded, "accuracy", threshold=0.05)
        
        assert drift.is_degrading
        assert drift.drift_amount > 0
    
    def test_drift_report(self):
        """Test comprehensive drift report"""
        ref_X = [[1.0, 10.0], [2.0, 20.0], [3.0, 30.0]] * 10
        cur_X = [[2.0, 10.0], [3.0, 20.0], [4.0, 30.0]] * 10
        
        report = generate_drift_report(
            ref_X, cur_X,
            feature_names=["f1", "f2"],
            reference_performance=0.95,
            current_performance=0.93
        )
        
        assert len(report.feature_drifts) == 2
        assert report.performance_drift is not None
        assert len(report.recommendations) > 0
    
    def test_simulate_mean_shift(self):
        """Test mean shift simulation"""
        data = [1.0, 2.0, 3.0, 4.0, 5.0] * 10
        drifted = simulate_drift_scenario(data, drift_type='mean_shift', drift_magnitude=1.0)
        
        original_mean = sum(data) / len(data)
        drifted_mean = sum(drifted) / len(drifted)
        
        assert drifted_mean > original_mean
    
    def test_simulate_variance_shift(self):
        """Test variance shift simulation"""
        data = [1.0, 2.0, 3.0, 4.0, 5.0] * 10
        drifted = simulate_drift_scenario(data, drift_type='variance_shift', drift_magnitude=1.0)
        
        # Variance should increase
        original_stats = calculate_distribution_stats(data)
        drifted_stats = calculate_distribution_stats(drifted)
        
        assert drifted_stats.std > original_stats.std


class TestMLIntegration:
    """Test integrated ML workflows"""
    
    def test_feature_selection_to_modeling(self):
        """Test workflow from feature selection to model training"""
        X = [[1.0, 5.0, 2.0], [2.0, 5.0, 4.0], [3.0, 5.0, 6.0], [4.0, 5.0, 8.0]]
        y = [3.0, 6.0, 9.0, 12.0]
        
        # Select features
        feature_data = {"f1": [1.0, 2.0, 3.0, 4.0], "f2": [5.0, 5.0, 5.0, 5.0], "f3": [2.0, 4.0, 6.0, 8.0]}
        result = variance_importance(feature_data)
        selection = select_features_by_importance(result, threshold=0.1)
        
        # Get selected indices
        selected_names = selection.selected_features
        all_names = ["f1", "f2", "f3"]
        selected_indices = [i for i, name in enumerate(all_names) if name in selected_names]
        
        # Train on selected features
        X_selected = [[row[i] for i in selected_indices] for row in X]
        model = train_linear_regression(X_selected, y, feature_names=selected_names)
        
        assert model.trained_samples == 4
        assert len(model.coefficients) == len(selected_names)
    
    def test_model_validation_workflow(self):
        """Test complete model validation workflow"""
        X = [[i] for i in range(100)]
        y = [i * 2 + 1 for i in range(100)]
        
        # Train model
        model = train_linear_regression(X[:80], y[:80], feature_names=["x"])
        
        # Validate on test set
        y_pred = [predict_with_linear_regression(model, [X[i][0]]).prediction 
                  for i in range(80, 100)]
        y_true = y[80:100]
        
        metrics = calculate_regression_metrics(y_true, y_pred)
        
        assert metrics.r_squared > 0.9
        assert metrics.mae < 1.0
    
    def test_drift_monitoring_workflow(self):
        """Test production drift monitoring workflow"""
        # Training data
        ref_X = [[1.0], [2.0], [3.0], [4.0]] * 10
        ref_y = [2.0, 4.0, 6.0, 8.0] * 10
        
        # Train model
        model = train_linear_regression(ref_X, ref_y, feature_names=["x"])
        
        # Production data (drifted)
        cur_X = [[2.0], [3.0], [4.0], [5.0]] * 10
        cur_y = [4.0, 6.0, 8.0, 10.0] * 10
        
        # Detect drift
        report = generate_drift_report(ref_X, cur_X, feature_names=["x"])
        
        # Calculate performance on both
        ref_pred = [predict_with_linear_regression(model, x).prediction for x in ref_X]
        cur_pred = [predict_with_linear_regression(model, x).prediction for x in cur_X]
        
        ref_metrics = calculate_regression_metrics(ref_y, ref_pred)
        cur_metrics = calculate_regression_metrics(cur_y, cur_pred)
        
        assert report.n_drifting_features >= 0
        assert ref_metrics.r_squared > 0
