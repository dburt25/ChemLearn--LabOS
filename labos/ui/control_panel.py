# labos/ui/control_panel.py

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence, TypeVar, TypedDict, cast
import traceback

try:  # pragma: no cover - imported at module import time only
    import streamlit as _streamlit  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - allows tests to run without dependency
    class _MissingStreamlit:
        """Minimal stub that raises a helpful error if Streamlit is unavailable."""

        def __getattr__(self, name: str) -> "None":
            raise RuntimeError(
                "Streamlit is not installed. Install the 'streamlit' extra or patch 'labos.ui.control_panel.st'"
                " in tests before calling UI helpers."
            )

    _streamlit = _MissingStreamlit()

st: Any = cast(Any, _streamlit)

from labos.config import LabOSConfig
from labos.core.errors import NotFoundError
from labos.core.module_registry import ModuleMetadata, ModuleRegistry as MetadataRegistry
from labos.core.workflows import WorkflowResult, run_module_job
from labos.datasets import Dataset
from labos.experiments import Experiment
from labos.jobs import Job
from labos.modules import ModuleDescriptor, ModuleRegistry, get_registry
from labos.runtime import LabOSRuntime
from labos.ui.drawing_tool import render_drawing_tool
from labos.ui.view import extract_dataset_ids
from labos.ui.components import (
    mode_badge,
    render_method_footer,
    section_block,
    section_header,
    spaced_columns,
    subtle_divider,
    title_block,
)
from labos.ui.workspace import render_workspace
from labos.ui.provenance_footer import render_method_and_data_footer


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

JSONListItem = TypeVar("JSONListItem")


class NMRPeak(TypedDict, total=False):
    shift_ppm: float
    intensity: float
    multiplicity: str | None
    notes: str | None


class IRPeak(TypedDict, total=False):
    wavenumber_cm_1: float
    intensity: str
    assignment: str | None
    confidence: float
    notes: str | None


EXPERIMENT_TEMPLATES: list[dict[str, object]] = [
    {
        "key": "calorimetry_warmup",
        "name": "Calorimetry warmup",
        "module_id": "pchem.calorimetry",
        "description": (
            "Prefills a gentle ΔT change and common water heat capacity so learners can see how parameters roll "
            "into experiment, job, and dataset records."
        ),
        "prefill": {
            "experiment_name": "Calorimetry Warmup",
            "sample_id": "SAMPLE-HEAT-01",
            "delta_t": 2.5,
            "heat_capacity": 4.18,
            "actor": "learner-operator",
        },
    },
    {
        "key": "calorimetry_stress",
        "name": "Calorimetry stress test",
        "module_id": "pchem.calorimetry",
        "description": (
            "Uses a larger ΔT swing to simulate high-variance runs. Great for Lab operators validating data capture "
            "before production."
        ),
        "prefill": {
            "experiment_name": "Calorimetry Stress",
            "sample_id": "SAMPLE-HEAT-99",
            "delta_t": 8.0,
            "heat_capacity": 3.9,
            "actor": "lab-operator",
        },
    },
]


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

    if "method_metadata_registry" not in st.session_state:
        st.session_state.method_metadata_registry = MetadataRegistry.with_phase0_defaults()


def _registered_module_entries(
    registry: ModuleRegistry, metadata_registry: MetadataRegistry
) -> list[tuple[str, ModuleDescriptor | None, ModuleMetadata | None]]:
    module_ids = set(metadata_registry.list_keys())
    entries: list[tuple[str, ModuleDescriptor | None, ModuleMetadata | None]] = []

    for module_id in sorted(module_ids):
        descriptor: ModuleDescriptor | None = None
        try:
            descriptor = registry.ensure_module_loaded(module_id)
        except NotFoundError:
            descriptor = None

        meta = metadata_registry.get_metadata_optional(module_id)
        entries.append((module_id, descriptor, meta))

    return entries


def _generate_experiment_id() -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return f"exp-{timestamp}"


def _run_module_from_ui(
    module_key: str,
    params: Mapping[str, object] | None,
    *,
    operation: str = "compute",
    experiment_name: str | None = None,
    actor: str | None = None,
) -> WorkflowResult:
    """Thin wrapper to invoke workflow jobs from UI callbacks."""

    return run_module_job(
        module_key=module_key,
        operation=operation,
        params=dict(params or {}),
        actor=actor or "labos.ui",
        experiment_name=experiment_name,
    )


def _mode_tip(section: str) -> str:
    profile = MODE_PROFILES.get(st.session_state.mode, MODE_PROFILES[MODES[0]])
    fallback = MODE_PROFILES[MODES[0]]
    tips = cast(dict[str, str], profile.get("tips", {}))
    fallback_tips = cast(dict[str, str], fallback.get("tips", {}))
    tip = tips.get(section)
    if tip:
        return tip
    return fallback_tips.get(section, "")


def _resolve_mode(mode: str | None = None) -> str:
    if mode:
        return mode
    current = st.session_state.get("mode") if hasattr(st, "session_state") else None
    if isinstance(current, str) and current:
        return current
    return MODES[0]


def is_learner(mode: str | None = None) -> bool:
    return _resolve_mode(mode) == "Learner"


def is_lab(mode: str | None = None) -> bool:
    return _resolve_mode(mode) == "Lab"


def is_builder(mode: str | None = None) -> bool:
    return _resolve_mode(mode) == "Builder"


def _render_mode_banner(
    experiments: Sequence[Experiment],
    datasets: Sequence[Dataset],
    jobs: Sequence[Job],
    registry: ModuleRegistry,
    metadata_registry: MetadataRegistry,
) -> None:
    profile = MODE_PROFILES.get(st.session_state.mode, MODE_PROFILES[MODES[0]])
    callout_name = str(profile.get("callout", "info"))
    callout = getattr(st, callout_name, st.info)
    modules_count = len(_registered_module_entries(registry, metadata_registry))
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
        expanded = is_learner(st.session_state.mode)
        with st.expander("What is this mode?", expanded=expanded):
            st.markdown(str(what_is_this))


