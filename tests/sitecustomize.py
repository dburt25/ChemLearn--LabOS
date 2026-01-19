"""Ensure LabOS sources remain importable regardless of current working directory."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
root_str = str(PROJECT_ROOT)
if root_str not in sys.path:
    sys.path.insert(0, root_str)

SRC_ROOT = PROJECT_ROOT / "src"
src_str = str(SRC_ROOT)
if SRC_ROOT.exists() and src_str not in sys.path:
    sys.path.insert(0, src_str)
