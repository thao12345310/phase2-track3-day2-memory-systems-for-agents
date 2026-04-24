"""
Configuration management for the Memory Agent Chatbot.
Loads settings from environment variables with sensible defaults.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Centralized configuration for all memory and agent settings."""

    # ── LLM ──────────────────────────────────────────────────────────────
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "gpt-4o-mini")
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.7"))
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "2048"))

    # ── Redis (optional, for long-term profile) ──────────────────────────
    REDIS_URL: str = os.getenv("REDIS_URL", "")

    # ── Memory parameters ────────────────────────────────────────────────
    SHORT_TERM_WINDOW: int = int(os.getenv("SHORT_TERM_WINDOW", "10"))
    MEMORY_TOKEN_BUDGET: int = int(os.getenv("MEMORY_TOKEN_BUDGET", "3000"))
    SEMANTIC_TOP_K: int = int(os.getenv("SEMANTIC_TOP_K", "3"))

    # ── Paths ────────────────────────────────────────────────────────────
    DATA_DIR: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    PROFILE_PATH: str = os.path.join(DATA_DIR, "user_profiles.json")
    EPISODES_PATH: str = os.path.join(DATA_DIR, "episodes.json")
    CHROMA_DIR: str = os.path.join(DATA_DIR, "chroma_db")

    @classmethod
    def validate(cls) -> bool:
        """Check that essential configuration is present."""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required. Set it in .env or environment.")
        return True
