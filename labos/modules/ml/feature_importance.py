"""
Feature Importance Analysis Module

Provides interpretable feature importance metrics for ML models
without requiring external ML libraries (educational implementations).
"""

from dataclasses import dataclass
from typing import List, Dict, Tuple, Callable, Optional
import random
import math


@dataclass
class FeatureImportance:
    """Feature importance result"""
    feature_name: str
    importance_score: float
    rank: int
    percentage: float  # Percentage of total importance
    confidence_interval: Tuple[float, float]  # (lower, upper)
    

@dataclass
class FeatureImportanceResult:
    """Complete feature importance analysis"""
    feature_importances: List[FeatureImportance]
    method: str  # "permutation", "coefficient", "variance"
    baseline_score: float  # Original model score
    total_importance: float
    top_features: List[str]  # Top N most important features
    notes: List[str]


@dataclass
class FeatureSelection:
    """Results from feature selection"""
    selected_features: List[str]
    rejected_features: List[str]
    selection_threshold: float
    total_features: int
    selected_count: int
    explained_variance: float  # How much variance is explained
    notes: List[str]


def calculate_variance(values: List[float]) -> float:
    """Calculate variance of a list of values"""
    if not values:
        return 0.0
    
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    return variance


def calculate_correlation(x: List[float], y: List[float]) -> float:
    """
    Calculate Pearson correlation coefficient between two variables.
    
    Args:
        x: First variable values
        y: Second variable values
        
    Returns:
        Correlation coefficient (-1 to 1)
    """
    if len(x) != len(y) or len(x) == 0:
        return 0.0
    
    n = len(x)
    mean_x = sum(x) / n
    mean_y = sum(y) / n
    
    numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    
    std_x = math.sqrt(sum((xi - mean_x) ** 2 for xi in x) / n)
    std_y = math.sqrt(sum((yi - mean_y) ** 2 for yi in y) / n)
    
    denominator = std_x * std_y * n
    
    if denominator == 0:
        return 0.0
    
    return numerator / denominator


def permutation_importance(
    feature_data: Dict[str, List[float]],
    target: List[float],
    model_predict: Callable[[Dict[str, List[float]]], List[float]],
    metric: Callable[[List[float], List[float]], float],
    n_repeats: int = 10
) -> FeatureImportanceResult:
    """
    Calculate feature importance using permutation method.
    
    Args:
        feature_data: Dictionary of feature_name -> values
        target: Target values
        model_predict: Function that takes features and returns predictions
        metric: Scoring function (higher is better)
        n_repeats: Number of permutation repeats
        
    Returns:
        FeatureImportanceResult
    """
    # Calculate baseline score
    baseline_predictions = model_predict(feature_data)
    baseline_score = metric(target, baseline_predictions)
    
    importances = []
    feature_names = list(feature_data.keys())
    
    for feature_name in feature_names:
        importance_scores = []
        
        # Repeat permutation multiple times
        for _ in range(n_repeats):
            # Create copy of data with this feature permuted
            permuted_data = feature_data.copy()
            original_values = feature_data[feature_name].copy()
            permuted_values = original_values.copy()
            random.shuffle(permuted_values)
            permuted_data[feature_name] = permuted_values
            
            # Calculate score with permuted feature
            permuted_predictions = model_predict(permuted_data)
            permuted_score = metric(target, permuted_predictions)
            
            # Importance is decrease in score
            importance = baseline_score - permuted_score
            importance_scores.append(importance)
        
        # Average importance over repeats
        mean_importance = sum(importance_scores) / len(importance_scores)
        std_importance = math.sqrt(calculate_variance(importance_scores))
        
        # Confidence interval (mean ± 1.96*std for 95% CI)
        ci_lower = mean_importance - 1.96 * std_importance
        ci_upper = mean_importance + 1.96 * std_importance
        
        importances.append({
            "name": feature_name,
            "importance": max(0, mean_importance),  # Clip negative values
            "ci": (ci_lower, ci_upper)
        })
    
    # Sort by importance
    importances.sort(key=lambda x: x["importance"], reverse=True)
    
    # Calculate percentages
    total_importance = sum(imp["importance"] for imp in importances)
    
    # Create FeatureImportance objects
    feature_importance_objs = []
    for rank, imp in enumerate(importances, 1):
        percentage = (imp["importance"] / total_importance * 100) if total_importance > 0 else 0
        feature_importance_objs.append(FeatureImportance(
            feature_name=imp["name"],
            importance_score=imp["importance"],
            rank=rank,
            percentage=percentage,
            confidence_interval=imp["ci"]
        ))
    
    # Get top features (top 5 or all if less than 5)
    top_n = min(5, len(feature_importance_objs))
    top_features = [f.feature_name for f in feature_importance_objs[:top_n]]
    
    notes = [
        f"Permutation importance with {n_repeats} repeats",
        f"Baseline model score: {baseline_score:.4f}",
        f"Top feature: {top_features[0] if top_features else 'None'}",
        f"Total features analyzed: {len(feature_names)}"
    ]
    
    return FeatureImportanceResult(
        feature_importances=feature_importance_objs,
        method="permutation",
        baseline_score=baseline_score,
        total_importance=total_importance,
        top_features=top_features,
        notes=notes
    )


