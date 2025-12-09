"""
Outlier Detection Module

Statistical methods for detecting anomalous data points.
"""

from dataclasses import dataclass
from typing import List, Dict, Tuple
from enum import Enum
import math


class OutlierMethod(Enum):
    """Outlier detection methods"""
    ZSCORE = "zscore"
    IQR = "iqr"
    ISOLATION_FOREST = "isolation_forest"
    MAHALANOBIS = "mahalanobis"


@dataclass
class OutlierResult:
    """Result of outlier detection"""
    indices: List[int]
    scores: List[float]
    threshold: float
    method: OutlierMethod
    n_outliers: int
    outlier_percentage: float
    explanation: str


def calculate_statistics(data: List[float]) -> Dict[str, float]:
    """Calculate basic statistics"""
    n = len(data)
    mean = sum(data) / n
    variance = sum((x - mean) ** 2 for x in data) / n
    std = math.sqrt(variance)
    
    sorted_data = sorted(data)
    q1_idx = n // 4
    q3_idx = 3 * n // 4
    q1 = sorted_data[q1_idx]
    q3 = sorted_data[q3_idx]
    iqr = q3 - q1
    
    return {
        "mean": mean,
        "std": std,
        "q1": q1,
        "q3": q3,
        "iqr": iqr,
        "min": sorted_data[0],
        "max": sorted_data[-1]
    }


def detect_outliers_zscore(
    data: List[float],
    threshold: float = 3.0
) -> OutlierResult:
    """
    Detect outliers using Z-score method.
    
    Args:
        data: Numeric data
        threshold: Z-score threshold (default 3.0)
        
    Returns:
        OutlierResult
    """
    stats = calculate_statistics(data)
    mean = stats["mean"]
    std = stats["std"]
    
    outlier_indices = []
    scores = []
    
    for i, value in enumerate(data):
        if std > 0:
            z_score = abs((value - mean) / std)
        else:
            z_score = 0.0
        
        scores.append(z_score)
        
        if z_score > threshold:
            outlier_indices.append(i)
    
    outlier_pct = (len(outlier_indices) / len(data)) * 100 if len(data) > 0 else 0
    
    explanation = f"Z-score method with threshold={threshold}. "
    explanation += f"Mean={mean:.3f}, StdDev={std:.3f}. "
    explanation += f"Detected {len(outlier_indices)} outliers ({outlier_pct:.1f}%)."
    
    return OutlierResult(
        indices=outlier_indices,
        scores=scores,
        threshold=threshold,
        method=OutlierMethod.ZSCORE,
        n_outliers=len(outlier_indices),
        outlier_percentage=outlier_pct,
        explanation=explanation
    )


def detect_outliers_iqr(
    data: List[float],
    k: float = 1.5
) -> OutlierResult:
    """
    Detect outliers using IQR method.
    
    Args:
        data: Numeric data
        k: IQR multiplier (default 1.5)
        
    Returns:
        OutlierResult
    """
    stats = calculate_statistics(data)
    q1 = stats["q1"]
    q3 = stats["q3"]
    iqr = stats["iqr"]
    
    lower_bound = q1 - k * iqr
    upper_bound = q3 + k * iqr
    
    outlier_indices = []
    scores = []
    
    for i, value in enumerate(data):
        # Score is distance beyond bounds
        if value < lower_bound:
            score = (lower_bound - value) / iqr if iqr > 0 else 0
        elif value > upper_bound:
            score = (value - upper_bound) / iqr if iqr > 0 else 0
        else:
            score = 0.0
        
        scores.append(score)
        
        if value < lower_bound or value > upper_bound:
            outlier_indices.append(i)
    
    outlier_pct = (len(outlier_indices) / len(data)) * 100 if len(data) > 0 else 0
    
    explanation = f"IQR method with k={k}. "
    explanation += f"Q1={q1:.3f}, Q3={q3:.3f}, IQR={iqr:.3f}. "
    explanation += f"Bounds: [{lower_bound:.3f}, {upper_bound:.3f}]. "
    explanation += f"Detected {len(outlier_indices)} outliers ({outlier_pct:.1f}%)."
    
    return OutlierResult(
        indices=outlier_indices,
        scores=scores,
        threshold=k,
        method=OutlierMethod.IQR,
        n_outliers=len(outlier_indices),
        outlier_percentage=outlier_pct,
        explanation=explanation
    )


