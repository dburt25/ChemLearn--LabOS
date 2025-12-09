"""
Drift Detection Module

Monitor data and model drift for production ML systems.
Educational implementations for GMLP compliance.
"""

from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import math


@dataclass
class DistributionStats:
    """Statistical summary of a distribution"""
    mean: float
    std: float
    min: float
    max: float
    median: float
    q1: float  # 25th percentile
    q3: float  # 75th percentile
    skewness: float
    kurtosis: float


@dataclass
class DriftScore:
    """Drift detection result for a feature"""
    feature_name: str
    drift_score: float
    is_drifting: bool
    reference_stats: DistributionStats
    current_stats: DistributionStats
    drift_method: str
    threshold: float
    explanation: str


@dataclass
class ModelPerformanceDrift:
    """Model performance drift over time"""
    reference_metric: float
    current_metric: float
    drift_amount: float
    is_degrading: bool
    threshold: float
    metric_name: str
    explanation: str


@dataclass
class DriftReport:
    """Comprehensive drift analysis"""
    feature_drifts: List[DriftScore]
    performance_drift: Optional[ModelPerformanceDrift]
    overall_drift_detected: bool
    n_drifting_features: int
    recommendations: List[str]


def calculate_distribution_stats(data: List[float]) -> DistributionStats:
    """
    Calculate comprehensive distribution statistics.
    
    Args:
        data: List of values
        
    Returns:
        DistributionStats
    """
    n = len(data)
    sorted_data = sorted(data)
    
    # Basic stats
    mean = sum(data) / n
    variance = sum((x - mean) ** 2 for x in data) / n
    std = math.sqrt(variance)
    
    min_val = sorted_data[0]
    max_val = sorted_data[-1]
    
    # Median
    if n % 2 == 0:
        median = (sorted_data[n // 2 - 1] + sorted_data[n // 2]) / 2
    else:
        median = sorted_data[n // 2]
    
    # Quartiles
    q1_idx = n // 4
    q3_idx = 3 * n // 4
    q1 = sorted_data[q1_idx]
    q3 = sorted_data[q3_idx]
    
    # Skewness: E[(X - μ)³] / σ³
    if std > 0:
        skewness = sum((x - mean) ** 3 for x in data) / (n * std ** 3)
    else:
        skewness = 0.0
    
    # Kurtosis: E[(X - μ)⁴] / σ⁴ - 3 (excess kurtosis)
    if std > 0:
        kurtosis = sum((x - mean) ** 4 for x in data) / (n * std ** 4) - 3
    else:
        kurtosis = 0.0
    
    return DistributionStats(
        mean=mean,
        std=std,
        min=min_val,
        max=max_val,
        median=median,
        q1=q1,
        q3=q3,
        skewness=skewness,
        kurtosis=kurtosis
    )


def kolmogorov_smirnov_test(
    reference: List[float],
    current: List[float]
) -> float:
    """
    Calculate Kolmogorov-Smirnov statistic.
    Measures max difference between CDFs.
    
    Args:
        reference: Reference distribution
        current: Current distribution
        
    Returns:
        KS statistic (0 to 1)
    """
    # Combine and sort all values
    all_values = sorted(set(reference + current))
    
    max_diff = 0.0
    
    for value in all_values:
        # Empirical CDF for reference
        cdf_ref = sum(1 for x in reference if x <= value) / len(reference)
        
        # Empirical CDF for current
        cdf_cur = sum(1 for x in current if x <= value) / len(current)
        
        diff = abs(cdf_ref - cdf_cur)
        max_diff = max(max_diff, diff)
    
    return max_diff


def population_stability_index(
    reference: List[float],
    current: List[float],
    n_bins: int = 10
) -> float:
    """
    Calculate Population Stability Index (PSI).
    
    PSI = Σ (current% - reference%) * ln(current% / reference%)
    
    Args:
        reference: Reference distribution
        current: Current distribution
        n_bins: Number of bins for discretization
        
    Returns:
        PSI value (0 = no drift, >0.2 = significant drift)
    """
    # Determine bin edges from reference
    sorted_ref = sorted(reference)
    bin_size = len(sorted_ref) // n_bins
    bin_edges = [sorted_ref[i * bin_size] for i in range(n_bins)]
    bin_edges.append(sorted_ref[-1] + 1e-6)
    
    psi = 0.0
    
    for i in range(n_bins):
        # Count samples in this bin
        ref_count = sum(1 for x in reference if bin_edges[i] <= x < bin_edges[i + 1])
        cur_count = sum(1 for x in current if bin_edges[i] <= x < bin_edges[i + 1])
        
        # Calculate percentages (add small epsilon to avoid log(0))
        ref_pct = (ref_count + 1e-6) / len(reference)
        cur_pct = (cur_count + 1e-6) / len(current)
        
        # PSI contribution
        psi += (cur_pct - ref_pct) * math.log(cur_pct / ref_pct)
    
    return psi


def detect_feature_drift(
    reference_data: List[float],
    current_data: List[float],
    feature_name: str,
    method: str = 'psi',
    threshold: float = None
) -> DriftScore:
    """
    Detect drift in a single feature.
    
    Args:
        reference_data: Reference (training) distribution
        current_data: Current (production) distribution
        feature_name: Name of feature
        method: 'psi' or 'ks'
        threshold: Custom threshold (default: 0.2 for PSI, 0.1 for KS)
        
    Returns:
        DriftScore
    """
    ref_stats = calculate_distribution_stats(reference_data)
    cur_stats = calculate_distribution_stats(current_data)
    
    if method == 'psi':
        drift_score = population_stability_index(reference_data, current_data)
        if threshold is None:
            threshold = 0.2
        explanation = f"PSI = {drift_score:.4f}. "
        if drift_score < 0.1:
            explanation += "No significant drift."
        elif drift_score < 0.2:
            explanation += "Moderate drift detected."
        else:
            explanation += "Significant drift detected!"
    
    elif method == 'ks':
        drift_score = kolmogorov_smirnov_test(reference_data, current_data)
        if threshold is None:
            threshold = 0.1
        explanation = f"KS statistic = {drift_score:.4f}. "
        if drift_score < 0.05:
            explanation += "Distributions are similar."
        elif drift_score < 0.1:
            explanation += "Moderate distribution shift."
        else:
            explanation += "Significant distribution shift!"
    
    else:
        raise ValueError(f"Unknown method: {method}")
    
    is_drifting = drift_score > threshold
    
    # Add distribution comparison
    explanation += f" Reference mean: {ref_stats.mean:.3f}, Current mean: {cur_stats.mean:.3f}."
    
    return DriftScore(
        feature_name=feature_name,
        drift_score=drift_score,
        is_drifting=is_drifting,
        reference_stats=ref_stats,
        current_stats=cur_stats,
        drift_method=method,
        threshold=threshold,
        explanation=explanation
    )


def detect_dataset_drift(
    reference_X: List[List[float]],
    current_X: List[List[float]],
    feature_names: List[str] = None,
    method: str = 'psi'
) -> List[DriftScore]:
    """
    Detect drift across all features in dataset.
    
    Args:
        reference_X: Reference feature matrix
        current_X: Current feature matrix
        feature_names: Optional feature names
        method: Drift detection method
        
    Returns:
        List of DriftScore for each feature
    """
    n_features = len(reference_X[0])
    
    if feature_names is None:
        feature_names = [f"feature_{i}" for i in range(n_features)]
    
    drift_scores = []
    
    for i in range(n_features):
        ref_feature = [row[i] for row in reference_X]
        cur_feature = [row[i] for row in current_X]
        
        drift = detect_feature_drift(
            ref_feature,
            cur_feature,
            feature_names[i],
            method=method
        )
        drift_scores.append(drift)
    
    return drift_scores


def detect_performance_drift(
    reference_metric: float,
    current_metric: float,
    metric_name: str = "accuracy",
    threshold: float = 0.05
) -> ModelPerformanceDrift:
    """
    Detect model performance degradation.
    
    Args:
        reference_metric: Reference (validation) performance
        current_metric: Current (production) performance
        metric_name: Name of metric
        threshold: Acceptable performance drop (default 5%)
        
    Returns:
        ModelPerformanceDrift
    """
    drift_amount = reference_metric - current_metric
    is_degrading = drift_amount > threshold
    
    pct_change = (drift_amount / reference_metric) * 100 if reference_metric > 0 else 0
    
    explanation = f"{metric_name} changed by {pct_change:+.1f}%. "
    if is_degrading:
        explanation += f"Performance degraded beyond threshold ({threshold:.1%})."
    else:
        explanation += "Performance within acceptable range."
    
    return ModelPerformanceDrift(
        reference_metric=reference_metric,
        current_metric=current_metric,
        drift_amount=drift_amount,
        is_degrading=is_degrading,
        threshold=threshold,
        metric_name=metric_name,
        explanation=explanation
    )


def generate_drift_report(
    reference_X: List[List[float]],
    current_X: List[List[float]],
    feature_names: List[str] = None,
    reference_performance: float = None,
    current_performance: float = None,
    performance_metric: str = "accuracy"
) -> DriftReport:
    """
    Generate comprehensive drift report.
    
    Args:
        reference_X: Reference feature matrix
        current_X: Current feature matrix
        feature_names: Optional feature names
        reference_performance: Optional reference model performance
        current_performance: Optional current model performance
        performance_metric: Name of performance metric
        
    Returns:
        DriftReport with recommendations
    """
    # Detect feature drifts
    feature_drifts = detect_dataset_drift(reference_X, current_X, feature_names)
    
    n_drifting = sum(1 for drift in feature_drifts if drift.is_drifting)
    
    # Detect performance drift if provided
    performance_drift = None
    if reference_performance is not None and current_performance is not None:
        performance_drift = detect_performance_drift(
            reference_performance,
            current_performance,
            performance_metric
        )
    
    # Overall drift
    overall_drift = n_drifting > 0 or (performance_drift and performance_drift.is_degrading)
    
    # Generate recommendations
    recommendations = []
    
    if n_drifting > 0:
        recommendations.append(
            f"Data drift detected in {n_drifting}/{len(feature_drifts)} features. "
            "Consider retraining model with recent data."
        )
        
        # Identify most drifted features
        sorted_drifts = sorted(feature_drifts, key=lambda d: d.drift_score, reverse=True)
        top_drifted = [d.feature_name for d in sorted_drifts[:3] if d.is_drifting]
        if top_drifted:
            recommendations.append(
                f"Features with highest drift: {', '.join(top_drifted)}"
            )
    
    if performance_drift and performance_drift.is_degrading:
        recommendations.append(
            f"Model performance degraded: {performance_drift.explanation}"
        )
        recommendations.append("Immediate model retraining recommended.")
    
    if not overall_drift:
        recommendations.append("No significant drift detected. Model is stable.")
    
    return DriftReport(
        feature_drifts=feature_drifts,
        performance_drift=performance_drift,
        overall_drift_detected=overall_drift,
        n_drifting_features=n_drifting,
        recommendations=recommendations
    )


def calculate_drift_severity(drift_scores: List[DriftScore]) -> str:
    """
    Categorize overall drift severity.
    
    Args:
        drift_scores: List of DriftScore
        
    Returns:
        Severity level: 'low', 'medium', 'high'
    """
    n_drifting = sum(1 for d in drift_scores if d.is_drifting)
    pct_drifting = n_drifting / len(drift_scores) if len(drift_scores) > 0 else 0
    
    avg_score = sum(d.drift_score for d in drift_scores) / len(drift_scores) if len(drift_scores) > 0 else 0
    
    if pct_drifting < 0.2 and avg_score < 0.15:
        return 'low'
    elif pct_drifting < 0.5 and avg_score < 0.3:
        return 'medium'
    else:
        return 'high'


def simulate_drift_scenario(
    original_data: List[float],
    drift_type: str = 'mean_shift',
    drift_magnitude: float = 1.0
) -> List[float]:
    """
    Simulate different types of data drift for testing.
    
    Args:
        original_data: Original distribution
        drift_type: 'mean_shift', 'variance_shift', 'distribution_change'
        drift_magnitude: How severe the drift is
        
    Returns:
        Drifted data
    """
    if drift_type == 'mean_shift':
        # Shift mean by drift_magnitude * std
        stats = calculate_distribution_stats(original_data)
        shift = drift_magnitude * stats.std
        return [x + shift for x in original_data]
    
    elif drift_type == 'variance_shift':
        # Scale variance
        stats = calculate_distribution_stats(original_data)
        factor = 1.0 + drift_magnitude
        return [(x - stats.mean) * factor + stats.mean for x in original_data]
    
    elif drift_type == 'distribution_change':
        # Mix with different distribution
        stats = calculate_distribution_stats(original_data)
        # Add random noise proportional to magnitude
        import random
        return [x + random.gauss(0, stats.std * drift_magnitude) for x in original_data]
    
    else:
        return original_data
