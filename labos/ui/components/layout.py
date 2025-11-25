"""Layout helpers for LabOS Streamlit views."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator, Sequence, Tuple, Union, cast

try:  # pragma: no cover - imported at module import time only
    import streamlit as _streamlit  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - allows tests to run without dependency
    class _MissingStreamlit:
        """Minimal stub that raises a helpful error if Streamlit is unavailable."""

        def __getattr__(self, name: str) -> "None":
            raise RuntimeError(
                "Streamlit is not installed. Install the 'streamlit' extra or patch 'labos.ui.components.layout.st'"
                " in tests before calling UI helpers."
            )

    _streamlit = _MissingStreamlit()

st: Any = cast(Any, _streamlit)


def spaced_columns(spec: Union[Sequence[float], int], *, gap: str = "medium") -> list[Any]:
    """Wrapper around ``st.columns`` with consistent gaps."""

    return st.columns(spec, gap=gap)


def mode_badge(mode: str, *, emphasize: bool = False) -> str:
    """Return HTML for a pill-shaped badge that highlights the current mode."""

    color_map = {
        "Learner": ("#0ea5e9", "#f0f9ff"),
        "Lab": ("#22c55e", "#ecfdf3"),
        "Builder": ("#f59e0b", "#fffbeb"),
    }
    primary, background = color_map.get(mode, ("#6366f1", "#eef2ff"))
    weight = "700" if emphasize else "600"
    return (
        f"<span style=\"display:inline-block;padding:0.35rem 0.75rem;border-radius:999px;"
        f"background:{background};color:{primary};font-weight:{weight};"
        "font-size:0.85rem;letter-spacing:0.01em;\">"
        f"{mode} mode"
        "</span>"
    )


def subtle_divider() -> None:
    """Insert a soft divider to separate sections without heavy borders."""

    st.markdown("<hr style='opacity:0.25;margin:0.5rem 0 1.25rem 0;'>", unsafe_allow_html=True)


def section_header(
    title: str, subtitle: Union[str, None] = None, *, icon: Union[str, None] = None
) -> None:
    """Render a consistent section heading with optional subtitle."""

    heading = f"{icon} {title}" if icon else title
    st.markdown(f"### {heading}")
    if subtitle:
        st.caption(subtitle)


@contextmanager
def section_block(
    title: str, subtitle: Union[str, None] = None, *, icon: Union[str, None] = None
) -> Iterator[Tuple[str, Union[str, None]]]:
    """Container context that prefixes content with a section header."""

    with st.container():
        section_header(title, subtitle, icon=icon)
        yield title, subtitle
    st.markdown("")


def title_block(title: str, subtitle: Union[str, None] = None) -> None:
    """Top-level title with optional supporting caption."""

    st.markdown(f"# {title}")
    if subtitle:
        st.caption(subtitle)
