"""
Model Validation Module

Comprehensive model validation metrics and visualization data
for educational ML (no external dependencies).
"""

from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import math
import random


@dataclass
class ConfusionMatrix:
    """Confusion matrix for classification"""
    true_positives: int
    true_negatives: int
    false_positives: int
    false_negatives: int
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    specificity: float


@dataclass
class ROCPoint:
    """Single point on ROC curve"""
    threshold: float
    true_positive_rate: float  # Sensitivity/Recall
    false_positive_rate: float
    true_negatives: int
    false_positives: int
    true_positives: int
    false_negatives: int


@dataclass
class ROCCurve:
    """ROC curve analysis"""
    points: List[ROCPoint]
    auc: float  # Area Under Curve
    optimal_threshold: float
    optimal_point: ROCPoint
    notes: List[str]


@dataclass
class CrossValidationResult:
    """K-fold cross-validation results"""
    fold_scores: List[float]
    mean_score: float
    std_score: float
    min_score: float
    max_score: float
    n_folds: int
    confidence_interval: Tuple[float, float]
    notes: List[str]


@dataclass
class LearningCurve:
    """Learning curve data"""
    training_sizes: List[int]
    train_scores: List[float]
    validation_scores: List[float]
    train_score_mean: float
    validation_score_mean: float
    convergence_point: Optional[int]  # Size where validation plateaus
    notes: List[str]


@dataclass
class RegressionMetrics:
    """Regression model metrics"""
    mae: float  # Mean Absolute Error
    mse: float  # Mean Squared Error
    rmse: float  # Root Mean Squared Error
    r_squared: float  # R² score
    adjusted_r_squared: float
    residuals: List[float]
    predictions: List[float]
    actuals: List[float]
    notes: List[str]


def calculate_confusion_matrix(
    y_true: List[int],
    y_pred: List[int],
    positive_label: int = 1
) -> ConfusionMatrix:
    """
    Calculate confusion matrix and derived metrics.
    
    Args:
        y_true: True labels (0 or 1)
        y_pred: Predicted labels (0 or 1)
        positive_label: Which label is considered positive
        
    Returns:
        ConfusionMatrix with all metrics
    """
    tp = sum(1 for i in range(len(y_true)) 
             if y_true[i] == positive_label and y_pred[i] == positive_label)
    tn = sum(1 for i in range(len(y_true)) 
             if y_true[i] != positive_label and y_pred[i] != positive_label)
    fp = sum(1 for i in range(len(y_true)) 
             if y_true[i] != positive_label and y_pred[i] == positive_label)
    fn = sum(1 for i in range(len(y_true)) 
             if y_true[i] == positive_label and y_pred[i] != positive_label)
    
    total = len(y_true)
    
    # Accuracy
    accuracy = (tp + tn) / total if total > 0 else 0
    
    # Precision: TP / (TP + FP)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    
    # Recall (Sensitivity, TPR): TP / (TP + FN)
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    
    # F1 Score: 2 * (precision * recall) / (precision + recall)
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    # Specificity (TNR): TN / (TN + FP)
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
    
    return ConfusionMatrix(
        true_positives=tp,
        true_negatives=tn,
        false_positives=fp,
        false_negatives=fn,
        accuracy=accuracy,
        precision=precision,
        recall=recall,
        f1_score=f1,
        specificity=specificity
    )