def _render_section_explainer(section: str, mode: str) -> None:
    """Provide mode-aware onboarding for specific sections."""

    learner_notes: dict[str, str] = {
        "Experiments": (
            "Experiments capture the intent of a study, including title, owner, tags, "
            "and timestamps. Use them to group jobs and datasets under a single story."
        ),
        "Jobs": (
            "Jobs are single execution attempts of a module/operation with parameters. "
            "Statuses tell the story of what ran and what failed."
        ),
        "Modules": (
            "Modules wrap scientific methods. Their descriptors advertise operations while "
            "Method metadata links to citations and limitations."
        ),
    }

    if is_learner(mode) and section in learner_notes:
        with st.expander("What is this?", expanded=True):
            st.info(learner_notes[section])


def render_mode_explanation(title: str, learner_note: str, lab_note: str | None = None) -> None:
    """Standardized contextual explanation that adapts to the active mode."""

    if is_learner():
        st.info(f"**{title}** — {learner_note}")
    elif is_lab() and lab_note:
        show_lab_mode_note(lab_note)


def _dataset_label(dataset: Dataset) -> str:
    metadata_label = str(dataset.metadata.get("label", "")).strip()
    return metadata_label or dataset.record_id


def _dataset_kind(dataset: Dataset) -> str:
    return dataset.metadata.get("kind") or dataset.dataset_type.value


def _dataset_preview_text(dataset: Dataset) -> str:
    metadata = dataset.metadata or {}
    schema_preview = metadata.get("schema") or metadata.get("preview")
    if schema_preview:
        return _truncate(json.dumps(schema_preview, default=str), length=160)
    return "Schema preview pending ingestion."


def show_experiment_explanation() -> None:
    st.info(
        "**Experiment** — names the study goal and owner so every job and dataset rolls up to a single story."
    )


def show_job_explanation() -> None:
    st.info(
        "**Job** — one execution attempt inside an experiment. It calls a module with parameters, links datasets,"
        " and logs status changes."
    )


def show_module_explanation() -> None:
    st.info(
        "**Module** — a reusable scientific method that jobs invoke. Descriptors list operations plus citations and"
        " limitations so you know what the computation does."
    )


def show_lab_mode_note(short_note: str) -> None:
    """Concisely remind Lab users what the panel focuses on."""

    st.caption(short_note)


def show_calorimetry_equations() -> None:
    with st.expander("Calorimetry basics (q, m, c, ΔT)", expanded=True):
        st.info(
            "Heat flow is estimated with **q = m · c · ΔT**, where *q* is heat, *m* is sample mass, *c* is specific"
            " heat capacity, and *ΔT* is the observed temperature change."
        )
        st.info(
            "Learner runs multiply your entered *c* and *ΔT* (assuming 1 g) so you can see how heat changes map to"
            " experiment, job, and dataset records."
        )


def show_ei_ms_explanation() -> None:
    with st.expander("EI-MS refresher", expanded=False):
        st.info(
            "Electron ionization mass spectrometry breaks molecules into fragments and plots their intensities against"
            " mass-to-charge (m/z). The resulting spectrum is the pattern of peaks you read to spot likely compounds."
        )


def _parse_float_list(text: str) -> list[float]:
    """Convert comma-separated or JSON list inputs into floats."""

    cleaned = text.strip()
    if not cleaned:
        return []
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, Sequence):
            return [float(item) for item in parsed if isinstance(item, (int, float, str))]
    except json.JSONDecodeError:
        pass

    parts = [part.strip() for part in cleaned.replace("\n", ",").split(",") if part.strip()]
    floats: list[float] = []
    for part in parts:
        try:
            floats.append(float(part))
        except ValueError:
            continue
    return floats


def _parse_annotations(text: str) -> dict[str, object]:
    if not text.strip():
        return {}
    try:
        parsed = json.loads(text)
        if isinstance(parsed, Mapping):
            return {str(key): value for key, value in parsed.items()}
    except json.JSONDecodeError:
        return {}
    return {}


def show_method_metadata(meta: Optional[ModuleMetadata]) -> None:
    if not meta:
        st.caption("Method metadata unavailable for this module.")
        return

    st.markdown("**Method & Data**")
    st.markdown(f"- **Method:** {meta.method_name}")
    st.markdown(f"- **Citation:** {meta.primary_citation or 'Not specified'}")
    st.markdown(f"- **Limitations:** {meta.limitations or 'Not specified'}")
    st.caption(f"Version: {meta.version} • Reference: {meta.reference_url or 'Not provided'}")


def show_calorimetry_method_snippet(meta: Optional[ModuleMetadata], dataset_id: Optional[str]) -> None:
    method_name = meta.method_name if meta else "Calorimetry estimation"
    dataset_label = dataset_id or "dataset pending"
    st.caption(f"Method & Data: {method_name} • Output dataset: {dataset_label}")


def show_method_summary(meta: Optional[ModuleMetadata]) -> None:
    module_key = meta.key if meta else "pchem.calorimetry"
    method_name = meta.method_name if meta else "Calorimetry metadata stub"
    display_name = meta.display_name if meta else "Calorimetry"
    detail = (
        f"Runs {method_name.lower()} to generate educational calorimetry metadata and provenance."
        if meta
        else "Generates placeholder calorimetry metadata for walkthroughs."
    )
    st.info(
        f"**Method & Data** — `{module_key}` ({display_name}) runs {method_name}. {detail}"
    )


def render_method_and_data_panel(meta: ModuleMetadata | None, dataset_id: str | None) -> None:
    """Shared Method & Data rendering adjusted for the active mode."""

    if is_learner():
        show_method_summary(meta)
    elif is_lab():
        show_calorimetry_method_snippet(meta, dataset_id)
    else:
        show_method_metadata(meta)

    module_key = meta.key if meta else "pchem.calorimetry"
    render_method_footer(module_key, meta)


def render_debug_toggle(label: str, key: str, payload: Mapping[str, object] | Sequence[Mapping[str, object]] | None) -> None:
    """Consistent checkbox + JSON renderer for Builder mode."""

    if st.checkbox(label, key=key):
        if isinstance(payload, Mapping):
            st.json(payload)
        else:
            st.json(list(payload or []))


def _safe_parse_json_list(raw_text: str, *, fallback: Optional[Sequence[JSONListItem]] = None) -> list[JSONListItem]:
    """Parse a JSON list from user input, returning a fallback if parsing fails."""

    fallback_list: list[JSONListItem] = list(fallback or [])
    if not raw_text.strip():
        return fallback_list
    try:
        parsed = json.loads(raw_text)
    except Exception:
        st.warning("Unable to parse the provided list; using defaults instead.")
        return fallback_list
    if isinstance(parsed, list):
        parsed_items: list[JSONListItem] = []
        for item in cast(list[Any], parsed):
            parsed_items.append(cast(JSONListItem, item))
        return parsed_items
    st.warning("Expected a JSON array; falling back to defaults.")
    return fallback_list


