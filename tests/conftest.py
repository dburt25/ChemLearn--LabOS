"""Pytest configuration helpers for LabOS tests."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the project root (which contains the `labos` package) is always on sys.path.
# CI sometimes invokes pytest from environments that do not automatically include it.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if PROJECT_ROOT.exists():
    root_str = str(PROJECT_ROOT)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
