"""Shared helpers for OpenAI and progress reporting."""

from __future__ import annotations

import os
from collections.abc import Callable, Generator
from contextlib import contextmanager

ProgressCallback = Callable[[str, str, str], None]


@contextmanager
def use_openai_api_key(api_key: str | None) -> Generator[None, None, None]:
    """Temporarily override OPENAI_API_KEY for a single request."""
    if not api_key:
        yield
        return

    previous = os.environ.get("OPENAI_API_KEY")
    os.environ["OPENAI_API_KEY"] = api_key
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop("OPENAI_API_KEY", None)
        else:
            os.environ["OPENAI_API_KEY"] = previous


def emit_progress(
    callback: ProgressCallback | None,
    step: str,
    message: str,
    status: str = "running",
) -> None:
    if callback:
        callback(step, message, status)