def show_json_restricted_message(entity: str) -> None:
    st.caption(f"Switch to Builder mode to view raw {entity} JSON.")


def show_calorimetry_raw_data(
    experiment_payload: Optional[Mapping[str, object]],
    job_payload: Optional[Mapping[str, object]],
    dataset_payload: Optional[Mapping[str, object]],
    audit_payload: Optional[Sequence[Mapping[str, object]]],
    meta: Optional[ModuleMetadata],
) -> None:
    if st.checkbox("Show Experiment JSON", key="calorimetry_show_experiment"):
        st.json(experiment_payload or {"message": "No experiment payload captured."})
    if st.checkbox("Show Job JSON", key="calorimetry_show_job"):
        st.json(job_payload or {"message": "No job payload captured."})
    if st.checkbox("Show Dataset JSON", key="calorimetry_show_dataset"):
        st.json(dataset_payload or {"message": "No dataset payload captured."})
    if st.checkbox("Show Audit JSON", key="calorimetry_show_audit"):
        st.json(list(audit_payload or []))
    if st.checkbox("Show Module Metadata", key="calorimetry_show_metadata"):
        st.json(meta.to_dict() if meta else {"message": "No metadata found for pchem.calorimetry."})


def _coerce_float(value: object, default: float) -> float:
    """Best-effort conversion of arbitrary prefill values to float inputs."""

    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return default
    return default


def _render_spectroscopy_stub_results(result: "WorkflowResult", mode: str, stub_kind: str) -> None:
    dataset_id = result.dataset.id if result.dataset else "dataset-pending"
    job_id = result.job.id
    st.success(f"{stub_kind} stub job {job_id} completed; dataset {dataset_id} recorded.")

    module_output: Mapping[str, object] = cast(Mapping[str, object], result.module_output or {})
    annotated = cast(Sequence[object] | None, module_output.get("annotated_peaks"))
    annotated_count = len(annotated) if isinstance(annotated, Sequence) else 0

    if annotated_count and is_learner(mode):
        st.info(
            f"Captured {annotated_count} peak entries with placeholder annotations to illustrate spectroscopy schemas."
        )
    elif annotated_count:
        st.caption(f"{annotated_count} peak entries echoed for verification.")

    if is_builder(mode):
        fallback_payload: Mapping[str, object] = {"message": "No module output returned."}
        debug_payload: Mapping[str, object] = module_output if module_output else fallback_payload
        render_debug_toggle(
            f"Show raw {stub_kind.lower()} stub output",
            key=f"{stub_kind.lower()}_stub_output_{job_id}",
            payload=debug_payload,
        )
    elif is_lab(mode):
        show_lab_mode_note("Raw stub JSON stays tucked away in Lab mode; switch to Builder to inspect schemas.")


def _render_nmr_stub_form(mode: str) -> None:
    st.markdown("##### NMR stub")
    default_peaks: list[NMRPeak] = [
        {"shift_ppm": 7.12, "intensity": 0.8, "multiplicity": "d", "notes": "aromatic"},
    ]
    with st.form("spectroscopy_nmr_stub_form", clear_on_submit=False):
        experiment_name = st.text_input("Experiment name", value="NMR stub experiment")
        sample_id = st.text_input("Sample ID", value="NMR-SAMPLE")
        chemical_formula = st.text_input("Chemical formula", value="C8H10N4O2")
        nucleus = st.text_input("Nucleus", value="1H")
        solvent = st.text_input("Solvent", value="CDCl3")
        shift_ppm = st.number_input("Peak shift (ppm)", value=7.12, step=0.01)
        intensity = st.number_input("Peak intensity", value=0.8, step=0.1)
        multiplicity = st.text_input("Multiplicity", value="d")
        notes = st.text_input("Peak notes", value="placeholder annotation")
        extra_peaks_raw = st.text_area(
            "Additional peaks (JSON list, optional)",
            value="",
            help="Provide an array of additional NMR peaks to include with the stub run.",
        )
        actor = st.text_input("Actor", value="lab-operator")
        submitted = st.form_submit_button("Run NMR stub", use_container_width=True)

    if submitted:
        peak_entry: NMRPeak = {
            "shift_ppm": shift_ppm,
            "intensity": intensity,
            "multiplicity": multiplicity or None,
            "notes": notes or None,
        }
        peaks: list[NMRPeak] = [peak_entry]
        if extra_peaks_raw.strip():
            parsed_peaks = _safe_parse_json_list(extra_peaks_raw, fallback=default_peaks)
            peaks.extend(parsed_peaks)
        with st.spinner("Running spectroscopy.nmr_stub..."):
            try:
                result = run_module_job(
                    module_key="spectroscopy",
                    operation="nmr_stub",
                    params={
                        "sample_id": sample_id,
                        "chemical_formula": chemical_formula,
                        "nucleus": nucleus,
                        "solvent": solvent,
                        "peak_list": peaks,
                    },
                    actor=actor,
                    experiment_name=experiment_name,
                )
            except Exception as exc:  # pragma: no cover - UI feedback path
                st.error(f"NMR stub failed: {exc}")
            else:
                _render_spectroscopy_stub_results(result, mode, "NMR")


