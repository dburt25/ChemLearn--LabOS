"""Public interfaces for external API and model integrations.

This package intentionally contains only abstract interfaces and shared data
structures. Concrete connectors should live in separate modules that depend on
vendor SDKs or HTTP clients while conforming to the contracts defined here.
"""

from .interfaces import (
    AbstractModelClient,
    ExternalPropertyPredictor,
    ExternalSpectrumPredictor,
    ModelClientError,
    ModelPrediction,
    ModelTimeoutError,
    PropertyRequest,
    SpectrumRequest,
)

__all__ = [
    "AbstractModelClient",
    "ExternalPropertyPredictor",
    "ExternalSpectrumPredictor",
    "ModelClientError",
    "ModelPrediction",
    "ModelTimeoutError",
    "PropertyRequest",
    "SpectrumRequest",
]
