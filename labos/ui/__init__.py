# labos/ui/__init__.py

"""UI layer for LabOS."""

from __future__ import annotations

from . import control_panel
from .control_panel import render_control_panel
from .provenance_footer import render_method_and_data_footer

__all__ = ["control_panel", "render_control_panel", "render_method_and_data_footer"]

