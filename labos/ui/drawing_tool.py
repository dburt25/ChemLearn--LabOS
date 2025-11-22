"""General-purpose workspace panel for diagrams, notes, and future visual tools."""

from __future__ import annotations

from typing import Any, cast

import streamlit as _streamlit  # type: ignore

st: Any = cast(Any, _streamlit)


def render_drawing_tool(mode: str) -> None:
    """Render a lightweight workspace panel with mode-aware guidance.

    Design intent: keep the surface agnostic so it can host reaction schemes,
    instrument setups, protein docking overlays, or any other scientific sketch
    that needs to attach to Experiments/Jobs/Datasets in later phases.
    """

    st.subheader("Workspace / Drawing")

    if mode == "Learner":
        st.info(
            "Use this space to sketch mechanisms, instrument setups, protein binding pockets, or quick notes "
            "before you commit them to an experiment. A proper drawable canvas will ship in a later update."
        )
    elif mode == "Lab":
        st.caption("Quick scratchpad for run notes or diagrams. Upload figures when you need extra detail.")
    else:  # Builder
        st.caption("Workspace surface for prototype diagrams. Future versions will expose canvas debug info here.")

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