def correlation_importance(
    feature_data: Dict[str, List[float]],
    target: List[float]
) -> FeatureImportanceResult:
    """
    Calculate feature importance based on correlation with target.
    Simple but interpretable method.
    
    Args:
        feature_data: Dictionary of feature_name -> values
        target: Target values
        
    Returns:
        FeatureImportanceResult
    """
    importances = []
    
    for feature_name, values in feature_data.items():
        # Calculate absolute correlation (direction doesn't matter for importance)
        corr = abs(calculate_correlation(values, target))
        importances.append({
            "name": feature_name,
            "importance": corr,
            "ci": (corr * 0.9, corr * 1.1)  # Rough CI estimate
        })
    
    # Sort by importance
    importances.sort(key=lambda x: x["importance"], reverse=True)
    
    # Calculate percentages
    total_importance = sum(imp["importance"] for imp in importances)
    
    feature_importance_objs = []
    for rank, imp in enumerate(importances, 1):
        percentage = (imp["importance"] / total_importance * 100) if total_importance > 0 else 0
        feature_importance_objs.append(FeatureImportance(
            feature_name=imp["name"],
            importance_score=imp["importance"],
            rank=rank,
            percentage=percentage,
            confidence_interval=imp["ci"]
        ))
    
    top_n = min(5, len(feature_importance_objs))
    top_features = [f.feature_name for f in feature_importance_objs[:top_n]]
    
    notes = [
        "Correlation-based importance",
        "Measures linear relationship with target",
        f"Top feature: {top_features[0] if top_features else 'None'}",
        f"Total features: {len(feature_data)}"
    ]
    
    return FeatureImportanceResult(
        feature_importances=feature_importance_objs,
        method="correlation",
        baseline_score=0.0,
        total_importance=total_importance,
        top_features=top_features,
        notes=notes
    )


