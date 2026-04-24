"""
Short-Term Memory — Sliding-window conversation buffer.

Stores the most recent N messages (user + assistant turns) so the agent
has immediate conversational context without exceeding token budgets.
"""

from __future__ import annotations

import copy
from typing import Any


class ShortTermMemory:
    """
    A fixed-size sliding window over the conversation history.

    Parameters
    ----------
    window_size : int
        Maximum number of message pairs to retain (default 10).
    """

    def __init__(self, window_size: int = 10) -> None:
        self.window_size = window_size
        self._buffer: list[dict[str, str]] = []

    # ── Public API ───────────────────────────────────────────────────────

    def add_message(self, role: str, content: str) -> None:
        """Append a message and trim to window size."""
        self._buffer.append({"role": role, "content": content})
        # Keep only the last `window_size` messages
        if len(self._buffer) > self.window_size:
            self._buffer = self._buffer[-self.window_size :]

    def get_recent_messages(self, n: int | None = None) -> list[dict[str, str]]:
        """Return the last *n* messages (default: all in window)."""
        if n is None:
            return copy.deepcopy(self._buffer)
        return copy.deepcopy(self._buffer[-n:])

    def clear(self) -> None:
        """Reset the buffer."""
        self._buffer.clear()

    def get_formatted(self) -> str:
        """Return messages as a formatted string for prompt injection."""
        lines: list[str] = []
        for msg in self._buffer:
            prefix = "User" if msg["role"] == "user" else "Assistant"
            lines.append(f"{prefix}: {msg['content']}")
        return "\n".join(lines)

    @property
    def size(self) -> int:
        return len(self._buffer)

    def __repr__(self) -> str:
        return f"ShortTermMemory(window={self.window_size}, current={self.size})"