def _render_ir_stub_form(mode: str) -> None:
    st.markdown("##### IR stub")
    default_peaks: list[IRPeak] = [
        {"wavenumber_cm_1": 1710, "intensity": "strong", "assignment": "C=O stretch", "confidence": 0.6},
    ]
    with st.form("spectroscopy_ir_stub_form", clear_on_submit=False):
        experiment_name = st.text_input("Experiment name (IR)", value="IR stub experiment")
        sample_id = st.text_input("Sample ID (IR)", value="IR-SAMPLE")
        chemical_formula = st.text_input("Chemical formula (IR)", value="C8H10N4O2")
        wavenumber = st.number_input("Band position (cm^-1)", value=1710, step=5)
        intensity = st.text_input("Band intensity", value="strong")
        assignment = st.text_input("Assignment", value="carbonyl stretch")
        confidence = st.number_input("Assignment confidence", value=0.6, min_value=0.0, max_value=1.0, step=0.05)
        notes = st.text_input("Band notes", value="placeholder band")
        extra_peaks_raw = st.text_area(
            "Additional bands (JSON list, optional)",
            value="",
            help="Provide an array of extra IR bands to echo through the stub.",
        )
        actor = st.text_input("Actor (IR)", value="lab-operator")
        submitted = st.form_submit_button("Run IR stub", use_container_width=True)

    if submitted:
        peak_entry: IRPeak = {
            "wavenumber_cm_1": wavenumber,
            "intensity": intensity,
            "assignment": assignment or None,
            "confidence": confidence,
            "notes": notes or None,
        }
        peaks: list[IRPeak] = [peak_entry]
        if extra_peaks_raw.strip():
            parsed_peaks = _safe_parse_json_list(extra_peaks_raw, fallback=default_peaks)
            peaks.extend(parsed_peaks)
        with st.spinner("Running spectroscopy.ir_stub..."):
            try:
                result = run_module_job(
                    module_key="spectroscopy",
                    operation="ir_stub",
                    params={
                        "sample_id": sample_id,
                        "chemical_formula": chemical_formula,
                        "peak_list": peaks,
                    },
                    actor=actor,
                    experiment_name=experiment_name,
                )
            except Exception as exc:  # pragma: no cover - UI feedback path
                st.error(f"IR stub failed: {exc}")
            else:
                _render_spectroscopy_stub_results(result, mode, "IR")


def _render_spectroscopy_stub_panel(meta_registry: MetadataRegistry, mode: str) -> None:
    meta = meta_registry.get("spectroscopy")

    st.markdown("#### Spectroscopy stubs (NMR + IR)")
    if is_learner(mode):
        st.info(
            "NMR peaks map chemical environments while IR bands highlight functional group vibrations. These stub runners echo "
            "your inputs so you can practice capturing spectra schemas without touching production data."
        )
    elif is_lab(mode):
        show_lab_mode_note("Enter peak or band details and run the stub; results stay lightweight for quick checks.")
    else:
        st.caption("Builder mode exposes registry toggles and raw stub outputs for debugging.")

    if is_builder(mode) and meta:
        render_debug_toggle(
            "Show spectroscopy registry metadata",
            key="spectroscopy_registry_metadata",
            payload=meta.to_dict(),
        )

    nmr_tab, ir_tab = st.tabs(["NMR", "IR"])
    with nmr_tab:
        _render_nmr_stub_form(mode)
    with ir_tab:
        _render_ir_stub_form(mode)


def _job_dataset_ids(job: Job) -> list[str]:
    return extract_dataset_ids(job)


def _find_audit_by_id(
    events: Sequence[dict[str, object]], event_id: Optional[str]
) -> Optional[dict[str, object]]:
    if not event_id:
        return None
    for event in events:
        if str(event.get("event_id")) == str(event_id):
            return event
    return None


def _truncate(text: str, length: int = 140) -> str:
    if len(text) <= length:
        return text
    return text[: length - 1].rstrip() + "…"


def _templates_for_module(module_id: str) -> list[dict[str, object]]:
    return [tpl for tpl in EXPERIMENT_TEMPLATES if tpl.get("module_id") == module_id]


def _apply_template_prefill(prefix: str, template: Mapping[str, object]) -> None:
    prefill = cast(Mapping[str, object], template.get("prefill", {}))
    st.session_state[f"{prefix}_prefill"] = dict(prefill)
    for field, value in prefill.items():
        st.session_state[f"{prefix}_{field}"] = value


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
        if is_learner():
            st.sidebar.caption("Switch to Builder mode to view the staged JSON payload.")
        else:
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
    col1, col2 = spaced_columns([4, 1], gap="large")
    profile = MODE_PROFILES.get(st.session_state.mode, MODE_PROFILES[MODES[0]])
    with col1:
        title_block("🧪 LabOS Control Panel", "ChemLearn LabOS – Phase 0 Skeleton")
        tagline = str(profile.get("tagline", ""))
        if tagline:
            st.caption(tagline)
    with col2:
        st.markdown(mode_badge(st.session_state.mode, emphasize=True), unsafe_allow_html=True)
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
        [
            "Overview",
            "Experiments",
            "Jobs",
            "Datasets",
            "Modules",
            "Audit Log",
            "Workspace",
            "Drawing Tool",
        ],
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
    metadata_registry: MetadataRegistry,
    mode: str,
) -> None:
    section_header("Overview", "Cross-panel snapshot of experiments, jobs, and datasets.", icon="📊")
    tip = _mode_tip("overview")
    if tip:
        st.caption(tip)
    if is_learner(mode):
        st.info(
            "Linked dataset previews show which inputs a job expects. Audits summarize the last recorded action."
        )
    elif is_lab(mode):
        show_lab_mode_note("Compact view highlights current counts without extra guidance.")

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
            if is_lab(mode):
                st.caption("Lab view keeps the latest five experiments within reach.")
            elif is_learner(mode):
                st.caption("Showing the five most recent experiments so you can orient to current work.")
            else:
                st.caption("Builder view trims the sample but exposes full details below.")
        else:
            st.info("No experiments registered yet. Use the sidebar flow or CLI to add one.")
    with module_col:
        st.markdown("#### Modules summary")
        module_entries = _registered_module_entries(registry, metadata_registry)
        if module_entries:
            module_rows: list[dict[str, object]] = []
            for module_id, descriptor, _meta in module_entries[:5]:
                module_rows.append(
                    {
                        "Module": module_id,
                        "Version": descriptor.version if descriptor else "unknown",
                        "Ops": len(descriptor.operations) if descriptor else 0,
                    }
                )
            st.dataframe(module_rows, use_container_width=True)
            if is_learner(mode):
                st.caption("Module Registry previews which scientific tools are wired. Use Modules page for guidance.")
            elif is_lab(mode):
                st.caption("Quick check: confirm the operation count before launching jobs.")
            else:
                st.caption("Builder tip: use the Modules section to compare descriptors vs. metadata registry.")
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

    if is_builder(mode):
        st.info(
            "Builder mode exposes quick registry stats for debugging. IDs and raw dictionaries appear in each section."
        )
    elif is_learner(mode):
        st.success(
            "Everything you see here is intentionally read-friendly. Switch sections to learn how LabOS tracks science."
        )


