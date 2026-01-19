"""Ensure src-based modules are importable during tests and CLI usage."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
src_path = PROJECT_ROOT / "src"
src_str = str(src_path)
if src_path.exists() and src_str not in sys.path:
    sys.path.insert(0, src_str)
