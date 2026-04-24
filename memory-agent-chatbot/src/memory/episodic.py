"""
Episodic Memory — Timestamped event/outcome log.

Records significant events from conversations (task completions,
decisions, user preferences expressed, debugging lessons, etc.)
so the agent can recall *what happened* in the past.
"""

from __future__ import annotations

import json
import os
import time
import uuid
from typing import Any, Optional

from src.config import Config


class EpisodicMemory:
    """
    Append-only log of conversation episodes, persisted to JSON.

    Each episode:
        {
            "id": str,
            "timestamp": float,
            "summary": str,
            "context": str,       # conversation snippet / topic
            "outcome": str,       # what happened / resolution
            "tags": list[str],    # searchable tags
        }
    """

    def __init__(self, user_id: str = "default") -> None:
        self.user_id = user_id
        self._episodes: list[dict[str, Any]] = []
        self._load()

    # ── Persistence ──────────────────────────────────────────────────────

    def _load(self) -> None:
        path = Config.EPISODES_PATH
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                all_episodes = json.load(f)
                self._episodes = all_episodes.get(self.user_id, [])

    def _save(self) -> None:
        path = Config.EPISODES_PATH
        os.makedirs(os.path.dirname(path), exist_ok=True)
        all_episodes = {}
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                all_episodes = json.load(f)
        all_episodes[self.user_id] = self._episodes
        with open(path, "w", encoding="utf-8") as f:
            json.dump(all_episodes, f, ensure_ascii=False, indent=2)

    # ── Public API ───────────────────────────────────────────────────────

    def add_episode(
        self,
        summary: str,
        context: str = "",
        outcome: str = "",
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        """Record a new episode and persist it."""
        episode = {
            "id": str(uuid.uuid4())[:8],
            "timestamp": time.time(),
            "summary": summary,
            "context": context,
            "outcome": outcome,
            "tags": tags or [],
        }
        self._episodes.append(episode)
        self._save()
        return episode

    def get_recent(self, n: int = 5) -> list[dict[str, Any]]:
        """Return the last *n* episodes."""
        return self._episodes[-n:]

    def search_by_tag(self, tag: str) -> list[dict[str, Any]]:
        """Find episodes that match a tag (case-insensitive)."""
        tag_lower = tag.lower()
        return [ep for ep in self._episodes if tag_lower in [t.lower() for t in ep.get("tags", [])]]

    def search_by_keyword(self, keyword: str) -> list[dict[str, Any]]:
        """Simple keyword search across summary, context, and outcome."""
        keyword_lower = keyword.lower()
        results = []
        for ep in self._episodes:
            text = f"{ep.get('summary', '')} {ep.get('context', '')} {ep.get('outcome', '')}".lower()
            if keyword_lower in text:
                results.append(ep)
        return results

    def get_formatted(self, n: int = 5) -> str:
        """Return recent episodes as formatted text for prompt injection."""
        recent = self.get_recent(n)
        if not recent:
            return "No past episodes recorded."
        lines = []
        for ep in recent:
            ts = time.strftime("%Y-%m-%d %H:%M", time.localtime(ep["timestamp"]))
            lines.append(f"[{ts}] {ep['summary']}")
            if ep.get("outcome"):
                lines.append(f"  → Outcome: {ep['outcome']}")
        return "\n".join(lines)

    def delete_episode(self, episode_id: str) -> bool:
        """Delete a specific episode by ID (privacy support)."""
        before = len(self._episodes)
        self._episodes = [ep for ep in self._episodes if ep["id"] != episode_id]
        if len(self._episodes) < before:
            self._save()
            return True
        return False

    def clear(self) -> None:
        """Delete all episodes for the user."""
        self._episodes.clear()
        self._save()

    @property
    def count(self) -> int:
        return len(self._episodes)

    def __repr__(self) -> str:
        return f"EpisodicMemory(user={self.user_id}, episodes={self.count})"
