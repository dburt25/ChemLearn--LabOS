"""Workspace view for experiments and job history."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping, Sequence, cast

try:  # pragma: no cover - imported at module import time only
    import streamlit as _streamlit  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - allows tests to run without dependency
    class _MissingStreamlit:
        """Minimal stub that raises a helpful error if Streamlit is unavailable."""

        def __getattr__(self, name: str) -> "None":
            raise RuntimeError(
                "Streamlit is not installed. Install the 'streamlit' extra or patch 'labos.ui.workspace.view.st'"
                " in tests before calling UI helpers."
            )

    _streamlit = _MissingStreamlit()

st: Any = cast(Any, _streamlit)

from labos.experiments import Experiment
from labos.jobs import Job, JobStatus


def _truncate(text: str, length: int = 160) -> str:
    if len(text) <= length:
        return text
    return text[: length - 1].rstrip() + "…"


def _parse_timestamp(value: str | None) -> str:
    if not value:
        return "Unknown"
    try:
        parsed = datetime.fromisoformat(value)
        return parsed.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:  # pragma: no cover - fallback for unexpected formats
        return value


def _job_status_label(status: JobStatus) -> str:
    display_map: dict[JobStatus, str] = {
        JobStatus.SUCCEEDED: "✅ Finished",
        JobStatus.FAILED: "❌ Failed",
        JobStatus.RUNNING: "⏳ Running",
        JobStatus.CANCELLED: "🚫 Cancelled",
        JobStatus.PENDING: "🕒 Pending",
    }
    return display_map.get(status, status.value)


def _job_status_color(status: JobStatus) -> str:
    if status == JobStatus.SUCCEEDED:
        return "green"
    if status == JobStatus.FAILED or status == JobStatus.CANCELLED:
        return "red"
    if status == JobStatus.RUNNING:
        return "orange"
    return "gray"


def _job_timestamp(job: Job) -> str:
    if getattr(job, "completed_at", None):
        return _parse_timestamp(cast(str | None, job.completed_at))
    if getattr(job, "updated_at", None):
        return _parse_timestamp(cast(str | None, job.updated_at))
    return _parse_timestamp(cast(str | None, getattr(job, "created_at", None)))


def _extract_dataset_ids(job: Job) -> list[str]:
    ids: list[str] = []
    params_obj = getattr(job, "parameters", None)
    if not isinstance(params_obj, Mapping):
        return ids
    parameters = cast(Mapping[str, object], params_obj)
    maybe_many = parameters.get("dataset_ids")
    if isinstance(maybe_many, Sequence) and not isinstance(maybe_many, (str, bytes, bytearray)):
        ids.extend(str(item) for item in maybe_many)
    maybe_one = parameters.get("dataset_id")
    if maybe_one is not None:
        ids.append(str(maybe_one))
    return list(dict.fromkeys(ids))


def _job_description(job: Job) -> str:
    params: Mapping[str, object] = cast(Mapping[str, object], getattr(job, "parameters", {}) or {})
    for key in ("summary", "description", "notes"):
        candidate = params.get(key)
        if isinstance(candidate, str) and candidate.strip():
            return _truncate(candidate.strip())

    datasets = _extract_dataset_ids(job)
    if datasets:
        return f"Linked datasets: {', '.join(datasets)}"

    if getattr(job, "error", None):
        return _truncate(str(job.error))

    return f"Operation `{job.operation}` by {job.actor}".strip()


def _render_job(job: Job, *, builder: bool) -> None:
    timestamp = _job_timestamp(job)
    status_label = _job_status_label(job.status)
    color = _job_status_color(job.status)

    row = st.columns([2, 1, 1.2, 3])
    row[0].markdown(f"**{job.module_id}** · `{job.operation}`")
    row[1].markdown(
        f"<span style='color:{color};font-weight:600'>{status_label}</span>",
        unsafe_allow_html=True,
    )
    row[2].markdown(f"`{timestamp}`")
    row[3].markdown(_job_description(job))

    if builder:
        with st.expander("Inspect job JSON", expanded=False):
            st.json(job.to_dict())


def _render_experiment_header(experiment: Experiment) -> None:
    status = getattr(experiment, "status", None)
    created = _parse_timestamp(getattr(experiment, "created_at", None))
    updated = _parse_timestamp(getattr(experiment, "updated_at", None))
    st.markdown(
        f"### {experiment.title or experiment.record_id}\n"
        f"`{experiment.record_id}` · Status: **{getattr(status, 'value', status)}**"
    )
    st.caption(f"Created: {created} • Updated: {updated} • Owner: {experiment.user_id}")


def _render_experiment_block(experiment: Experiment, jobs: Sequence[Job], *, builder: bool) -> None:
    with st.container():
        _render_experiment_header(experiment)
        exp_jobs = sorted(
            jobs,
            key=lambda job: getattr(job, "updated_at", ""),
            reverse=True,
        )
        if not exp_jobs:
            st.info("No jobs linked to this experiment yet.")
        else:
            for job in exp_jobs:
                _render_job(job, builder=builder)
        if builder:
            with st.expander("Inspect experiment JSON", expanded=False):
                st.json(experiment.to_dict())


def render_workspace(experiments: Sequence[Experiment], jobs: Sequence[Job], mode: str) -> None:
    """Render workspace area with experiments and job history."""

    builder = mode == "Builder"

    st.subheader("Workspace")
    st.caption("Review experiments alongside their recorded jobs and statuses.")

    col1, col2, col3 = st.columns([1, 1, 1.5])
    col1.metric("Experiments", len(experiments))
    col2.metric("Jobs", len(jobs))
    latest_timestamp = None
    for job in sorted(jobs, key=lambda j: getattr(j, "updated_at", ""), reverse=True):
        latest_timestamp = _job_timestamp(job)
        break
    col3.metric("Latest job update", latest_timestamp or "—")

    if not experiments:
        st.info("No experiments recorded yet. Run a workflow to see experiments and jobs appear here.")
        return

    experiment_index = {exp.record_id: exp for exp in experiments}
    sorted_experiments = sorted(
        experiment_index.values(),
        key=lambda exp: getattr(exp, "created_at", ""),
        reverse=True,
    )

    jobs_by_experiment: dict[str, list[Job]] = {exp.record_id: [] for exp in sorted_experiments}
    for job in jobs:
        jobs_by_experiment.setdefault(job.experiment_id, []).append(job)

    orphan_jobs = [job for job in jobs if job.experiment_id not in jobs_by_experiment]

    for exp in sorted_experiments:
        _render_experiment_block(exp, jobs_by_experiment.get(exp.record_id, []), builder=builder)

    if orphan_jobs:
        st.markdown("#### Jobs without an experiment link")
        st.caption("These jobs reference missing or deleted experiments.")
        for job in orphan_jobs:
            _render_job(job, builder=builder)

    st.caption("Statuses update after workflows run; refresh the page to pick up newly written manifests.")
