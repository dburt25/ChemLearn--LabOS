# labos/ui/control_panel.py

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence, cast

import streamlit as _streamlit  # type: ignore

st: Any = cast(Any, _streamlit)

from labos.config import LabOSConfig
from labos.core.errors import NotFoundError
from labos.datasets import Dataset
from labos.experiments import Experiment
from labos.jobs import Job
from labos.modules import ModuleDescriptor, ModuleRegistry, get_registry
from labos.runtime import LabOSRuntime


MODES = ["Learner", "Lab", "Builder"]

MODE_PROFILES: dict[str, dict[str, object]] = {
    "Learner": {
        "tagline": "Guided explanations and safety rails for new operators.",
        "callout": "info",
        "message": "Learner mode explains what each panel does so you can practice without touching production data. Currently tracking {experiments} experiments, {datasets} datasets, and {jobs} jobs.",
        "what_is_this": "Use Learner mode when you want contextual help and inline definitions. All controls stay read-only until you explicitly promote a draft via the CLI.",
        "tips": {
            "overview": "Learner mode surfaces the why behind every metric. Hover on the help icons to read more.",
            "experiments": "Use the inspector below to peek at experiment metadata without editing files.",
            "jobs": "Learner mode highlights job status codes so you can follow execution stories.",
            "datasets": "Review dataset owners and URIs to understand provenance before running analyses.",
            "modules": "Module Inspector gives you safe read-only access to descriptors and operations.",
        },
    },
    "Lab": {
        "tagline": "Minimal UI optimized for day-to-day lab execution.",
        "callout": "success",
        "message": "Lab mode keeps noise low so you can focus on running the latest {jobs} jobs against {experiments} experiments.",
        "what_is_this": "Operators choose Lab mode when they already know the workflow. The UI trims help text but keeps compliance reminders visible.",
        "tips": {
            "overview": "Lab mode shows only actionable KPIs—everything else is tucked away for speed.",
            "experiments": "Pick an experiment and jump straight to its JSON payload for rapid validation.",
            "jobs": "Statuses update live; refresh after running a CLI task to see new records.",
            "datasets": "Datasets are grouped by owner so you can coordinate with data stewards quickly.",
            "modules": "Use Module Inspector to confirm the operation name before running CLI jobs.",
        },
    },
    "Builder": {
        "tagline": "Debugging surface for module and UI developers.",
        "callout": "warning",
        "message": "Builder mode exposes registry internals so you can verify modules ({modules_count}) and upcoming jobs ({jobs}).",
        "what_is_this": "Choose Builder when extending LabOS. Expect verbose metadata, JSON dumps, and quick links to descriptors.",
        "tips": {
            "overview": "Builder mode highlights gaps between registry metadata and stored files.",
            "experiments": "Double-check tags, status enums, and timestamps before writing migrations.",
            "jobs": "Inspect logs/results to confirm module contract changes.",
            "datasets": "Metadata column shows whatever your ingestion scripts recorded—use it to spot schema drift.",
            "modules": "Module Inspector exposes every registered operation so you can test them live.",
        },
    },
}


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


def _generate_experiment_id() -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return f"exp-{timestamp}"


def _mode_tip(section: str) -> str:
    profile = MODE_PROFILES.get(st.session_state.mode, MODE_PROFILES[MODES[0]])
    fallback = MODE_PROFILES[MODES[0]]
    tips = cast(dict[str, str], profile.get("tips", {}))
    fallback_tips = cast(dict[str, str], fallback.get("tips", {}))
    tip = tips.get(section)
    if tip:
        return tip
    return fallback_tips.get(section, "")


def _render_mode_banner(
    experiments: Sequence[Experiment],
    datasets: Sequence[Dataset],
    jobs: Sequence[Job],
    registry: ModuleRegistry,
) -> None:
    profile = MODE_PROFILES.get(st.session_state.mode, MODE_PROFILES[MODES[0]])
    callout_name = str(profile.get("callout", "info"))
    callout = getattr(st, callout_name, st.info)
    modules: dict[str, ModuleDescriptor] = cast(dict[str, ModuleDescriptor], getattr(registry, "_modules", {}))
    modules_count = len(modules)
    message_template = str(profile.get("message", ""))
    message = message_template.format(
        experiments=len(experiments),
        datasets=len(datasets),
        jobs=len(jobs),
        modules_count=modules_count,
    )
    callout(message)
    what_is_this = profile.get("what_is_this")
    if what_is_this:
        expanded = st.session_state.mode == "Learner"
        with st.expander("What is this mode?", expanded=expanded):
            st.markdown(str(what_is_this))