def variance_importance(
    feature_data: Dict[str, List[float]]
) -> FeatureImportanceResult:
    """
    Calculate feature importance based on variance.
    High variance features may be more informative.
    
    Args:
        feature_data: Dictionary of feature_name -> values
        
    Returns:
        FeatureImportanceResult
    """
    importances = []
    
    for feature_name, values in feature_data.items():
        variance = calculate_variance(values)
        importances.append({
            "name": feature_name,
            "importance": variance,
            "ci": (variance * 0.9, variance * 1.1)
        })
    
    importances.sort(key=lambda x: x["importance"], reverse=True)
    
    total_importance = sum(imp["importance"] for imp in importances)
    
    feature_importance_objs = []
    for rank, imp in enumerate(importances, 1):
        percentage = (imp["importance"] / total_importance * 100) if total_importance > 0 else 0
        feature_importance_objs.append(FeatureImportance(
            feature_name=imp["name"],
            importance_score=imp["importance"],
            rank=rank,
            percentage=percentage,
            confidence_interval=imp["ci"]
        ))
    
    top_n = min(5, len(feature_importance_objs))
    top_features = [f.feature_name for f in feature_importance_objs[:top_n]]
    
    notes = [
        "Variance-based importance",
        "High variance features may contain more information",
        f"Total features: {len(feature_data)}"
    ]
    
    return FeatureImportanceResult(
        feature_importances=feature_importance_objs,
        method="variance",
        baseline_score=0.0,
        total_importance=total_importance,
        top_features=top_features,
        notes=notes
    )


def select_features_by_importance(
    importance_result: FeatureImportanceResult,
    threshold: float = 0.05,  # Keep features with >5% importance
    max_features: Optional[int] = None
) -> FeatureSelection:
    """
    Select features based on importance threshold.
    
    Args:
        importance_result: Result from importance analysis
        threshold: Minimum importance percentage to keep
        max_features: Maximum number of features to select
        
    Returns:
        FeatureSelection
    """
    selected = []
    rejected = []
    
    for feature_imp in importance_result.feature_importances:
        if feature_imp.percentage >= threshold:
            selected.append(feature_imp.feature_name)
        else:
            rejected.append(feature_imp.feature_name)
    
    # Apply max_features limit if specified
    if max_features and len(selected) > max_features:
        rejected.extend(selected[max_features:])
        selected = selected[:max_features]
    
    # Calculate explained variance (sum of selected feature importances)
    explained_variance = sum(
        f.percentage for f in importance_result.feature_importances
        if f.feature_name in selected
    )
    
    notes = [
        f"Selected {len(selected)} of {len(importance_result.feature_importances)} features",
        f"Threshold: {threshold * 100:.1f}% importance",
        f"Explained variance: {explained_variance:.2f}%",
        f"Method: {importance_result.method}"
    ]
    
    return FeatureSelection(
        selected_features=selected,
        rejected_features=rejected,
        selection_threshold=threshold,
        total_features=len(importance_result.feature_importances),
        selected_count=len(selected),
        explained_variance=explained_variance,
        notes=notes
    )


def rank_features_by_multiple_methods(
    feature_data: Dict[str, List[float]],
    target: List[float]
) -> Dict[str, FeatureImportanceResult]:
    """
    Rank features using multiple methods for robust analysis.
    
    Args:
        feature_data: Dictionary of feature_name -> values
        target: Target values
        
    Returns:
        Dictionary of method_name -> FeatureImportanceResult
    """
    results = {}
    
    # Correlation method
    results["correlation"] = correlation_importance(feature_data, target)
    
    # Variance method
    results["variance"] = variance_importance(feature_data)
    
    return results


def aggregate_feature_rankings(
    results: Dict[str, FeatureImportanceResult]
) -> List[Tuple[str, float]]:
    """
    Aggregate rankings from multiple methods using Borda count.
    
    Args:
        results: Dictionary of method -> FeatureImportanceResult
        
    Returns:
        List of (feature_name, aggregate_score) sorted by score
    """
    # Collect all features
    all_features = set()
    for result in results.values():
        all_features.update(f.feature_name for f in result.feature_importances)
    
    # Calculate Borda count for each feature
    borda_scores = {feature: 0 for feature in all_features}
    
    for result in results.values():
        n_features = len(result.feature_importances)
        for feature_imp in result.feature_importances:
            # Borda count: highest rank gets n points, lowest gets 1
            points = n_features - feature_imp.rank + 1
            borda_scores[feature_imp.feature_name] += points
    
    # Sort by aggregate score
    sorted_features = sorted(borda_scores.items(), key=lambda x: x[1], reverse=True)
    
    return sorted_features
