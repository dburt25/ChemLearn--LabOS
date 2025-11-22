# labos/ui/__init__.py

"""
UI layer for LabOS.

Phase 0:
- A single Streamlit-based Control Panel.
- Three modes: Learner, Lab, Builder (stored in session state).
"""

from .control_panel import render_control_panel

__all__ = ["render_control_panel"]