def _render_create_experiment_form() -> None:
    st.sidebar.subheader("Create Experiment")
    draft_id = st.session_state.get("draft_experiment_id")
    if not draft_id:
        draft_id = _generate_experiment_id()
        st.session_state.draft_experiment_id = draft_id

    submitted = False
    with st.sidebar.form("create_experiment_form", clear_on_submit=False):
        experiment_id = st.text_input(
            "Experiment ID",
            value=draft_id,
            help="Auto-generated IDs follow the exp-YYYYMMDD-HHMMSS pattern.",
        )
        name = st.text_input(
            "Experiment Name",
            placeholder="e.g. EI-MS tuning sweep",
            help="Provide a descriptive label so teammates can recognize the draft soon.",
        )
        mode_choice = st.selectbox(
            "Mode Context",
            options=MODES,
            index=MODES.index(st.session_state.mode),
            help="Choose the context you plan to run this experiment in.",
        )
        submitted = st.form_submit_button("Stage Experiment", use_container_width=True)

    if submitted:
        if not name.strip():
            st.sidebar.warning("Name is required before staging the experiment.")
            return
        staged: dict[str, str] = {
            "record_id": experiment_id or draft_id,
            "title": name.strip(),
            "mode": mode_choice,
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        st.session_state.last_created_experiment = staged
        st.session_state.draft_experiment_id = _generate_experiment_id()
        st.session_state.mode = mode_choice
        st.sidebar.success("Experiment draft captured. Persist it via the CLI or API when ready.")
        st.sidebar.json(staged)


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
    profile = MODE_PROFILES.get(st.session_state.mode, MODE_PROFILES[MODES[0]])
    with col1:
        st.markdown(
            """
            # 🧪 LabOS Control Panel
            
            _ChemLearn LabOS – Phase 0 Skeleton_
            """,
            unsafe_allow_html=True,
        )
        tagline = str(profile.get("tagline", ""))
        if tagline:
            st.caption(tagline)
    with col2:
        st.markdown("#### Mode")
        mode = st.radio(
            "Mode",
            MODES,
            index=MODES.index(st.session_state.mode),
            label_visibility="collapsed",
            help="Switch perspectives to reveal learner notes, lab-focused metrics, or builder diagnostics.",
        )
        st.session_state.mode = mode


def _render_sidebar() -> None:
    st.sidebar.title("Navigation")
    section = st.sidebar.radio(
        "Section",
        ["Overview", "Experiments", "Jobs", "Datasets", "Modules", "Audit Log"],
        help="Choose which resource set to inspect. Mode-aware tips adjust automatically.",
    )
    st.session_state.current_section = section

    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Current mode:** `{st.session_state.mode}`")
    st.sidebar.markdown("_Phase 0 – skeleton only, not for clinical use._")
    _render_create_experiment_form()


def _render_overview(
    experiments: Sequence[Experiment],
    datasets: Sequence[Dataset],
    jobs: Sequence[Job],
    registry: ModuleRegistry,
) -> None:
    st.subheader("Overview")
    tip = _mode_tip("overview")
    if tip:
        st.caption(tip)

    col1, col2, col3 = st.columns(3)
    col1.metric("Experiments", len(experiments), help="Count of experiment JSON records on disk.")
    col2.metric("Datasets", len(datasets), help="Datasets discovered in the configured storage path.")
    col3.metric("Jobs", len(jobs), help="Latest job manifests found under jobs_dir.")

    st.markdown("---")
    exp_col, module_col = st.columns([2, 1], gap="large")
    with exp_col:
        st.markdown("#### Experiments at a glance")
        if experiments:
            exp_rows = [
                {
                    "Title": exp.title,
                    "ID": exp.record_id,
                    "Status": exp.status.value,
                    "Updated": exp.updated_at,
                }
                for exp in experiments[:5]
            ]
            st.dataframe(exp_rows, use_container_width=True)
            st.caption("Showing the five most recent experiments.")
        else:
            st.info("No experiments registered yet. Use the sidebar flow or CLI to add one.")
    with module_col:
        st.markdown("#### Modules summary")
        modules = cast(dict[str, ModuleDescriptor], getattr(registry, "_modules", {}))
        if modules:
            module_rows: list[dict[str, object]] = []
            for descriptor in list(modules.values())[:5]:
                module_rows.append(
                    {
                        "Module": descriptor.module_id,
                        "Version": descriptor.version,
                        "Ops": len(descriptor.operations),
                    }
                )
            st.dataframe(module_rows, use_container_width=True)
            st.caption("Need more detail? Open the Module Inspector page.")
        else:
            st.warning("No modules registered. Set LABOS_MODULES to auto-discover packs.")

    st.markdown("---")
    jobs_col, datasets_col = st.columns(2, gap="large")
    with jobs_col:
        st.markdown("#### Jobs snapshot")
        if jobs:
            job_rows = [
                {
                    "Job": job.record_id,
                    "Status": job.status.value,
                    "Experiment": job.experiment_id,
                }
                for job in jobs[:5]
            ]
            st.dataframe(job_rows, use_container_width=True)
        else:
            st.info("No jobs have run yet.")
    with datasets_col:
        st.markdown("#### Datasets snapshot")
        if datasets:
            dataset_rows = [
                {
                    "Dataset": ds.record_id,
                    "Owner": ds.owner,
                    "Type": ds.dataset_type.value,
                }
                for ds in datasets[:5]
            ]
            st.dataframe(dataset_rows, use_container_width=True)
        else:
            st.info("No datasets registered yet.")

    st.success(
        "Everything you see here is designed to be extended by bots later without breaking compliance or architecture."
    )


def _render_experiments(experiments: Sequence[Experiment]) -> None:
    st.subheader("Experiments")
    if not experiments:
        st.info("No experiments registered yet.")
        return

    tip = _mode_tip("experiments")
    if tip:
        st.caption(tip)

    summary = [
        {
            "Title": exp.title,
            "Status": exp.status.value,
            "ID": exp.record_id,
            "Owner": exp.user_id,
            "Updated": exp.updated_at,
        }
        for exp in experiments
    ]
    st.dataframe(summary, use_container_width=True)

    record_ids = [exp.record_id for exp in experiments]
    selected_id = st.selectbox(
        "Inspect experiment",
        options=record_ids,
        help="Choose a record to view its full JSON payload.",
    )
    if selected_id:
        selected_exp = next((exp for exp in experiments if exp.record_id == selected_id), None)
        if selected_exp:
            with st.expander(f"Details — {selected_exp.title}", expanded=False):
                st.json(selected_exp.to_dict())


def _render_jobs(jobs: Sequence[Job]) -> None:
    st.subheader("Jobs")
    if not jobs:
        st.info("No jobs have run yet.")
        return

    tip = _mode_tip("jobs")
    if tip:
        st.caption(tip)

    job_rows = [
        {
            "Job": job.record_id,
            "Status": job.status.value,
            "Module": job.module_id,
            "Operation": job.operation,
            "Experiment": job.experiment_id,
            "Updated": job.updated_at,
        }
        for job in jobs
    ]
    st.dataframe(job_rows, use_container_width=True)

    selected_job = st.selectbox(
        "Inspect job",
        options=[row["Job"] for row in job_rows],
        help="Opens the stored JSON manifest for deeper debugging.",
    )
    if selected_job:
        job_map = {job.record_id: job for job in jobs}
        job_obj = job_map.get(selected_job)
        if job_obj:
            with st.expander(f"Details — {selected_job}", expanded=False):
                st.json(job_obj.to_dict())


def _render_datasets(datasets: Sequence[Dataset]) -> None:
    st.subheader("Datasets")
    if not datasets:
        st.info("No datasets registered yet.")
        return

    tip = _mode_tip("datasets")
    if tip:
        st.caption(tip)

    dataset_rows = [
        {
            "Dataset": ds.record_id,
            "Owner": ds.owner,
            "Type": ds.dataset_type.value,
            "URI": ds.uri,
            "Updated": ds.updated_at,
        }
        for ds in datasets
    ]
    st.dataframe(dataset_rows, use_container_width=True)

    selected_dataset = st.selectbox(
        "Inspect dataset",
        options=[row["Dataset"] for row in dataset_rows],
        help="Reveal metadata captured at ingestion time.",
    )
    if selected_dataset:
        dataset_map = {ds.record_id: ds for ds in datasets}
        ds_obj = dataset_map.get(selected_dataset)
        if ds_obj:
            with st.expander(f"Details — {selected_dataset}", expanded=False):
                st.json(ds_obj.to_dict())


def _render_modules(registry: ModuleRegistry) -> None:
    st.subheader("Modules & Operations")
    tip = _mode_tip("modules")
    if tip:
        st.caption(tip)

    modules = cast(dict[str, ModuleDescriptor], getattr(registry, "_modules", {}))

    if not modules:
        st.info(
            "No modules registered. Set LABOS_MODULES or call register_descriptor() from your plugin."
        )
        return

    summary_rows: list[dict[str, object]] = []
    for descriptor in modules.values():
        summary_rows.append(
            {
                "Module": descriptor.module_id,
                "Version": descriptor.version,
                "Operations": len(descriptor.operations),
                "Description": descriptor.description or "—",
            }
        )
    st.dataframe(summary_rows, use_container_width=True)

    st.markdown("### Module Inspector")
    module_ids = sorted(modules.keys())
    selected_module = st.selectbox(
        "Select module",
        options=module_ids,
        help="Review descriptor details before wiring jobs or experiments to it.",
    )
    descriptor = modules[selected_module]
    st.markdown(f"**{descriptor.module_id}** — v{descriptor.version}")
    st.write(descriptor.description or "No description provided.")
    if descriptor.operations:
        st.markdown("Operations")
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
    _render_mode_banner(experiments, datasets, jobs, module_registry)

    section = st.session_state.get("current_section", "Overview")

    if section == "Overview":
        _render_overview(experiments, datasets, jobs, module_registry)
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
