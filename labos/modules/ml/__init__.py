"""
Machine Learning Module for LabOS

Explainable, auditable ML for chemistry education and research:
- Feature importance and SHAP analysis
- Model validation and cross-validation
- Property prediction with interpretability
- Drift detection and monitoring
"""

from . import feature_importance, model_validation, prediction_models, drift_detection

__all__ = ["feature_importance", "model_validation", "prediction_models", "drift_detection"]
