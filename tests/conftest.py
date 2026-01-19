from __future__ import annotations

import sys
from pathlib import Path


SRC_PATH = Path(__file__).resolve().parent.parent / "src"
if SRC_PATH.exists():
    sys.path.insert(0, str(SRC_PATH))
# Ensure the project root (which contains the `labos` package) is always on sys.path.
# CI sometimes invokes pytest from environments that do not automatically include it.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if PROJECT_ROOT.exists():
    root_str = str(PROJECT_ROOT)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)

SRC_ROOT = PROJECT_ROOT / "src"
if SRC_ROOT.exists():
    src_str = str(SRC_ROOT)
    if src_str not in sys.path:
        sys.path.insert(0, src_str)
    src_path = PROJECT_ROOT / "src"
    if src_path.exists():
        src_str = str(src_path)
        if src_str not in sys.path:
            sys.path.insert(0, src_str)
