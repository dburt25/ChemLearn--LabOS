"""Stub adapter implementations for external predictors.

These classes satisfy the public interfaces without performing any real network
requests. They are placeholders to allow higher-level code to depend on stable
shapes while external integrations are developed in future phases.
"""

from __future__ import annotations

from typing import Any, Mapping, MutableMapping, Optional

from .interfaces import (
    ExternalPropertyPredictor,
    ExternalSpectrumPredictor,
    ModelPrediction,
    PropertyRequest,
    SpectrumRequest,
)


_NOT_IMPLEMENTED_MESSAGE = "External integration not implemented in Phase 2.5.3."


class DummySpectrumPredictor(ExternalSpectrumPredictor):
    """Stub spectrum predictor that signals missing integration."""

    def predict(
        self,
        *,
        inputs: Mapping[str, Any],
        tags: Optional[MutableMapping[str, str]] = None,
        timeout_s: Optional[float] = None,
    ) -> ModelPrediction:
        raise NotImplementedError(_NOT_IMPLEMENTED_MESSAGE)

    def predict_spectrum(
        self,
        request: SpectrumRequest,
        *,
        timeout_s: Optional[float] = None,
    ) -> ModelPrediction:
        raise NotImplementedError(_NOT_IMPLEMENTED_MESSAGE)

    def close(self) -> None:
        raise NotImplementedError(_NOT_IMPLEMENTED_MESSAGE)


class DummyPropertyPredictor(ExternalPropertyPredictor):
    """Stub property predictor that signals missing integration."""

    def predict(
        self,
        *,
        inputs: Mapping[str, Any],
        tags: Optional[MutableMapping[str, str]] = None,
        timeout_s: Optional[float] = None,
    ) -> ModelPrediction:
        raise NotImplementedError(_NOT_IMPLEMENTED_MESSAGE)

    def predict_properties(
        self,
        request: PropertyRequest,
        *,
        timeout_s: Optional[float] = None,
    ) -> ModelPrediction:
        raise NotImplementedError(_NOT_IMPLEMENTED_MESSAGE)

    def close(self) -> None:
        raise NotImplementedError(_NOT_IMPLEMENTED_MESSAGE)


def get_default_spectrum_predictor() -> ExternalSpectrumPredictor:
    """Return a stub spectrum predictor for environments without integrations."""

    return DummySpectrumPredictor()


def get_default_property_predictor() -> ExternalPropertyPredictor:
    """Return a stub property predictor for environments without integrations."""

    return DummyPropertyPredictor()
