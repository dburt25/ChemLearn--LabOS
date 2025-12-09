"""
Prediction Models Module

Educational ML models for chemistry property prediction.
Pure Python implementations for transparency and interpretability.
"""

from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import math


@dataclass
class LinearRegressionModel:
    """Simple linear regression model"""
    coefficients: List[float]
    intercept: float
    feature_names: List[str]
    r_squared: float
    trained_samples: int


@dataclass
class KNNModel:
    """K-Nearest Neighbors model"""
    X_train: List[List[float]]
    y_train: List[float]
    k: int
    metric: str  # 'euclidean' or 'manhattan'
    feature_names: List[str]


@dataclass
class DecisionRule:
    """Single decision rule"""
    feature_idx: int
    feature_name: str
    threshold: float
    left_value: float
    right_value: float
    operator: str  # '<=' or '>'


@dataclass
class DecisionTreeModel:
    """Simple decision tree for regression"""
    rules: List[DecisionRule]
    feature_names: List[str]
    max_depth: int
    min_samples_split: int


@dataclass
class PredictionResult:
    """Prediction with explanation"""
    prediction: float
    confidence: float
    explanation: str
    feature_contributions: Dict[str, float]
    similar_examples: List[Tuple[List[float], float]]  # For KNN


def train_linear_regression(
    X: List[List[float]],
    y: List[float],
    feature_names: List[str] = None
) -> LinearRegressionModel:
    """
    Train linear regression using ordinary least squares.
    
    β = (X^T X)^(-1) X^T y
    
    Args:
        X: Feature matrix
        y: Target values
        feature_names: Optional feature names
        
    Returns:
        Trained LinearRegressionModel
    """
    n_samples = len(X)
    n_features = len(X[0])
    
    if feature_names is None:
        feature_names = [f"feature_{i}" for i in range(n_features)]
    
    # Add intercept column
    X_with_intercept = [[1.0] + row for row in X]
    
    # Calculate X^T X
    XTX = [[0.0 for _ in range(n_features + 1)] for _ in range(n_features + 1)]
    for i in range(n_features + 1):
        for j in range(n_features + 1):
            for row in X_with_intercept:
                XTX[i][j] += row[i] * row[j]
    
    # Calculate X^T y
    XTy = [0.0 for _ in range(n_features + 1)]
    for i in range(n_features + 1):
        for k in range(n_samples):
            XTy[i] += X_with_intercept[k][i] * y[k]
    
    # Solve using Gaussian elimination (simplified for small systems)
    coefficients = solve_linear_system(XTX, XTy)
    
    intercept = coefficients[0]
    feature_coeffs = coefficients[1:]
    
    # Calculate R²
    y_pred = [predict_linear(X[i], feature_coeffs, intercept) for i in range(n_samples)]
    y_mean = sum(y) / n_samples
    ss_tot = sum((yi - y_mean) ** 2 for yi in y)
    ss_res = sum((y[i] - y_pred[i]) ** 2 for i in range(n_samples))
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
    
    return LinearRegressionModel(
        coefficients=feature_coeffs,
        intercept=intercept,
        feature_names=feature_names,
        r_squared=r_squared,
        trained_samples=n_samples
    )


def predict_linear(
    x: List[float],
    coefficients: List[float],
    intercept: float
) -> float:
    """Make prediction with linear model"""
    return intercept + sum(x[i] * coefficients[i] for i in range(len(x)))


def solve_linear_system(A: List[List[float]], b: List[float]) -> List[float]:
    """
    Solve Ax = b using Gaussian elimination.
    Simplified for small systems.
    """
    n = len(b)
    
    # Create augmented matrix
    aug = [A[i] + [b[i]] for i in range(n)]
    
    # Forward elimination
    for i in range(n):
        # Find pivot
        max_row = i
        for k in range(i + 1, n):
            if abs(aug[k][i]) > abs(aug[max_row][i]):
                max_row = k
        aug[i], aug[max_row] = aug[max_row], aug[i]
        
        # Make all rows below this one 0 in current column
        for k in range(i + 1, n):
            if aug[i][i] != 0:
                c = aug[k][i] / aug[i][i]
                for j in range(i, n + 1):
                    aug[k][j] -= c * aug[i][j]
    
    # Back substitution
    x = [0.0 for _ in range(n)]
    for i in range(n - 1, -1, -1):
        if aug[i][i] != 0:
            x[i] = aug[i][n]
            for j in range(i + 1, n):
                x[i] -= aug[i][j] * x[j]
            x[i] /= aug[i][i]
    
    return x


