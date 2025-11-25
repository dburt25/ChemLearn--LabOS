"""Interface definitions for external ML/API connectors.

These interfaces describe the contracts for integrating external model servers
without prescribing any transport or vendor-specific details. Implementations
must live outside LabOS core modules and rely only on the standard library.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Mapping, MutableMapping, Optional, Sequence


class ModelClientError(RuntimeError):
    """Base exception for model client failures.

    Implementations should raise this error (or subclasses) when requests cannot
    be completed due to recoverable issues such as serialization problems,
    validation errors, or remote service rejections. Fatal misconfiguration
    detected before contacting a service should also surface as this error to
    keep failure handling uniform.
    """


class ModelTimeoutError(ModelClientError):
    """Raised when a model request exceeds the allotted timeout."""


@dataclass(frozen=True)
class ModelPrediction:
    """Normalized response payload from an external model.

    Attributes:
        model_name: Identifier for the remote model or endpoint.
        request_id: Stable token for correlating upstream and downstream logs.
        outputs: Mapping with structured prediction results. Implementations
            should favor JSON-serializable values to enable audit logging.
        raw_response: Optional provider-specific payload preserved for debugging
            or provenance, left untouched by the client interface.
        elapsed_ms: Optional round-trip latency in milliseconds if available.
        metadata: Optional free-form metadata such as provider version, routing
            hints, or input normalization details.
    """

    model_name: str
    request_id: str
    outputs: Mapping[str, Any]
    raw_response: Optional[Any] = None
    elapsed_ms: Optional[float] = None
    metadata: Optional[Mapping[str, Any]] = None


@dataclass(frozen=True)
class SpectrumRequest:
    """Input requirements for spectral predictions.

    Attributes:
        spectrum_type: Type of spectrum to predict (e.g., "MS", "NMR").
        sample_features: Numeric or encoded features representing the sample.
            Implementations should document the required ordering and scaling.
        metadata: Optional auxiliary information such as instrument settings,
            solvent, or ionization mode.
    """

    spectrum_type: str
    sample_features: Sequence[float]
    metadata: Optional[Mapping[str, Any]] = None


@dataclass(frozen=True)
class PropertyRequest:
    """Input requirements for molecular property predictions.

    Attributes:
        representation: Canonical representation of the molecule (e.g., SMILES,
            InChI). Implementations should explicitly state which formats are
            accepted and any normalization steps.
        property_names: Properties requested (e.g., logP, pKa). Empty sequences
            should be rejected at validation time.
        metadata: Optional context such as temperature, pH, or provenance of the
            structure.
    """

    representation: str
    property_names: Sequence[str]
    metadata: Optional[Mapping[str, Any]] = None


class AbstractModelClient(ABC):
    """Minimal interface for interacting with external model services.

    Implementations must be side-effect free beyond network or IPC calls and
    must not mutate caller-owned inputs. To ensure predictable resource usage,
    any cleanup of open connections should be handled in :meth:`close`.
    """

    @abstractmethod
    def predict(
        self,
        *,
        inputs: Mapping[str, Any],
        tags: Optional[MutableMapping[str, str]] = None,
        timeout_s: Optional[float] = None,
    ) -> ModelPrediction:
        """Submit a generic prediction request.

        Args:
            inputs: JSON-serializable payload representing model features.
            tags: Optional mutable mapping for propagation of tracing tokens or
                correlation IDs. Implementations should not remove keys but may
                add transport-specific identifiers.
            timeout_s: Optional wall-clock timeout in seconds for the request.

        Returns:
            ModelPrediction: Normalized prediction artifact suitable for audit
                logging and downstream consumption.

        Raises:
            ModelTimeoutError: If the request exceeds ``timeout_s``.
            ModelClientError: For validation failures, transport errors, or
                provider-side rejections. Concrete implementations should expose
                precise subclasses when available but remain compatible with this
                base type for callers that prefer coarse-grained handling.
        """

    @abstractmethod
    def close(self) -> None:
        """Release any held resources.

        Implementations should close network sessions, file descriptors, or any
        other stateful handles. The method must be idempotent and safe to call
        even if the client failed during initialization.
        """


class ExternalSpectrumPredictor(AbstractModelClient):
    """Interface for external spectrum prediction backends."""

    @abstractmethod
    def predict_spectrum(
        self,
        request: SpectrumRequest,
        *,
        timeout_s: Optional[float] = None,
    ) -> ModelPrediction:
        """Predict a spectrum for the given sample description.

        Args:
            request: Structured :class:`SpectrumRequest` containing the spectrum
                type, encoded sample features, and optional metadata.
            timeout_s: Optional deadline in seconds overriding the client
                default for this call only.

        Returns:
            ModelPrediction: Spectrum intensities or peak lists encoded in the
                ``outputs`` mapping. Implementations should document key names
                (e.g., ``"m_z"``, ``"intensity"``) and units.

        Raises:
            ModelTimeoutError: If ``timeout_s`` is exceeded.
            ModelClientError: For validation, serialization, or provider-side
                failures. The ``raw_response`` field should capture any provider
                diagnostic payload when safe to do so.
        """


class ExternalPropertyPredictor(AbstractModelClient):
    """Interface for external molecular property prediction services."""

    @abstractmethod
    def predict_properties(
        self,
        request: PropertyRequest,
        *,
        timeout_s: Optional[float] = None,
    ) -> ModelPrediction:
        """Predict molecular properties using an external service.

        Args:
            request: Structured :class:`PropertyRequest` specifying the molecular
                representation, requested properties, and optional metadata.
            timeout_s: Optional deadline in seconds overriding the client
                default for this call only.

        Returns:
            ModelPrediction: ``outputs`` should map property names to predicted
                values and units. Implementations should normalize property name
                casing and units before returning to callers.

        Raises:
            ModelTimeoutError: If ``timeout_s`` is exceeded.
            ModelClientError: For invalid inputs, connectivity issues, or
                provider-side errors. Implementations should document which
                errors are retriable versus fatal.
        """
