"""Command-line interface entrypoints for LabOS.

Phase 2 introduces an educational, low-risk CLI that surfaces
module metadata and demo experiment/job flows without persistence.
"""

from .main import main

__all__ = ["main"]
