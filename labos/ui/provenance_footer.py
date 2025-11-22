from __future__ import annotations

from html import escape
from typing import Any, Sequence, cast

try:  # pragma: no cover - allows import without optional dependency
    import streamlit as _streamlit  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    class _MissingStreamlit:
        def __getattr__(self, name: str) -> "None":
            raise RuntimeError(
                "Streamlit is not installed. Install the 'streamlit' extra or mock"
                " 'labos.ui.provenance_footer.st' when rendering provenance footers."
            )

    _streamlit = _MissingStreamlit()

from labos.core.module_registry import ModuleMetadata, ModuleRegistry as MetadataRegistry

st = cast(Any, _streamlit)


def render_method_and_data_footer(
    module_registry: MetadataRegistry,
    recent_audits: Sequence[dict[str, object]] | None,
    mode: str,
) -> None:
    """Render a mode-aware Method & Data footer with module provenance hints."""

    st.markdown("---")

    mode_prefix = {
        "Learner": "Preview how LabOS will surface provenance once pipelines are wired.",
        "Lab": "Concise provenance snapshot for quick verification.",
        "Builder": "Raw registry details shown for debugging." ,
    }.get(mode, "Provenance snapshot.")

    st.markdown(
        f"""
        <div style=\"font-size: 0.95rem; opacity: 0.9;\">
        ⓘ <strong>Method &amp; Data</strong> — {escape(mode_prefix)}<br/>
        Module citations live in <code>CITATIONS.md</code> (placeholders until validated).<br/>
        Limitations remain educational scaffolds unless noted otherwise.
        </div>
        """,
        unsafe_allow_html=True,
    )

    metadata: list[ModuleMetadata] = sorted(
        module_registry.all(), key=lambda meta: meta.display_name.lower()
    )
    if not metadata:
        st.info("No method metadata registered yet. Extend labos.core.module_registry to populate this footer.")
        return

    st.markdown("**Module provenance preview**")
    if mode == "Learner":
        st.caption("Each entry lists the method name, key, and limitations to trace future validation steps.")
    elif mode == "Lab":
        st.caption("Use keys to confirm module selection before running jobs.")
    else:
        st.caption("Builder mode exposes IDs to compare against registry definitions.")

    for meta in metadata:
        st.markdown(
            f"- `{escape(meta.method_name)}` (key: `{escape(meta.key)}`) — Limitations: {escape(meta.limitations)}"
        )

    if recent_audits:
        st.markdown("_Recent audit signals_ (latest entries)")
        for event in recent_audits[:3]:
            event_type = escape(str(event.get("event_type", "event")))
            created_at = escape(str(event.get("created_at", "")))
            st.caption(f"• {event_type} — {created_at}")
    else:
        st.caption("Audit stream not loaded yet; provenance events will appear here when available.")

    if mode == "Builder":
        st.json({"metadata_keys": [meta.key for meta in metadata]})
