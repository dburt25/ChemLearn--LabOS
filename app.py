# app.py

"""
Top-level entrypoint for LabOS Phase 0.

Run with:
    streamlit run app.py
"""

from labos.ui import render_control_panel


def main() -> None:
    render_control_panel()


if __name__ == "__main__":
    main()
