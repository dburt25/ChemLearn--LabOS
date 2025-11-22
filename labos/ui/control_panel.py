# labos/ui/control_panel.py

from __future__ import annotations

import streamlit as st

from labos.core import (
    Experiment,
    Job,
    DatasetRef,
    AuditEvent,
    ModuleRegistry,
)


MODES = ["Learner", "Lab", "Builder"]


def _init_session_state() -> None:
    if "mode" not in st.session_state:
        st.session_state.mode = "Learner"
    if "registry" not in st.session_state:
        st.session_state.registry = ModuleRegistry.with_phase0_defaults()
    if "experiments" not in st.session_state:
        st.session_state.experiments = [Experiment.example(1, mode=st.session_state.mode)]
    if "jobs" not in st.session_state:
        st.session_state.jobs = [Job.example(1)]
    if "datasets" not in st.session_state:
        st.session_state.datasets = [DatasetRef.example(1)]
    if "audit_events" not in st.session_state:
        st.session_state.audit_events = [AuditEvent.example(1)]


def _render_header() -> None:
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(
            """
            # 🧪 LabOS Control Panel
            
            _ChemLearn LabOS – Phase 0 Skeleton_
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown("#### Mode")
        mode = st.radio(
            "Mode",
            MODES,
            index=MODES.index(st.session_state.mode),
            label_visibility="collapsed",
        )
        st.session_state.mode = mode


def _render_sidebar() -> None:
    st.sidebar.title("Navigation")
    section = st.sidebar.radio(
        "Section",
        ["Overview", "Experiments", "Jobs", "Datasets", "Modules", "Audit Log"],
    )
    st.session_state.current_section = section

    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Current mode:** `{st.session_state.mode}`")
    st.sidebar.markdown("_Phase 0 – skeleton only, not for clinical use._")


def _render_overview() -> None:
    st.subheader("Overview")

    st.markdown(
        """
        This is the **Phase 0** skeleton of ChemLearn LabOS.

        - ✅ Core domain objects: Experiments, Jobs, Datasets, Audit Events
        - ✅ Module registry with provenance metadata
        - ✅ Three modes: **Learner**, **Lab**, **Builder**
        - ✅ Single-page Streamlit Control Panel
        - ⏳ Future: EI-MS engine, P-Chem calculator, Data Import Wizard, multi-module orchestration
        """
    )

    st.info(
        "Everything you see here is designed to be extended by bots later, "
        "WITHOUT breaking compliance or architecture."
    )


def _render_experiments() -> None:
    st.subheader("Experiments")
    exps = st.session_state.experiments

    for exp in exps:
        with st.expander(exp.short_label(), expanded=True):
            st.json(exp.to_dict())


def _render_jobs() -> None:
    st.subheader("Jobs")
    jobs = st.session_state.jobs

    for job in jobs:
        with st.expander(job.id, expanded=True):
            st.json(job.to_dict())


def _render_datasets() -> None:
    st.subheader("Datasets")
    ds_list = st.session_state.datasets

    for ds in ds_list:
        with st.expander(ds.label, expanded=True):
            st.json(ds.to_dict())


def _render_modules() -> None:
    st.subheader("Modules & Methods (Registry)")
    registry: ModuleRegistry = st.session_state.registry

    for meta in registry.all():
        with st.expander(f"{meta.display_name} [{meta.key}]", expanded=False):
            st.write(f"**Method:** {meta.method_name}")
            st.write(f"**Primary Citation:** {meta.primary_citation}")
            if meta.dataset_citations:
                st.write("**Dataset Citations:**")
                for c in meta.dataset_citations:
                    st.write(f"- {c}")
            st.write(f"**Limitations:** {meta.limitations}")


def _render_audit_log() -> None:
    st.subheader("Audit Log (Phase 0 examples)")
    events = st.session_state.audit_events

    for ev in events:
        with st.expander(f"{ev.id} — {ev.action}", expanded=False):
            st.json(ev.to_dict())


def _render_method_and_data_footer() -> None:
    st.markdown("---")
    st.markdown(
        """
        <div style="font-size: 0.85rem; opacity: 0.8;">
        ⓘ <strong>Method &amp; Data</strong> — Phase 0 placeholder.<br/>
        In later phases, this footer will show:
        - Which LabOS module(s) were used
        - Which datasets and versions were involved
        - Validation status and limitations<br/>
        For now, this is just a reminder that <em>every serious result must carry provenance.</em>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_control_panel() -> None:
    """
    Main entrypoint for the LabOS Control Panel UI.
    """
    st.set_page_config(
        page_title="ChemLearn LabOS",
        page_icon="🧪",
        layout="wide",
    )

    _init_session_state()
    _render_header()
    _render_sidebar()

    section = st.session_state.get("current_section", "Overview")

    if section == "Overview":
        _render_overview()
    elif section == "Experiments":
        _render_experiments()
    elif section == "Jobs":
        _render_jobs()
    elif section == "Datasets":
        _render_datasets()
    elif section == "Modules":
        _render_modules()
    elif section == "Audit Log":
        _render_audit_log()

    _render_method_and_data_footer()