def _render_experiments(experiments: Sequence[Experiment], mode: str) -> None:
    section_header("Experiments", "Track study umbrellas and their latest updates.", icon="🧬")
    if is_learner():
        show_experiment_explanation()
    _render_section_explainer("Experiments", mode)
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
    st.dataframe(summary, use_container_width=True, hide_index=True)

    record_ids = [exp.record_id for exp in experiments]
    selected_id = st.selectbox(
        "Inspect experiment",
        options=record_ids,
        help="Choose a record to view its full JSON payload.",
    )
    if selected_id:
        selected_exp = next((exp for exp in experiments if exp.record_id == selected_id), None)
        if selected_exp:
            expanded = is_builder(mode)
            with st.expander(f"Details — {selected_exp.title}", expanded=expanded):
                if is_learner():
                    show_json_restricted_message("experiment")
                    st.caption("Switch to Lab for concise fields or Builder for raw JSON.")
                elif is_lab():
                    show_lab_mode_note("Lab view keeps experiment details succinct.")
                    st.markdown(
                        f"**Owner:** {selected_exp.user_id}  \n"
                        f"**Status:** {selected_exp.status.value}  \n"
                        f"**Updated:** {selected_exp.updated_at}"
                    )
                else:
                    if st.checkbox("Show experiment JSON", key=f"exp_json_{selected_id}"):
                        st.json(selected_exp.to_dict())


def _render_jobs(
    jobs: Sequence[Job],
    datasets: Sequence[Dataset],
    audit_events: Sequence[dict[str, object]],
    mode: str,
) -> None:
    section_header("Jobs", "Inspect recorded runs and their linked datasets.", icon="🧾")
    if is_learner():
        show_job_explanation()
    _render_section_explainer("Jobs", mode)
    if not jobs:
        st.info("No jobs have run yet.")
        return

    tip = _mode_tip("jobs")
    if tip:
        st.caption(tip)
    if is_learner(mode):
        st.info(
            "Linked dataset previews show which inputs a job expects. Audits summarize the last recorded action."
        )
    elif is_lab(mode):
        st.caption("Compact view keeps dataset links and audit timestamps within reach.")

    dataset_map = {ds.record_id: ds for ds in datasets}
    job_rows: list[dict[str, object]] = []
    for job in jobs:
        linked_ids = _job_dataset_ids(job)
        linked_preview = (
            ", ".join(linked_ids)
            if linked_ids
            else "No datasets linked"
        )
        audit_info = _find_audit_by_id(audit_events, getattr(job, "last_audit_event_id", None))
        audit_label = "Audit pending"
        if audit_info:
            created_at = audit_info.get("created_at", "")
            audit_label = f"{audit_info.get('event_type', 'event')} @ {created_at}".strip()
        job_rows.append(
            {
                "Job": job.record_id,
                "Status": job.status.value,
                "Module": job.module_id,
                "Operation": job.operation,
                "Experiment": job.experiment_id,
                "Datasets": linked_preview,
                "Audit": audit_label,
                "Updated": job.updated_at,
            }
        )
    st.dataframe(job_rows, use_container_width=True, hide_index=True)
    st.button(
        "Run selected job (coming soon)",
        disabled=True,
        help="TODO: wire job execution triggers once Run buttons are enabled.",
    )

    selected_job = st.selectbox(
        "Inspect job",
        options=[row["Job"] for row in job_rows],
        help="Opens the stored JSON manifest for deeper debugging.",
    )
    if selected_job:
        job_map = {job.record_id: job for job in jobs}
        job_obj = job_map.get(selected_job)
        if job_obj:
            expanded = is_builder(mode)
            with st.expander(f"Details — {selected_job}", expanded=expanded):
                if is_builder(mode):
                    st.caption("Raw job manifest for debugging module contracts and parameters.")
                    render_debug_toggle("Show job JSON", f"job_json_{selected_job}", job_obj.to_dict())
                elif is_learner():
                    show_json_restricted_message("job")
                else:
                    show_lab_mode_note("JSON hidden here to keep the summary focused; open Builder for payloads.")

                st.caption("Linked datasets and latest audit signals help trace provenance from jobs to data.")
                linked_ids = _job_dataset_ids(job_obj)
                if linked_ids:
                    for ds_id in linked_ids:
                        ds_obj = dataset_map.get(ds_id)
                        if ds_obj:
                            st.markdown(
                                f"- `{ds_id}` — {_dataset_label(ds_obj)} ({_dataset_kind(ds_obj)})"
                            )
                            st.caption(_dataset_preview_text(ds_obj))
                        else:
                            st.markdown(f"- `{ds_id}` — dataset record not found yet.")
                else:
                    st.info("No dataset references attached to this job. Add dataset_ids to parameters when wiring execution.")
                audit_info = _find_audit_by_id(audit_events, getattr(job_obj, "last_audit_event_id", None))
                if audit_info:
                    st.write("Last audit event:", audit_info.get("event_type", "event"))
                    st.caption(f"Created at: {audit_info.get('created_at', 'unknown')}")
                else:
                    st.caption("Audit linkage pending. Future runs will populate this automatically.")

    st.caption("Jobs table now hints at linked datasets and audit records; execution wiring will land in a later wave.")


def _render_datasets(datasets: Sequence[Dataset], mode: str) -> None:
    section_header("Datasets", "Preview registered data assets and provenance hints.", icon="🗂️")
    if not datasets:
        st.info("No datasets registered yet.")
        return

    tip = _mode_tip("datasets")
    if tip:
        st.caption(tip)

    if is_learner(mode):
        st.info(
            "This preview shows the imported dataset structure and recent actions so learners can trace provenance before running analyses."
        )

    dataset_rows: list[dict[str, object]] = [
        {
            "Dataset": ds.record_id,
            "Label": _dataset_label(ds),
            "Kind": _dataset_kind(ds),
            "Module Key": ds.metadata.get("module_key", "—"),
            "Schema Preview": _dataset_preview_text(ds),
        }
        for ds in datasets
    ]
    st.dataframe(dataset_rows, use_container_width=True, hide_index=True)

    selected_dataset = st.selectbox(
        "Inspect dataset",
        options=[row["Dataset"] for row in dataset_rows],
        help="Reveal metadata captured at ingestion time.",
    )
    if selected_dataset:
        dataset_map = {ds.record_id: ds for ds in datasets}
        ds_obj = dataset_map.get(selected_dataset)
        if ds_obj:
            with st.expander(f"Details — {selected_dataset}", expanded=is_builder(mode)):
                st.markdown(
                    f"**Label:** {_dataset_label(ds_obj)} | **Kind:** {_dataset_kind(ds_obj)}"
                )
                st.caption(
                    "Module key and schema previews surface what generated this dataset. Future waves will add richer lineage."
                )
                st.write("URI:", ds_obj.uri or "No URI recorded")
                st.write("Owner:", ds_obj.owner)
                st.write("Schema/preview:")
                st.code(_dataset_preview_text(ds_obj))
                if is_learner():
                    show_json_restricted_message("dataset")
                else:
                    if is_builder(mode):
                        st.caption("Full dataset record with IDs and typed fields exposed for ingestion debugging.")
                        render_debug_toggle("Show dataset JSON", f"dataset_json_{selected_dataset}", ds_obj.to_dict())
                    else:
                        show_lab_mode_note("Dataset JSON available in Builder mode to reduce visual clutter here.")

