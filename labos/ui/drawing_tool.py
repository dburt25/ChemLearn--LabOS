"""General-purpose workspace panel for diagrams, notes, and future visual tools."""

from __future__ import annotations

from typing import Any, cast

import streamlit as _streamlit  # type: ignore

st: Any = cast(Any, _streamlit)


def render_drawing_tool(mode: str | None = None) -> None:
    """Render a lightweight workspace panel with mode-aware guidance.

    Design intent: keep the surface agnostic so it can host reaction schemes,
    instrument setups, protein docking overlays, or any other scientific sketch
    that needs to attach to Experiments/Jobs/Datasets in later phases.
    """

    st.subheader("Workspace / Sketchpad")

    mode_message = {
        "Learner": (
            "Use this space to practice sketching mechanisms, instrument setups, binding sites, or quick notes "
            "before formalizing them into an experiment. A richer canvas is coming, so focus on ideas over polish."
        ),
        "Lab": (
            "Concise scratchpad for run notes or diagrams. Upload figures when you need extra detail—future versions will "
            "keep these alongside your jobs."
        ),
        "Builder": (
            "Prototype sketches here. This surface will later link diagrams to Experiments/Jobs so extensions can track "
            "provenance."
        ),
    }

    st.caption(mode_message.get(mode or "", "Drop quick sketches or notes to guide your next steps."))

    st.text_area(
        "Notes",
        value="",
        placeholder="Describe reaction mechanisms, measurement setups, or TODOs...",
        height=200,
    )

    st.file_uploader(
        "Optional reference image",
        type=["png", "jpg", "jpeg", "pdf"],
        accept_multiple_files=False,
        help="Upload a sketch or diagram to keep alongside your notes.",
    )

    st.markdown(
        """
        <div style="font-size: 0.85rem; opacity: 0.7;">
        TODO: Upgrade this panel with an interactive canvas (e.g., streamlit-drawable-canvas) once vetted for Phase 2.
        </div>
        """,
        unsafe_allow_html=True,
    )