def train_knn(
    X: List[List[float]],
    y: List[float],
    k: int = 5,
    metric: str = 'euclidean',
    feature_names: List[str] = None
) -> KNNModel:
    """
    Train K-Nearest Neighbors (just stores training data).
    
    Args:
        X: Feature matrix
        y: Target values
        k: Number of neighbors
        metric: Distance metric
        feature_names: Optional feature names
        
    Returns:
        Trained KNNModel
    """
    if feature_names is None:
        feature_names = [f"feature_{i}" for i in range(len(X[0]))]
    
    return KNNModel(
        X_train=X,
        y_train=y,
        k=k,
        metric=metric,
        feature_names=feature_names
    )


def predict_knn(
    model: KNNModel,
    x: List[float]
) -> PredictionResult:
    """
    Predict using KNN with explanation.
    
    Args:
        model: Trained KNN model
        x: Feature vector
        
    Returns:
        PredictionResult with similar examples
    """
    # Calculate distances
    distances = []
    for i, x_train in enumerate(model.X_train):
        if model.metric == 'euclidean':
            dist = math.sqrt(sum((x[j] - x_train[j]) ** 2 for j in range(len(x))))
        else:  # manhattan
            dist = sum(abs(x[j] - x_train[j]) for j in range(len(x)))
        distances.append((dist, i))
    
    # Get k nearest
    distances.sort()
    k_nearest = distances[:model.k]
    
    # Average their target values
    prediction = sum(model.y_train[idx] for _, idx in k_nearest) / model.k
    
    # Confidence based on distance variance
    nearest_dists = [d for d, _ in k_nearest]
    avg_dist = sum(nearest_dists) / len(nearest_dists)
    confidence = 1.0 / (1.0 + avg_dist)  # Inverse distance
    
    # Get similar examples
    similar_examples = [(model.X_train[idx], model.y_train[idx]) for _, idx in k_nearest]
    
    # Explanation
    explanation = f"Prediction based on {model.k} nearest neighbors. "
    explanation += f"Average distance: {avg_dist:.3f}. "
    explanation += f"Neighbor values: {[model.y_train[idx] for _, idx in k_nearest]}"
    
    # Feature contributions (based on average feature differences)
    feature_contributions = {}
    for j, fname in enumerate(model.feature_names):
        avg_neighbor_feature = sum(model.X_train[idx][j] for _, idx in k_nearest) / model.k
        contribution = abs(x[j] - avg_neighbor_feature)
        feature_contributions[fname] = contribution
    
    return PredictionResult(
        prediction=prediction,
        confidence=confidence,
        explanation=explanation,
        feature_contributions=feature_contributions,
        similar_examples=similar_examples
    )


def train_decision_tree(
    X: List[List[float]],
    y: List[float],
    feature_names: List[str] = None,
    max_depth: int = 3,
    min_samples_split: int = 10
) -> DecisionTreeModel:
    """
    Train simple decision tree for regression.
    
    Args:
        X: Feature matrix
        y: Target values
        feature_names: Optional feature names
        max_depth: Maximum tree depth
        min_samples_split: Minimum samples to split
        
    Returns:
        Trained DecisionTreeModel
    """
    if feature_names is None:
        feature_names = [f"feature_{i}" for i in range(len(X[0]))]
    
    rules = []
    
    # Recursive tree building (simplified)
    def build_tree(X_subset, y_subset, depth):
        if depth >= max_depth or len(X_subset) < min_samples_split:
            return
        
        # Find best split
        best_feature = 0
        best_threshold = 0.0
        best_mse = float('inf')
        
        for feat_idx in range(len(X_subset[0])):
            # Get unique values for this feature
            values = sorted(set(x[feat_idx] for x in X_subset))
            
            for i in range(len(values) - 1):
                threshold = (values[i] + values[i + 1]) / 2
                
                # Split data
                left_y = [y_subset[j] for j in range(len(X_subset)) 
                         if X_subset[j][feat_idx] <= threshold]
                right_y = [y_subset[j] for j in range(len(X_subset)) 
                          if X_subset[j][feat_idx] > threshold]
                
                if len(left_y) == 0 or len(right_y) == 0:
                    continue
                
                # Calculate MSE
                left_mean = sum(left_y) / len(left_y)
                right_mean = sum(right_y) / len(right_y)
                mse = sum((y - left_mean) ** 2 for y in left_y) + \
                      sum((y - right_mean) ** 2 for y in right_y)
                
                if mse < best_mse:
                    best_mse = mse
                    best_feature = feat_idx
                    best_threshold = threshold
        
        # Create rule
        left_y = [y_subset[j] for j in range(len(X_subset)) 
                 if X_subset[j][best_feature] <= best_threshold]
        right_y = [y_subset[j] for j in range(len(X_subset)) 
                  if X_subset[j][best_feature] > best_threshold]
        
        if len(left_y) > 0 and len(right_y) > 0:
            rule = DecisionRule(
                feature_idx=best_feature,
                feature_name=feature_names[best_feature],
                threshold=best_threshold,
                left_value=sum(left_y) / len(left_y),
                right_value=sum(right_y) / len(right_y),
                operator='<='
            )
            rules.append(rule)
    
    build_tree(X, y, 0)
    
    return DecisionTreeModel(
        rules=rules,
        feature_names=feature_names,
        max_depth=max_depth,
        min_samples_split=min_samples_split
    )


