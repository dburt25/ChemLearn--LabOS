"""LLM abstraction hooks (placeholders until providers are configured)."""

from __future__ import annotations

from typing import Any, Iterable, Mapping


def llm_complete(prompt: str, model: str = "gpt-5.1", **kwargs: Any) -> str:
    """Thin wrapper for text completion APIs.

    The implementation is intentionally deferred until compliance reviews for AI
    providers are complete. Calling this function raises ``NotImplementedError``
    to make the dependency explicit.
    """

    raise NotImplementedError("LLM usage requires an approved provider binding")


def llm_chat(messages: Iterable[Mapping[str, str]], model: str = "gpt-5.1", **kwargs: Any) -> str:
    """Placeholder chat completion helper (see note above)."""

    raise NotImplementedError("Chat APIs are not wired yet")
