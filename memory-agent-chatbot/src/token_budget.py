"""
Token budget utilities — estimate token counts and trim content.
"""

from __future__ import annotations

import re


def estimate_tokens(text: str) -> int:
    """
    Estimate token count using tiktoken if available,
    otherwise fall back to word-count heuristic (1 token ≈ 0.75 words).
    """
    try:
        import tiktoken
        enc = tiktoken.encoding_for_model("gpt-4o-mini")
        return len(enc.encode(text))
    except Exception:
        # Fallback: ~4 chars per token for English, ~2 chars for Vietnamese
        return max(len(text) // 3, len(text.split()))


def trim_to_budget(text: str, budget: int) -> str:
    """
    Trim text to fit within a token budget.
    Keeps the most recent content (trims from the beginning).
    """
    current = estimate_tokens(text)
    if current <= budget:
        return text

    # Split by lines and trim from top
    lines = text.split("\n")
    while lines and estimate_tokens("\n".join(lines)) > budget:
        lines.pop(0)
    return "\n".join(lines)


def allocate_budget(total: int) -> dict[str, int]:
    """
    Allocate a token budget across memory sections.
    
    Distribution:
      - recent conversation: 40%
      - profile: 15%
      - episodic: 20%
      - semantic: 25%
    """
    return {
        "recent": int(total * 0.40),
        "profile": int(total * 0.15),
        "episodic": int(total * 0.20),
        "semantic": int(total * 0.25),
    }