def calculate_roc_curve(
    y_true: List[int],
    y_scores: List[float],
    positive_label: int = 1,
    n_thresholds: int = 50
) -> ROCCurve:
    """
    Calculate ROC curve points and AUC.
    
    Args:
        y_true: True labels
        y_scores: Predicted probabilities or scores
        positive_label: Which label is positive
        n_thresholds: Number of thresholds to evaluate
        
    Returns:
        ROCCurve with points and AUC
    """
    # Generate thresholds
    min_score = min(y_scores)
    max_score = max(y_scores)
    thresholds = [min_score + (max_score - min_score) * i / (n_thresholds - 1) 
                  for i in range(n_thresholds)]
    thresholds.sort()
    
    points = []
    
    for threshold in thresholds:
        # Convert scores to predictions
        y_pred = [1 if score >= threshold else 0 for score in y_scores]
        
        # Calculate confusion matrix
        cm = calculate_confusion_matrix(y_true, y_pred, positive_label)
        
        # TPR and FPR
        tpr = cm.recall  # Same as TPR
        fpr = 1 - cm.specificity  # FPR = 1 - TNR
        
        points.append(ROCPoint(
            threshold=threshold,
            true_positive_rate=tpr,
            false_positive_rate=fpr,
            true_negatives=cm.true_negatives,
            false_positives=cm.false_positives,
            true_positives=cm.true_positives,
            false_negatives=cm.false_negatives
        ))
    
    # Calculate AUC using trapezoidal rule
    points.sort(key=lambda p: p.false_positive_rate)
    auc = 0.0
    for i in range(len(points) - 1):
        # Trapezoid area
        width = points[i + 1].false_positive_rate - points[i].false_positive_rate
        height = (points[i].true_positive_rate + points[i + 1].true_positive_rate) / 2
        auc += width * height
    
    # Find optimal threshold (closest to top-left corner)
    optimal_point = min(points, key=lambda p: 
                       math.sqrt((1 - p.true_positive_rate)**2 + p.false_positive_rate**2))
    
    notes = [
        f"ROC AUC: {auc:.4f}",
        f"Optimal threshold: {optimal_point.threshold:.4f}",
        f"At optimal: TPR={optimal_point.true_positive_rate:.3f}, FPR={optimal_point.false_positive_rate:.3f}",
        f"Number of thresholds evaluated: {n_thresholds}"
    ]
    
    return ROCCurve(
        points=points,
        auc=auc,
        optimal_threshold=optimal_point.threshold,
        optimal_point=optimal_point,
        notes=notes
    )


def cross_validate(
    X: List[List[float]],
    y: List[float],
    model_train_and_score: callable,
    n_folds: int = 5
) -> CrossValidationResult:
    """
    Perform k-fold cross-validation.
    
    Args:
        X: Feature matrix (list of samples, each sample is list of features)
        y: Target values
        model_train_and_score: Function that takes (X_train, y_train, X_val, y_val) and returns score
        n_folds: Number of folds
        
    Returns:
        CrossValidationResult
    """
    n_samples = len(X)
    fold_size = n_samples // n_folds
    
    # Create indices
    indices = list(range(n_samples))
    random.shuffle(indices)
    
    fold_scores = []
    
    for fold in range(n_folds):
        # Split into train and validation
        val_start = fold * fold_size
        val_end = val_start + fold_size if fold < n_folds - 1 else n_samples
        
        val_indices = indices[val_start:val_end]
        train_indices = indices[:val_start] + indices[val_end:]
        
        X_train = [X[i] for i in train_indices]
        y_train = [y[i] for i in train_indices]
        X_val = [X[i] for i in val_indices]
        y_val = [y[i] for i in val_indices]
        
        # Train and score
        score = model_train_and_score(X_train, y_train, X_val, y_val)
        fold_scores.append(score)
    
    # Calculate statistics
    mean_score = sum(fold_scores) / len(fold_scores)
    variance = sum((s - mean_score) ** 2 for s in fold_scores) / len(fold_scores)
    std_score = math.sqrt(variance)
    
    # 95% confidence interval
    ci_margin = 1.96 * std_score / math.sqrt(n_folds)
    ci = (mean_score - ci_margin, mean_score + ci_margin)
    
    notes = [
        f"{n_folds}-fold cross-validation",
        f"Mean score: {mean_score:.4f} ± {std_score:.4f}",
        f"95% CI: [{ci[0]:.4f}, {ci[1]:.4f}]",
        f"Score range: [{min(fold_scores):.4f}, {max(fold_scores):.4f}]"
    ]
    
    return CrossValidationResult(
        fold_scores=fold_scores,
        mean_score=mean_score,
        std_score=std_score,
        min_score=min(fold_scores),
        max_score=max(fold_scores),
        n_folds=n_folds,
        confidence_interval=ci,
        notes=notes
    )