def _render_calorimetry_results(
    payload: Mapping[str, object], meta: Optional[ModuleMetadata], mode: str
) -> None:
    st.markdown("#### Results")

    experiment_payload = cast(Optional[Mapping[str, object]], payload.get("experiment"))
    job_payload = cast(Optional[Mapping[str, object]], payload.get("job"))
    dataset_payload = cast(Optional[Mapping[str, object]], payload.get("dataset"))
    audit_payload = cast(Optional[Sequence[Mapping[str, object]]], payload.get("audit_events"))

    params = cast(Mapping[str, object], (job_payload or {}).get("params") or {})
    delta_t = params.get("delta_t")
    heat_capacity = params.get("heat_capacity")
    sample_id = params.get("sample_id")

    dataset_id = cast(Optional[str], (dataset_payload or {}).get("id"))
    job_id = cast(Optional[str], (job_payload or {}).get("id"))
    experiment_name = cast(Optional[str], (experiment_payload or {}).get("name")) or cast(
        Optional[str], (experiment_payload or {}).get("id")
    )

    heat_transfer: Optional[float] = None
    try:
        if isinstance(delta_t, (int, float)) and isinstance(heat_capacity, (int, float)):
            heat_transfer = float(heat_capacity) * float(delta_t)
    except Exception:  # pragma: no cover - defensive conversion guard
        heat_transfer = None

    summary_rows: list[dict[str, object]] = [
        {
            "Experiment": experiment_name or "Pending",
            "Job": job_id or "Pending",
            "Sample": sample_id or "N/A",
            "Temperature change (ΔT, °C)": delta_t if delta_t is not None else "N/A",
            "Heat capacity (c, J/g*C)": heat_capacity if heat_capacity is not None else "N/A",
            "Heat transferred (q, J)": round(heat_transfer, 3) if heat_transfer is not None else "Stub pending",
            "Dataset": dataset_id or "Pending",
            "Status": (job_payload or {}).get("status", "completed"),
        }
    ]

    st.dataframe(summary_rows, hide_index=True, use_container_width=True)

    if heat_transfer is not None and is_learner():
        st.caption("†Heat transfer assumes a 1 g sample for this educational stub.")

    render_mode_explanation(
        "Experiment & Job summary",
        "Learner mode highlights IDs and provenance context first, keeping JSON optional.",
        "Concise, operator-focused summary; detailed JSON stays tucked away.",
    )

    render_method_and_data_panel(meta, dataset_id)

    if is_builder(mode):
        st.markdown("##### Debug views")
        st.caption("Toggle JSON payloads to debug registry wiring and workflow results.")
        show_calorimetry_raw_data(experiment_payload, job_payload, dataset_payload, audit_payload, meta)


def _render_pchem_calorimetry_runner(meta_registry: MetadataRegistry, mode: str) -> None:
    meta = meta_registry.get("pchem.calorimetry")
    templates = _templates_for_module("pchem.calorimetry")

    st.markdown("#### Run Calorimetry Workflow (beta)")
    if is_learner(mode):
        st.caption(
            "Learner mode explains each part of the workflow before you run it."
        )
        show_calorimetry_equations()
        show_method_summary(meta)
    elif is_lab(mode):
        show_lab_mode_note("Enter only the required fields; detailed equations hide in Learner mode.")
    else:
        st.caption("Creates an experiment + job, calls the PChem calorimetry stub, and emits dataset/audit metadata.")
        if meta:
            st.caption(f"Registry method: {meta.method_name}")

    if is_builder(mode):
        if st.checkbox("Show calorimetry registry metadata", key="calorimetry_registry"):
            st.json(meta.to_dict() if meta else {"message": "No registry entry found for pchem.calorimetry."})

    template_options = ["Custom run"] + [str(tpl.get("name", tpl.get("key", "template"))) for tpl in templates]
    selected_template = st.selectbox(
        "Start from Template",
        options=template_options,
        help="Prefill module parameters using saved experiment templates.",
        key="pchem_template_choice",
    )

    selected_template_payload: Mapping[str, object] | None = None
    selected_template_key = "custom"
    for tpl in templates:
        if tpl.get("name") == selected_template:
            selected_template_payload = tpl
            selected_template_key = str(tpl.get("key", tpl.get("name", "custom")))
            break

    last_template_key = st.session_state.get("pchem_last_template")
    if selected_template_key != last_template_key:
        st.session_state.pchem_last_template = selected_template_key
        if selected_template_payload:
            _apply_template_prefill("pchem", selected_template_payload)
        else:
            st.session_state.pop("pchem_template_prefill", None)

    template_prefill = cast(Mapping[str, object], st.session_state.get("pchem_template_prefill", {}))
    delta_t_prefill = _coerce_float(template_prefill.get("delta_t"), 3.5)
    heat_capacity_prefill = _coerce_float(template_prefill.get("heat_capacity"), 4.18)

    if selected_template_payload:
        description = str(selected_template_payload.get("description", ""))
        if is_learner(mode):
            st.info(f"Template guide: {description}")
        elif is_lab(mode):
            st.caption(f"Template: {description}")
        else:
            st.caption(description)
            render_debug_toggle(
                "Show template JSON",
                key="pchem_template_json",
                payload=selected_template_payload,
            )

    if is_learner(mode):
        st.markdown("##### How this works")
        show_experiment_explanation()
        show_job_explanation()
        show_module_explanation()

    default_name = st.session_state.get("pchem_default_experiment")
    if not default_name:
        default_name = f"Calorimetry Demo {datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"

    with st.form("pchem_calorimetry_form", clear_on_submit=False):
        experiment_name = st.text_input(
            "Experiment Name",
            value=str(template_prefill.get("experiment_name", default_name)),
            key="pchem_experiment_name",
        )
        sample_id = st.text_input(
            "Sample ID",
            value=str(template_prefill.get("sample_id", "SAMPLE-STUB")),
            key="pchem_sample_id",
        )
        delta_t = st.number_input(
            "Delta T (C)",
            value=delta_t_prefill,
            step=0.1,
            key="pchem_delta_t",
        )
        heat_capacity = st.number_input(
            "Heat Capacity (J/g*C)",
            value=heat_capacity_prefill,
            step=0.01,
            key="pchem_heat_capacity",
        )
        actor = st.text_input(
            "Actor",
            value=str(template_prefill.get("actor", "lab-operator")),
            key="pchem_actor",
        )
        submitted = st.form_submit_button("Run calorimetry workflow", use_container_width=True)

    if submitted:
        st.session_state.pchem_default_experiment = experiment_name
        with st.spinner("Executing calorimetry stub..."):
            try:
                result = _run_module_from_ui(
                    "pchem.calorimetry",
                    {
                        "sample_id": sample_id,
                        "delta_t": float(delta_t),
                        "heat_capacity": float(heat_capacity),
                        "actor": actor,
                    },
                    actor=actor,
                    experiment_name=experiment_name,
                )
            except Exception as exc:  # pragma: no cover - UI feedback path
                st.error(f"Calorimetry workflow failed: {exc}")
                if is_builder(mode):
                    with st.expander("Show traceback", expanded=False):
                        st.code(traceback.format_exc())
            else:
                dataset_label = result.dataset.id if result.dataset else "dataset-pending"
                st.success(f"Job {result.job.id} completed; produced {dataset_label}.")
                st.session_state.pchem_last_workflow = {"payload": result.to_dict()}

        last_payload = st.session_state.get("pchem_last_workflow")
        payload = None
        if isinstance(last_payload, Mapping):
            last_mapping = cast(Mapping[str, object], last_payload)
            candidate = last_mapping.get("payload")
            payload = cast(Mapping[str, object] | None, candidate or last_mapping)

        if payload:
            _render_calorimetry_results(payload, meta, mode)


