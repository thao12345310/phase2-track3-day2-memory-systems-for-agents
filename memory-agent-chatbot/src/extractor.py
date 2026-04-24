"""
LLM-based fact extractor — uses the LLM to extract profile facts and
episodic summaries from user messages.
"""

from __future__ import annotations

import json
import re
from typing import Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from src.config import Config


EXTRACTOR_SYSTEM = """You are a memory extraction assistant. Analyze the user message and extract:

1. **profile_facts**: Key-value pairs about the user (name, age, job, preferences, allergies, location, etc.)
   - If the user CORRECTS a previous fact, include the corrected version with "corrected": true
   - Format: [{"key": "...", "value": "...", "corrected": false}]

2. **episode**: If the conversation contains a completed task, a decision, or a notable event, summarize it.
   - Format: {"summary": "...", "outcome": "...", "tags": ["..."]}
   - Return null if no episode is worth recording.

3. **knowledge**: If the user shares factual knowledge (not personal), extract it for semantic memory.
   - Format: "..." (a single text chunk) or null

Respond ONLY with valid JSON:
{
  "profile_facts": [...],
  "episode": {...} or null,
  "knowledge": "..." or null
}"""


def extract_memory_from_message(
    user_message: str,
    assistant_response: str,
    conversation_context: str = "",
) -> dict[str, Any]:
    """
    Use the LLM to extract structured memory data from a conversation turn.

    Returns:
        {
            "profile_facts": [{"key": str, "value": str, "corrected": bool}],
            "episode": {"summary": str, "outcome": str, "tags": list} | None,
            "knowledge": str | None,
        }
    """
    try:
        llm = ChatOpenAI(
            model=Config.MODEL_NAME,
            temperature=0,
            api_key=Config.OPENAI_API_KEY,
            max_tokens=500,
        )

        prompt = f"""Context of recent conversation:
{conversation_context[-500:] if conversation_context else 'N/A'}

Latest user message: {user_message}
Assistant's response: {assistant_response}

Extract memory items from this exchange."""

        response = llm.invoke([
            SystemMessage(content=EXTRACTOR_SYSTEM),
            HumanMessage(content=prompt),
        ])

        # Parse JSON from response
        content = response.content.strip()
        # Try to find JSON in the response
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            return json.loads(json_match.group())

        return {"profile_facts": [], "episode": None, "knowledge": None}

    except Exception as e:
        print(f"[Extractor] Error: {e}")
        return {"profile_facts": [], "episode": None, "knowledge": None}