def generate_learning_curve(
    X: List[List[float]],
    y: List[float],
    model_train_and_score: callable,
    train_sizes: List[int] = None
) -> LearningCurve:
    """
    Generate learning curve data.
    
    Args:
        X: Feature matrix
        y: Target values
        model_train_and_score: Function that takes sizes and returns (train_score, val_score)
        train_sizes: List of training set sizes to evaluate
        
    Returns:
        LearningCurve data
    """
    if train_sizes is None:
        n_samples = len(X)
        train_sizes = [int(n_samples * p) for p in [0.1, 0.2, 0.4, 0.6, 0.8, 1.0]]
    
    train_scores = []
    val_scores = []
    
    for size in train_sizes:
        train_score, val_score = model_train_and_score(X[:size], y[:size])
        train_scores.append(train_score)
        val_scores.append(val_score)
    
    # Find convergence point (where validation score plateaus)
    convergence_point = None
    if len(val_scores) >= 3:
        for i in range(2, len(val_scores)):
            # Check if last 3 validation scores have small variance
            recent_scores = val_scores[i-2:i+1]
            variance = sum((s - sum(recent_scores)/3) ** 2 for s in recent_scores) / 3
            if variance < 0.0001:  # Small variance threshold
                convergence_point = train_sizes[i]
                break
    
    train_mean = sum(train_scores) / len(train_scores)
    val_mean = sum(val_scores) / len(val_scores)
    
    notes = [
        f"Learning curve with {len(train_sizes)} sample sizes",
        f"Training score mean: {train_mean:.4f}",
        f"Validation score mean: {val_mean:.4f}",
    ]
    
    if convergence_point:
        notes.append(f"Converged at ~{convergence_point} samples")
    
    return LearningCurve(
        training_sizes=train_sizes,
        train_scores=train_scores,
        validation_scores=val_scores,
        train_score_mean=train_mean,
        validation_score_mean=val_mean,
        convergence_point=convergence_point,
        notes=notes
    )


def calculate_regression_metrics(
    y_true: List[float],
    y_pred: List[float],
    n_features: int = 1
) -> RegressionMetrics:
    """
    Calculate comprehensive regression metrics.
    
    Args:
        y_true: True values
        y_pred: Predicted values
        n_features: Number of features (for adjusted R²)
        
    Returns:
        RegressionMetrics
    """
    n = len(y_true)
    
    # Residuals
    residuals = [y_true[i] - y_pred[i] for i in range(n)]
    
    # MAE
    mae = sum(abs(r) for r in residuals) / n
    
    # MSE
    mse = sum(r ** 2 for r in residuals) / n
    
    # RMSE
    rmse = math.sqrt(mse)
    
    # R²
    y_mean = sum(y_true) / n
    ss_tot = sum((y - y_mean) ** 2 for y in y_true)
    ss_res = sum(r ** 2 for r in residuals)
    
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
    
    # Adjusted R²
    if n > n_features + 1:
        adj_r_squared = 1 - (1 - r_squared) * (n - 1) / (n - n_features - 1)
    else:
        adj_r_squared = r_squared
    
    notes = [
        f"Number of samples: {n}",
        f"MAE: {mae:.4f}",
        f"RMSE: {rmse:.4f}",
        f"R²: {r_squared:.4f}",
        f"Adjusted R²: {adj_r_squared:.4f}"
    ]
    
    return RegressionMetrics(
        mae=mae,
        mse=mse,
        rmse=rmse,
        r_squared=r_squared,
        adjusted_r_squared=adj_r_squared,
        residuals=residuals,
        predictions=y_pred,
        actuals=y_true,
        notes=notes
    )


def calculate_classification_report(
    y_true: List[int],
    y_pred: List[int],
    class_names: List[str] = None
) -> Dict[str, ConfusionMatrix]:
    """
    Generate classification report for multi-class problems.
    
    Args:
        y_true: True labels
        y_pred: Predicted labels
        class_names: Optional names for classes
        
    Returns:
        Dictionary of class -> ConfusionMatrix (one-vs-rest)
    """
    unique_classes = sorted(set(y_true))
    
    if class_names is None:
        class_names = [f"Class_{c}" for c in unique_classes]
    
    report = {}
    
    for i, class_label in enumerate(unique_classes):
        # Convert to binary problem (one-vs-rest)
        y_true_binary = [1 if y == class_label else 0 for y in y_true]
        y_pred_binary = [1 if y == class_label else 0 for y in y_pred]
        
        cm = calculate_confusion_matrix(y_true_binary, y_pred_binary, positive_label=1)
        report[class_names[i]] = cm
    
    return report
