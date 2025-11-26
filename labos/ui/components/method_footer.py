from __future__ import annotations

from html import escape
from typing import Any, cast

try:  # pragma: no cover - optional dependency guard
    import streamlit as _streamlit  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    class _MissingStreamlit:
        """Minimal stub to avoid import errors when Streamlit is absent."""

        def __getattr__(self, name: str) -> "None":
            raise RuntimeError(
                "Streamlit is not installed. Install the 'streamlit' extra or mock"
                " 'labos.ui.components.method_footer.st' when rendering footers."
            )

    _streamlit = _MissingStreamlit()

from labos.core.module_registry import ModuleMetadata

st: Any = cast(Any, _streamlit)


def render_method_footer(module_key: str, metadata: ModuleMetadata | None) -> None:
    """Render a compact method metadata footer for a module.

    Parameters
    ----------
    module_key:
        Registry key for the module, used as an identifier when metadata is missing.
    metadata:
        Module metadata entry; when absent, the footer explains how to populate it.
    """

    st.markdown("---")

    if metadata is None:
        st.caption(
            f"Method metadata for `{escape(module_key)}` is not available yet. "
            "Add a ModuleMetadata entry to populate this footer."
        )
        return

    method_name = metadata.method_name or "Method name pending"
    citation = metadata.primary_citation or "Citation pending"
    limitations = metadata.limitations or "Limitations not documented"
    display_name = metadata.display_name or module_key
    reference_url = metadata.reference_url or "Reference URL pending"
    version = metadata.version or "Unversioned"

    st.markdown(f"**Method metadata** — `{escape(module_key)}` ({escape(display_name)})")
    st.caption(f"{escape(method_name)}")
    st.caption(f"Citation: {escape(citation)}")
    st.caption(f"Limitations: {escape(limitations)}")
    st.caption(f"Reference: {escape(reference_url)} • Version: {escape(version)}")
