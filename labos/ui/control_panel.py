# labos/ui/control_panel.py

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Sequence, cast

import streamlit as _streamlit  # type: ignore

st: Any = cast(Any, _streamlit)

from labos.config import LabOSConfig
from labos.core.errors import NotFoundError
from labos.datasets import Dataset
from labos.experiments import Experiment
from labos.jobs import Job
from labos.modules import ModuleRegistry, get_registry
from labos.runtime import LabOSRuntime


MODES = ["Learner", "Lab", "Builder"]


def _init_session_state() -> None:
    if "mode" not in st.session_state:
        st.session_state.mode = MODES[0]

    if "runtime" not in st.session_state:
        runtime = LabOSRuntime()
        runtime.ensure_initialized()
        st.session_state.runtime = runtime

    if "module_registry" not in st.session_state:
        st.session_state.module_registry = get_registry()

    if "current_section" not in st.session_state:
        st.session_state.current_section = "Overview"


def _load_experiments(runtime: LabOSRuntime) -> list[Experiment]:
    registry = runtime.components.experiments
    experiments: list[Experiment] = []
    try:
        ids = sorted(registry.list_ids(), reverse=True)
    except FileNotFoundError:
        return experiments

    for record_id in ids:
        try:
            experiments.append(registry.get(record_id))
        except (NotFoundError, FileNotFoundError):
            continue
    return experiments


def _load_datasets(runtime: LabOSRuntime) -> list[Dataset]:
    registry = runtime.components.datasets
    datasets: list[Dataset] = []
    try:
        ids = sorted(registry.list_ids(), reverse=True)
    except FileNotFoundError:
        return datasets

    for record_id in ids:
        try:
            datasets.append(registry.get(record_id))
        except (NotFoundError, FileNotFoundError):
            continue
    return datasets


def _load_jobs(config: LabOSConfig) -> list[Job]:
    jobs: list[Job] = []
    jobs_dir: Path = config.jobs_dir
    if not jobs_dir.exists():
        return jobs

    for job_path in sorted(jobs_dir.glob("*.json"), reverse=True):
        try:
            data = json.loads(job_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        try:
            jobs.append(Job(**data))
        except TypeError:
            continue
    return jobs


def _load_audit_events(config: LabOSConfig, limit: int = 20) -> list[dict[str, object]]:
    events: list[dict[str, object]] = []
    audit_dir: Path = config.audit_dir
    if not audit_dir.exists():
        return events

    for log_path in sorted(audit_dir.glob("*.jsonl"), reverse=True):
        try:
            lines = [line for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        except OSError:
            continue
        for line in reversed(lines):
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
            if len(events) >= limit:
                return events
    return events


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


def _render_overview(
    experiments: Sequence[Experiment],
    datasets: Sequence[Dataset],
    jobs: Sequence[Job],
) -> None:
    st.subheader("Overview")

    col1, col2, col3 = st.columns(3)
    col1.metric("Experiments", len(experiments))
    col2.metric("Datasets", len(datasets))
    col3.metric("Jobs", len(jobs))

    st.markdown(
        """
        This page reflects files under your LabOS data directories. Use the CLI or
        upcoming UI actions to add records, then refresh the app to see updates.

        - ✅ Core domain objects: Experiments, Jobs, Datasets, Audit Events
        - ✅ Module registry auto-discovers installed scientific packs
        - ✅ Three working modes: **Learner**, **Lab**, **Builder**
        - ⏳ Future: EI-MS engine, P-Chem calculator, Data Import Wizard, multi-module orchestration
        """
    )

    st.info(
        "Everything you see here is designed to be extended by bots later, "
        "WITHOUT breaking compliance or architecture."
    )


def _render_experiments(experiments: Sequence[Experiment]) -> None:
    st.subheader("Experiments")
    if not experiments:
        st.info("No experiments registered yet.")
        return

    for exp in experiments:
        with st.expander(f"{exp.title} — {exp.record_id}", expanded=False):
            st.json(exp.to_dict())


def _render_jobs(jobs: Sequence[Job]) -> None:
    st.subheader("Jobs")
    if not jobs:
        st.info("No jobs have run yet.")
        return

    for job in jobs:
        label = f"{job.record_id} — {job.status}"
        with st.expander(label, expanded=False):
            st.json(job.to_dict())


def _render_datasets(datasets: Sequence[Dataset]) -> None:
    st.subheader("Datasets")
    if not datasets:
        st.info("No datasets registered yet.")
        return

    for ds in datasets:
        with st.expander(f"{ds.record_id} — {ds.owner}", expanded=False):
            st.json(ds.to_dict())


def _render_modules(registry: ModuleRegistry) -> None:
    st.subheader("Modules & Operations")
    modules = getattr(registry, "_modules", {})

    if not modules:
        st.info(
            "No modules registered. Set LABOS_MODULES or call register_descriptor() from your plugin."
        )
        return

    for descriptor in modules.values():
        header = f"{descriptor.module_id} (v{descriptor.version})"
        with st.expander(header, expanded=False):
            st.write(descriptor.description or "No description provided.")
            if descriptor.operations:
                st.write("**Operations**")
                for op in descriptor.operations.values():
                    st.markdown(f"- `{op.name}` — {op.description}")
            else:
                st.write("_No operations registered._")


def _render_audit_log(events: Sequence[dict[str, object]]) -> None:
    st.subheader("Audit Log")
    if not events:
        st.info("No audit events recorded yet.")
        return

    for event in events:
        header = f"{event.get('event_id', 'unknown')} — {event.get('event_type', 'event')}"
        with st.expander(header, expanded=False):
            st.json(event)


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
    runtime: LabOSRuntime = st.session_state.runtime
    module_registry: ModuleRegistry = st.session_state.module_registry

    experiments = _load_experiments(runtime)
    datasets = _load_datasets(runtime)
    jobs = _load_jobs(runtime.config)
    audit_events = _load_audit_events(runtime.config)

    _render_header()
    _render_sidebar()

    section = st.session_state.get("current_section", "Overview")

    if section == "Overview":
        _render_overview(experiments, datasets, jobs)
    elif section == "Experiments":
        _render_experiments(experiments)
    elif section == "Jobs":
        _render_jobs(jobs)
    elif section == "Datasets":
        _render_datasets(datasets)
    elif section == "Modules":
        _render_modules(module_registry)
    elif section == "Audit Log":
        _render_audit_log(audit_events)

    _render_method_and_data_footer()
