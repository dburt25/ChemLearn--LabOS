"""ChemLearn LabOS core package.

The package exposes helpers for loading configuration, interacting with
registries, and invoking the CLI entry point. Importing this module does not
perform any I/O so it remains safe for unit tests.
"""

from __future__ import annotations

from importlib.metadata import version, PackageNotFoundError

from .config import LabOSConfig

__all__ = ["LabOSConfig", "get_version"]


def get_version() -> str:
	"""Return the installed LabOS package version for logging purposes."""

	try:
		return version("chemlearn-labos")
	except PackageNotFoundError:  # pragma: no cover - fallback for local runs
		return "0.1.0"
