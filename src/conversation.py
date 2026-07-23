"""Conversation history helpers for multi-turn chat."""

from __future__ import annotations

from typing import Literal, TypedDict

ChatRole = Literal["user", "assistant"]


class ChatMessage(TypedDict):
    role: ChatRole
    content: str


def format_history_for_prompt(
    history: list[ChatMessage],
    max_turns: int = 6,
) -> str:
    """Format prior messages as plain text for LLM prompts."""
    if not history:
        return ""

    lines: list[str] = []
    for message in history[-max_turns:]:
        label = "User" if message["role"] == "user" else "Assistant"
        lines.append(f"{label}: {message['content']}")

    return "\n".join(lines)


def build_search_query(question: str, history: list[ChatMessage]) -> str:
    """Expand a follow-up question with conversation context for semantic search."""
    if not history:
        return question

    context = format_history_for_prompt(history, max_turns=4)
    return (
        "Conversation context:\n"
        f"{context}\n\n"
        f"Follow-up question: {question}"
    )
