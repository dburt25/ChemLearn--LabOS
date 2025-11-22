"""Custom exception hierarchy for LabOS."""

from __future__ import annotations


class LabOSError(Exception):
    """Base exception for all LabOS failures."""


class ConfigurationError(LabOSError):
    """Raised when configuration loading fails."""


class RegistryError(LabOSError):
    """Raised when a registry action cannot be fulfilled."""


class NotFoundError(RegistryError):
    """Raised when an entity lookup misses."""


class ValidationError(LabOSError):
    """Raised when input data fails validation."""


class AuditError(LabOSError):
    """Raised for audit log persistence problems."""


class ModuleExecutionError(LabOSError):
    """Raised when a scientific module fails to execute."""