def _render_ei_ms_results(result: WorkflowResult, mode: str) -> None:
    dataset_id = result.dataset.id if result.dataset else "dataset-pending"
    st.success(f"EI-MS job {result.job.id} completed; dataset {dataset_id} recorded.")

    module_output = cast(Mapping[str, object], result.module_output or {})
    fragments = module_output.get("fragments")
    if isinstance(fragments, Sequence):
        fragment_rows = []
        for fragment in fragments:
            if not isinstance(fragment, Mapping):
                continue
            fragment_rows.append(
                {
                    "Mass (m/z)": fragment.get("mass"),
                    "Relative Intensity": fragment.get("relative_intensity"),
                    "Classification": fragment.get("classification"),
                    "Annotation": fragment.get("annotation", "—"),
                }
            )
        if fragment_rows:
            st.dataframe(fragment_rows, use_container_width=True, hide_index=True)
    summary = module_output.get("summary")
    if isinstance(summary, Mapping):
        neutral_losses = summary.get("neutral_losses")
        if isinstance(neutral_losses, Sequence) and neutral_losses:
            st.markdown("**Neutral loss suggestions**")
            st.dataframe(neutral_losses, use_container_width=True, hide_index=True)

    if is_builder(mode):
        render_debug_toggle(
            "Show EI-MS raw output", key="ei_ms_output_debug", payload=module_output or {"message": "No output"}
        )


def _render_ei_ms_runner(meta_registry: MetadataRegistry, mode: str) -> None:
    meta = meta_registry.get("ei_ms.basic_analysis")

    st.markdown("#### Run EI-MS basic analysis")
    if is_learner(mode):
        show_ei_ms_explanation()
    elif is_lab(mode):
        show_lab_mode_note("Enter masses and run the workflow to tag fragments.")
    elif meta:
        st.caption(f"Method: {meta.method_name}")

    default_name = st.session_state.get("ei_ms_default_experiment") or "EI-MS walkthrough"

    with st.form("ei_ms_basic_analysis", clear_on_submit=False):
        experiment_name = st.text_input("Experiment Name", value=default_name, key="ei_ms_experiment_name")
        precursor_mass = st.number_input("Precursor mass (m/z)", value=180.16, step=0.01)
        fragment_masses_raw = st.text_area(
            "Fragment masses (comma-separated or JSON list)",
            value="15, 28, 43, 57, 71",
            help="Provide fragment m/z values to analyze.",
        )
        fragment_intensities_raw = st.text_area(
            "Fragment intensities (optional)",
            value="100, 75, 60, 40, 20",
            help="Optional relative intensities to improve tagging.",
        )
        annotations_raw = st.text_area(
            "Annotations (JSON mapping, optional)",
            value="{\"43\": \"base peak\"}",
            help="Map m/z values to labels such as base peaks or known fragments.",
        )
        actor = st.text_input("Actor", value="lab-operator", key="ei_ms_actor")
        submitted = st.form_submit_button("Run EI-MS analysis", use_container_width=True)

    if submitted:
        st.session_state.ei_ms_default_experiment = experiment_name
        fragment_masses = _parse_float_list(fragment_masses_raw)
        intensities = _parse_float_list(fragment_intensities_raw)
        annotations = _parse_annotations(annotations_raw)

        params: dict[str, object] = {
            "precursor_mass": float(precursor_mass),
            "fragment_masses": fragment_masses,
        }
        if intensities:
            params["fragment_intensities"] = intensities
        if annotations:
            params["annotations"] = annotations

        with st.spinner("Running EI-MS workflow..."):
            try:
                result = _run_module_from_ui(
                    "ei_ms.basic_analysis",
                    params,
                    operation="analyze",
                    experiment_name=experiment_name,
                    actor=actor,
                )
            except Exception as exc:  # pragma: no cover - UI feedback path
                st.error(f"EI-MS analysis failed: {exc}")
                if is_builder(mode):
                    with st.expander("Show traceback", expanded=False):
                        st.code(traceback.format_exc())
            else:
                _render_ei_ms_results(result, mode)