def detect_outliers_isolation_forest(
    data: List[float],
    contamination: float = 0.1,
    n_trees: int = 100
) -> OutlierResult:
    """
    Simplified isolation forest for univariate data.
    
    Args:
        data: Numeric data
        contamination: Expected proportion of outliers
        n_trees: Number of trees
        
    Returns:
        OutlierResult
    """
    import random
    
    def isolation_tree_path_length(value: float, data_sample: List[float], depth: int = 0, max_depth: int = 10) -> int:
        """Calculate path length in isolation tree"""
        if depth >= max_depth or len(data_sample) <= 1:
            return depth
        
        # Random split
        min_val = min(data_sample)
        max_val = max(data_sample)
        
        if min_val == max_val:
            return depth
        
        split = random.uniform(min_val, max_val)
        
        left = [x for x in data_sample if x < split]
        right = [x for x in data_sample if x >= split]
        
        if value < split and left:
            return isolation_tree_path_length(value, left, depth + 1, max_depth)
        elif right:
            return isolation_tree_path_length(value, right, depth + 1, max_depth)
        else:
            return depth
    
    # Calculate average path length for each point
    scores = []
    for value in data:
        path_lengths = []
        for _ in range(n_trees):
            # Sample for tree
            sample_size = min(256, len(data))
            sample = random.sample(data, sample_size)
            path_length = isolation_tree_path_length(value, sample)
            path_lengths.append(path_length)
        
        avg_path = sum(path_lengths) / len(path_lengths)
        # Normalize: shorter path = more isolated = higher score
        score = 10.0 / (avg_path + 1)
        scores.append(score)
    
    # Determine threshold based on contamination
    sorted_scores = sorted(scores, reverse=True)
    threshold_idx = int(len(sorted_scores) * contamination)
    threshold = sorted_scores[threshold_idx] if threshold_idx < len(sorted_scores) else 0
    
    outlier_indices = [i for i, score in enumerate(scores) if score >= threshold]
    outlier_pct = (len(outlier_indices) / len(data)) * 100 if len(data) > 0 else 0
    
    explanation = f"Isolation Forest with contamination={contamination}, {n_trees} trees. "
    explanation += f"Detected {len(outlier_indices)} outliers ({outlier_pct:.1f}%)."
    
    return OutlierResult(
        indices=outlier_indices,
        scores=scores,
        threshold=threshold,
        method=OutlierMethod.ISOLATION_FOREST,
        n_outliers=len(outlier_indices),
        outlier_percentage=outlier_pct,
        explanation=explanation
    )


def detect_multivariate_outliers(
    data: List[List[float]],
    method: str = "mahalanobis",
    threshold: float = 3.0
) -> OutlierResult:
    """
    Detect outliers in multivariate data.
    
    Args:
        data: List of feature vectors
        method: Detection method
        threshold: Threshold for outlier detection
        
    Returns:
        OutlierResult
    """
    n_samples = len(data)
    n_features = len(data[0]) if data else 0
    
    # Calculate means
    means = [sum(data[i][j] for i in range(n_samples)) / n_samples 
             for j in range(n_features)]
    
    # Calculate covariance matrix
    cov_matrix = [[0.0 for _ in range(n_features)] for _ in range(n_features)]
    
    for i in range(n_features):
        for j in range(n_features):
            cov = sum((data[k][i] - means[i]) * (data[k][j] - means[j]) 
                     for k in range(n_samples)) / n_samples
            cov_matrix[i][j] = cov
    
    # Simplified Mahalanobis distance (using diagonal only for stability)
    scores = []
    for sample in data:
        distance_sq = 0.0
        for j in range(n_features):
            if cov_matrix[j][j] > 0:
                distance_sq += ((sample[j] - means[j]) ** 2) / cov_matrix[j][j]
        
        score = math.sqrt(distance_sq)
        scores.append(score)
    
    outlier_indices = [i for i, score in enumerate(scores) if score > threshold]
    outlier_pct = (len(outlier_indices) / n_samples) * 100 if n_samples > 0 else 0
    
    explanation = f"Mahalanobis distance with threshold={threshold}. "
    explanation += f"{n_samples} samples, {n_features} features. "
    explanation += f"Detected {len(outlier_indices)} outliers ({outlier_pct:.1f}%)."
    
    return OutlierResult(
        indices=outlier_indices,
        scores=scores,
        threshold=threshold,
        method=OutlierMethod.MAHALANOBIS,
        n_outliers=len(outlier_indices),
        outlier_percentage=outlier_pct,
        explanation=explanation
    )


def compare_outlier_methods(
    data: List[float]
) -> Dict[str, OutlierResult]:
    """
    Compare multiple outlier detection methods.
    
    Args:
        data: Numeric data
        
    Returns:
        Dictionary of method name -> OutlierResult
    """
    results = {}
    
    results["zscore"] = detect_outliers_zscore(data)
    results["iqr"] = detect_outliers_iqr(data)
    results["isolation_forest"] = detect_outliers_isolation_forest(data, contamination=0.05)
    
    return results


def consensus_outliers(
    results: Dict[str, OutlierResult],
    min_methods: int = 2
) -> List[int]:
    """
    Find outliers detected by multiple methods.
    
    Args:
        results: Dictionary of method -> OutlierResult
        min_methods: Minimum number of methods that must agree
        
    Returns:
        List of consensus outlier indices
    """
    # Count how many methods flag each index
    all_indices = set()
    for result in results.values():
        all_indices.update(result.indices)
    
    consensus = []
    for idx in all_indices:
        count = sum(1 for result in results.values() if idx in result.indices)
        if count >= min_methods:
            consensus.append(idx)
    
    return sorted(consensus)