def predict_decision_tree(
    model: DecisionTreeModel,
    x: List[float]
) -> PredictionResult:
    """
    Predict using decision tree with explanation.
    
    Args:
        model: Trained decision tree
        x: Feature vector
        
    Returns:
        PredictionResult with rule path
    """
    # Apply rules in sequence
    prediction = 0.0
    applied_rules = []
    
    for rule in model.rules:
        value = x[rule.feature_idx]
        
        if value <= rule.threshold:
            prediction = rule.left_value
            applied_rules.append(f"{rule.feature_name} <= {rule.threshold:.3f}")
        else:
            prediction = rule.right_value
            applied_rules.append(f"{rule.feature_name} > {rule.threshold:.3f}")
    
    # If no rules, use mean
    if len(model.rules) == 0:
        prediction = 0.0
    
    explanation = "Decision path: " + " AND ".join(applied_rules) if applied_rules else "No rules applied"
    
    # Feature contributions based on which rules fired
    feature_contributions = {}
    for rule in model.rules:
        fname = rule.feature_name
        if fname not in feature_contributions:
            feature_contributions[fname] = 1.0
    
    confidence = 0.8 if applied_rules else 0.5
    
    return PredictionResult(
        prediction=prediction,
        confidence=confidence,
        explanation=explanation,
        feature_contributions=feature_contributions,
        similar_examples=[]
    )


def predict_with_linear_regression(
    model: LinearRegressionModel,
    x: List[float]
) -> PredictionResult:
    """
    Predict using linear regression with explanation.
    
    Args:
        model: Trained linear regression model
        x: Feature vector
        
    Returns:
        PredictionResult with feature contributions
    """
    prediction = predict_linear(x, model.coefficients, model.intercept)
    
    # Feature contributions are just coefficient * value
    feature_contributions = {
        model.feature_names[i]: abs(model.coefficients[i] * x[i])
        for i in range(len(x))
    }
    
    # Explanation
    explanation = f"Linear combination: {model.intercept:.3f} (intercept)"
    for i, fname in enumerate(model.feature_names):
        explanation += f" + {model.coefficients[i]:.3f} * {fname}"
    
    confidence = model.r_squared  # Use R² as confidence proxy
    
    return PredictionResult(
        prediction=prediction,
        confidence=confidence,
        explanation=explanation,
        feature_contributions=feature_contributions,
        similar_examples=[]
    )


def normalize_features(X: List[List[float]]) -> Tuple[List[List[float]], List[float], List[float]]:
    """
    Normalize features to zero mean and unit variance.
    
    Returns:
        (X_normalized, means, stds)
    """
    n_features = len(X[0])
    
    # Calculate means
    means = [sum(row[j] for row in X) / len(X) for j in range(n_features)]
    
    # Calculate stds
    stds = []
    for j in range(n_features):
        variance = sum((row[j] - means[j]) ** 2 for row in X) / len(X)
        stds.append(math.sqrt(variance))
    
    # Normalize
    X_norm = []
    for row in X:
        norm_row = [(row[j] - means[j]) / stds[j] if stds[j] > 0 else 0.0 
                    for j in range(n_features)]
        X_norm.append(norm_row)
    
    return X_norm, means, stds


def apply_normalization(
    x: List[float],
    means: List[float],
    stds: List[float]
) -> List[float]:
    """Apply learned normalization to new sample"""
    return [(x[i] - means[i]) / stds[i] if stds[i] > 0 else 0.0 
            for i in range(len(x))]