def _render_modules(registry: ModuleRegistry, metadata_registry: MetadataRegistry, mode: str) -> None:
    section_header("Modules & Operations", "Review registered modules and guided runners.", icon="🧭")
    if is_learner():
        show_module_explanation()
        show_ei_ms_explanation()
    _render_section_explainer("Modules", mode)
    tip = _mode_tip("modules")
    if tip:
        st.caption(tip)

    module_entries = _registered_module_entries(registry, metadata_registry)
    metadata_map = {meta.key: meta for meta in metadata_registry.all()}

    if module_entries:
        summary_rows: list[dict[str, object]] = []
        for module_id, descriptor, meta in module_entries:
            summary_rows.append(
                {
                    "Module": meta.display_name if meta else module_id,
                    "Key": module_id,
                    "Method": meta.method_name if meta else "Pending metadata",
                    "Ops": len(descriptor.operations) if descriptor else 0,
                    "Citation": _truncate(meta.primary_citation if meta else "Awaiting citation"),
                    "Limitations": _truncate(meta.limitations if meta else "Add limitations"),
                }
            )
        st.dataframe(summary_rows, use_container_width=True, hide_index=True)
        if is_lab(mode):
            st.caption("Compact registry view for quick verification before launching jobs.")
        elif is_learner(mode):
            st.caption("Each row pairs a module key with its method name and citation so you can trace provenance.")
        else:
            st.caption("Builder mode keeps keys visible to match code, jobs, and metadata entries.")
    else:
        st.info("No modules registered. Set LABOS_MODULES or call register_descriptor() from your plugin.")
        return

    subtle_divider()
    with section_block(
        "Module Inspector",
        "Future waves will add Run buttons that execute operations into Jobs/Datasets.",
        icon="🔎",
    ):
        module_ids = [module_id for module_id, _descriptor, _meta in module_entries]
        selected_module = st.selectbox(
            "Select module",
            options=module_ids,
            help="Review descriptor details before wiring jobs or experiments to it.",
        )

        entry = next((item for item in module_entries if item[0] == selected_module), None)
        if entry is None:
            st.warning("Selected module descriptor not found.")
            return

        descriptor = entry[1]
        meta = metadata_map.get(selected_module)
        if descriptor is None:
            st.warning("Selected module descriptor not found.")
            return

        if is_lab(mode):
            show_lab_mode_note(
                f"{len(descriptor.operations)} operation(s) ready; {_truncate(meta.method_name if meta else 'method metadata pending')}"
            )
        elif is_builder(mode) and meta:
            st.caption("Registry metadata available below for debugging.")

        st.write(descriptor.description or "No description provided.")
        if meta and not is_lab(mode):
            st.markdown(f"_Method:_ {meta.method_name}")
            st.markdown(f"_Citation:_ {_truncate(meta.primary_citation)}")
            st.markdown(f"_Limitations:_ {_truncate(meta.limitations)}")
        if descriptor.operations:
            st.markdown("Operations")
            for op in descriptor.operations.values():
                st.markdown(f"- `{op.name}` — {op.description}")
            if descriptor.module_id == "spectroscopy":
                _render_spectroscopy_stub_panel(metadata_registry, mode)
            elif descriptor.module_id == "pchem.calorimetry":
                _render_pchem_calorimetry_runner(metadata_registry, mode)
            elif descriptor.module_id == "ei_ms.basic_analysis":
                _render_ei_ms_runner(metadata_registry, mode)
            else:
                st.button(
                    "Run (coming soon)",
                    disabled=True,
                    help="Execution wiring will be added in a later phase. TODO: attach run handlers to jobs queue.",
                )
        else:
            st.write("_No operations registered._")

        if is_builder(mode):
            st.markdown("#### Debug payloads")
            st.caption("Toggle registry entries to validate wiring without cluttering other modes.")
            render_debug_toggle(
                "Show descriptor JSON",
                key=f"descriptor_json_{descriptor.module_id}",
                payload={
                    "module_id": descriptor.module_id,
                    "version": descriptor.version,
                    "operations": {op.name: op.description for op in descriptor.operations.values()},
                },
            )
            if meta:
                render_debug_toggle(
                    "Show registry metadata",
                    key=f"metadata_json_{descriptor.module_id}",
                    payload={"metadata_key": meta.key, "metadata": meta.__dict__},
                )


def _render_audit_log(events: Sequence[dict[str, object]], mode: str) -> None:
    st.subheader("Audit Log")
    if is_learner(mode):
        st.info("Audit entries show who did what, when, and why. These logs anchor ALCOA+ compliance.")
    if not events:
        st.info("No audit events recorded yet.")
        return

    for event in events:
        header = f"{event.get('event_id', 'unknown')} — {event.get('event_type', 'event')}"
        with st.expander(header, expanded=False):
            if is_learner():
                st.markdown(
                    f"**Actor:** {event.get('actor', 'unknown')}  \n"
                    f"**Action:** {event.get('event_type', event.get('action', 'event'))}  \n"
                    f"**Target:** {event.get('target', 'N/A')}  \n"
                    f"**Created:** {event.get('created_at', 'unknown')}"
                )
            else:
                st.json(event)
    if is_builder(mode):
        st.caption("Builder mode exposes raw audit dictionaries to validate logging schemas.")

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
    method_metadata_registry: MetadataRegistry = st.session_state.method_metadata_registry

    experiments = _load_experiments(runtime)
    datasets = _load_datasets(runtime)
    jobs = _load_jobs(runtime.config)
    audit_events = _load_audit_events(runtime.config)

    _render_header()
    _render_sidebar()
    _render_mode_banner(experiments, datasets, jobs, module_registry, method_metadata_registry)

    section = st.session_state.get("current_section", "Overview")
    mode = st.session_state.mode

    if section == "Overview":
        _render_overview(experiments, datasets, jobs, module_registry, method_metadata_registry, mode)
    elif section == "Experiments":
        _render_experiments(experiments, mode)
    elif section == "Jobs":
        _render_jobs(jobs, datasets, audit_events, mode)
    elif section == "Datasets":
        _render_datasets(datasets, mode)
    elif section == "Modules":
        _render_modules(module_registry, method_metadata_registry, mode)
    elif section == "Audit Log":
        _render_audit_log(audit_events, mode)
    elif section == "Workspace":
        render_workspace(experiments, jobs, datasets, mode)
    elif section == "Drawing Tool":
        render_drawing_tool(mode)

    render_method_and_data_footer(method_metadata_registry, audit_events, mode)
