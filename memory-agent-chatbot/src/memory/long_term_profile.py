"""
Long-Term Profile Memory — Persistent key/value user profile store.

Stores structured facts about the user (name, preferences, allergies, etc.)
with conflict-aware update logic: when a fact is corrected, the old value is
replaced and an audit trail is kept.

Backends:
  - JSON file (default / fallback)
  - Redis (optional, when REDIS_URL is configured)
"""

from __future__ import annotations

import json
import os
import time
from typing import Any, Optional

from src.config import Config


class LongTermProfileMemory:
    """
    Key/value store for user profile facts with conflict handling.

    Each fact is stored as:
        key → { "value": ..., "updated_at": ..., "history": [...] }
    """

    def __init__(self, user_id: str = "default", use_redis: bool = False) -> None:
        self.user_id = user_id
        self._use_redis = use_redis and bool(Config.REDIS_URL)
        self._redis_client = None
        self._profile: dict[str, dict[str, Any]] = {}

        if self._use_redis:
            self._init_redis()
        else:
            self._load_from_file()

    # ── Redis backend ────────────────────────────────────────────────────

    def _init_redis(self) -> None:
        """Initialize Redis connection and load existing profile."""
        try:
            import redis
            self._redis_client = redis.from_url(Config.REDIS_URL, decode_responses=True)
            self._redis_client.ping()
            raw = self._redis_client.get(f"profile:{self.user_id}")
            if raw:
                self._profile = json.loads(raw)
        except Exception as e:
            print(f"[LongTermProfile] Redis unavailable ({e}), falling back to JSON.")
            self._use_redis = False
            self._load_from_file()

    # ── JSON file backend ────────────────────────────────────────────────

    def _load_from_file(self) -> None:
        """Load profile from JSON file."""
        path = Config.PROFILE_PATH
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                all_profiles = json.load(f)
                self._profile = all_profiles.get(self.user_id, {})

    def _save_to_file(self) -> None:
        """Persist profile to JSON file."""
        path = Config.PROFILE_PATH
        os.makedirs(os.path.dirname(path), exist_ok=True)
        all_profiles = {}
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                all_profiles = json.load(f)
        all_profiles[self.user_id] = self._profile
        with open(path, "w", encoding="utf-8") as f:
            json.dump(all_profiles, f, ensure_ascii=False, indent=2)

    # ── Persistence dispatch ─────────────────────────────────────────────

    def _persist(self) -> None:
        """Save to whichever backend is active."""
        if self._use_redis and self._redis_client:
            self._redis_client.set(
                f"profile:{self.user_id}", json.dumps(self._profile, ensure_ascii=False)
            )
        else:
            self._save_to_file()

    # ── Public API ───────────────────────────────────────────────────────

    def update_fact(self, key: str, value: Any) -> dict[str, Any]:
        """
        Set or update a profile fact with conflict handling.

        If *key* already exists with a different value, the old value is
        archived in `history` and the new value takes precedence.

        Returns the fact record.
        """
        key = key.strip().lower()
        now = time.time()

        if key in self._profile:
            existing = self._profile[key]
            old_value = existing["value"]
            if old_value != value:
                # Archive the old value
                existing.setdefault("history", [])
                existing["history"].append(
                    {"value": old_value, "replaced_at": now}
                )
                existing["value"] = value
                existing["updated_at"] = now
        else:
            self._profile[key] = {
                "value": value,
                "updated_at": now,
                "history": [],
            }

        self._persist()
        return self._profile[key]

    def get_fact(self, key: str) -> Optional[Any]:
        """Retrieve the current value for a fact, or None."""
        key = key.strip().lower()
        record = self._profile.get(key)
        return record["value"] if record else None

    def get_all_facts(self) -> dict[str, Any]:
        """Return a simplified view: { key: value }."""
        return {k: v["value"] for k, v in self._profile.items()}

    def get_profile_formatted(self) -> str:
        """Return profile facts as a formatted string for prompt injection."""
        if not self._profile:
            return "No profile information available."
        lines = []
        for key, record in self._profile.items():
            lines.append(f"- {key}: {record['value']}")
        return "\n".join(lines)

    def delete_fact(self, key: str) -> bool:
        """Delete a specific fact (supports privacy/deletion requests)."""
        key = key.strip().lower()
        if key in self._profile:
            del self._profile[key]
            self._persist()
            return True
        return False

    def clear(self) -> None:
        """Delete all profile facts for the user."""
        self._profile.clear()
        self._persist()

    def __repr__(self) -> str:
        return f"LongTermProfileMemory(user={self.user_id}, facts={len(self._profile)})"
