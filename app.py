# app.py

"""
Top-level entrypoint for LabOS Phase 0.

Run with:
    streamlit run app.py
"""

from labos.ui import render_control_panel


def main() -> None:
    """Entry point invoked by both Streamlit and direct Python runs."""

    render_control_panel()


# Streamlit executes this script with a custom module name, so we call main() eagerly
# to ensure widgets render whether the script is run via `streamlit run` or plain Python.
main()
