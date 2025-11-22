"""General-purpose workspace panel for diagrams, notes, and future visual tools."""

from __future__ import annotations

from typing import Any, cast

try:  # pragma: no cover - import-time guard
    import streamlit as _streamlit  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - keeps tests runnable without optional dependency
    class _MissingStreamlit:
        def __getattr__(self, name: str) -> "None":
            raise RuntimeError(
                "Streamlit is not installed. Install the 'streamlit' extra or mock 'labos.ui.drawing_tool.st'"
                " before rendering the workspace panel."
            )

    _streamlit = _MissingStreamlit()

st: Any = cast(Any, _streamlit)


def render_drawing_tool(mode: str | None = None, experiment_id: str | None = None) -> None:
    """Render a lightweight workspace panel with mode-aware guidance.

    Design intent: keep the surface agnostic so it can host reaction schemes,
    instrument setups, protein docking overlays, or any other scientific sketch
    that needs to attach to Experiments/Jobs/Datasets in later phases.
    """

    st.subheader("Workspace / Sketchpad")

    mode_message = {
        "Learner": (
            "Use this space to practice sketching mechanisms, instrument setups, protein pockets, or quick notes "
            "before formalizing them into an experiment. A richer canvas is coming, so focus on ideas over polish."
        ),
        "Lab": (
            "Concise scratchpad for run notes or diagrams. Upload figures when you need extra detail—future versions will "
            "keep these alongside your jobs."
        ),
        "Builder": (
            "Prototype sketches here. This panel is the visual front-end for Workspace and upcoming 3D plans so extensions "
            "can track provenance."
        ),
    }

    st.caption(mode_message.get(mode or "", "Drop quick sketches or notes to guide your next steps."))

    note_text = st.text_area(
        "Notes",
        value="",
        placeholder="Describe reaction mechanisms, measurement setups, protein pockets, or TODOs...",
        height=200,
    )

    uploaded_file = st.file_uploader(
        "Optional reference image",
        type=["png", "jpg", "jpeg", "pdf"],
        accept_multiple_files=False,
        help="Upload a sketch or diagram to keep alongside your notes (e.g., spectra, docking snapshots).",
    )

    tagged_experiment = st.text_input(
        "Tag to Experiment ID",
        value=experiment_id or "",
        placeholder="exp-20251122-123000",
        help="Associate this sketch with an Experiment ID so future provenance hooks can attach uploads/notes.",
    )

    st.divider()
    st.markdown(
        "### Workspace capture summary",
    )
    st.markdown(
        "- Notes recorded: {}".format("yes" if note_text.strip() else "none yet")
    )
    st.markdown(
        "- Upload attached: {}".format(uploaded_file.name if uploaded_file else "none yet")
    )
    if tagged_experiment:
        st.success(f"You tagged this sketch to experiment: {tagged_experiment}")
    else:
        st.info("No experiment tag provided yet—enter an Experiment ID to link this workspace to provenance later.")

    st.markdown(
        """
        <div style="font-size: 0.85rem; opacity: 0.7;">
        TODO: Upgrade this panel with an interactive canvas (e.g., streamlit-drawable-canvas) once vetted for Phase 2.
        Future versions will let you overlay 2D annotations onto 3D scenes while keeping experiment tags intact.
        </div>
        """,
        unsafe_allow_html=True,
    )
