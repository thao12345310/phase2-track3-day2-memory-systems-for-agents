"""
LangGraph-based Memory Agent — core graph with state, router, and prompt injection.

Architecture:
    ┌─────────────┐
    │  User Input  │
    └──────┬──────┘
           ▼
    ┌──────────────┐
    │  Retrieve     │  ← Gathers from 4 memory backends
    │  Memory       │
    └──────┬───────┘
           ▼
    ┌──────────────┐
    │  Build Prompt │  ← Injects memory sections into prompt
    │  (Router)     │
    └──────┬───────┘
           ▼
    ┌──────────────┐
    │  LLM Call     │
    └──────┬───────┘
           ▼
    ┌──────────────┐
    │  Save Memory  │  ← Extracts & saves facts, episodes, knowledge
    └──────┬───────┘
           ▼
    ┌──────────────┐
    │  Response     │
    └──────────────┘
"""

from __future__ import annotations

from typing import Any, TypedDict, Annotated
import operator

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from src.config import Config
from src.memory import ShortTermMemory, LongTermProfileMemory, EpisodicMemory, SemanticMemory
from src.token_budget import estimate_tokens, trim_to_budget, allocate_budget
from src.extractor import extract_memory_from_message


# ═══════════════════════════════════════════════════════════════════════════
# 1. STATE DEFINITION
# ═══════════════════════════════════════════════════════════════════════════

class MemoryState(TypedDict):
    """LangGraph state carrying all memory data through the pipeline."""

    messages: list                      # Raw conversation messages
    user_input: str                     # Current user input
    user_profile: dict                  # Assembled profile facts
    episodes: list[dict]                # Recent episodic memories
    semantic_hits: list[str]            # Relevant semantic search results
    recent_conversation: str            # Formatted recent messages
    assembled_prompt: list              # Final prompt with injected memory
    assistant_response: str             # LLM output
    memory_budget: int                  # Total token budget for memory
    token_usage: dict                   # Token usage tracking


# ═══════════════════════════════════════════════════════════════════════════
# 2. MEMORY AGENT CLASS
# ═══════════════════════════════════════════════════════════════════════════

class MemoryAgent:
    """
    Multi-memory agent built on LangGraph.

    Manages four memory backends and orchestrates retrieve → inject → respond → save.
    """

    def __init__(self, user_id: str = "default", use_memory: bool = True) -> None:
        self.user_id = user_id
        self.use_memory = use_memory

        # Initialize LLM
        self.llm = ChatOpenAI(
            model=Config.MODEL_NAME,
            temperature=Config.TEMPERATURE,
            api_key=Config.OPENAI_API_KEY,
            max_tokens=Config.MAX_TOKENS,
        )

        # Initialize 4 memory backends
        self.short_term = ShortTermMemory(window_size=Config.SHORT_TERM_WINDOW)
        self.long_term = LongTermProfileMemory(user_id=user_id)
        self.episodic = EpisodicMemory(user_id=user_id)
        self.semantic = SemanticMemory()

        # Build the LangGraph
        self.graph = self._build_graph()

    # ── Graph construction ───────────────────────────────────────────────

    def _build_graph(self) -> Any:
        """Build the LangGraph state machine."""
        workflow = StateGraph(MemoryState)

        # Add nodes
        workflow.add_node("retrieve_memory", self._retrieve_memory)
        workflow.add_node("build_prompt", self._build_prompt)
        workflow.add_node("call_llm", self._call_llm)
        workflow.add_node("save_memory", self._save_memory)

        # Define edges
        workflow.set_entry_point("retrieve_memory")
        workflow.add_edge("retrieve_memory", "build_prompt")
        workflow.add_edge("build_prompt", "call_llm")
        workflow.add_edge("call_llm", "save_memory")
        workflow.add_edge("save_memory", END)

        return workflow.compile()

    # ── Node: Retrieve Memory ────────────────────────────────────────────

    def _retrieve_memory(self, state: MemoryState) -> dict:
        """
        Router node: gather relevant data from all 4 memory backends
        based on the current user input.
        """
        user_input = state["user_input"]
        budget = allocate_budget(state.get("memory_budget", Config.MEMORY_TOKEN_BUDGET))

        if not self.use_memory:
            return {
                "user_profile": {},
                "episodes": [],
                "semantic_hits": [],
                "recent_conversation": "",
            }

        # 1. Short-term: recent conversation window
        recent = self.short_term.get_formatted()
        recent = trim_to_budget(recent, budget["recent"])

        # 2. Long-term profile: user facts
        profile = self.long_term.get_all_facts()

        # 3. Episodic: recent events + keyword search
        recent_episodes = self.episodic.get_recent(3)
        keyword_episodes = self.episodic.search_by_keyword(user_input)[:2]
        # Merge and deduplicate
        seen_ids = set()
        all_episodes = []
        for ep in recent_episodes + keyword_episodes:
            if ep["id"] not in seen_ids:
                seen_ids.add(ep["id"])
                all_episodes.append(ep)

        # 4. Semantic: vector search
        semantic_hits = self.semantic.search(user_input, top_k=Config.SEMANTIC_TOP_K)
        semantic_texts = [hit["text"] for hit in semantic_hits]

        return {
            "user_profile": profile,
            "episodes": all_episodes,
            "semantic_hits": semantic_texts,
            "recent_conversation": recent,
        }

    # ── Node: Build Prompt ───────────────────────────────────────────────

    def _build_prompt(self, state: MemoryState) -> dict:
        """
        Assemble the final prompt with memory sections injected.
        Each memory type gets its own clearly labeled section.
        """
        budget = allocate_budget(state.get("memory_budget", Config.MEMORY_TOKEN_BUDGET))

        # Build system prompt with memory sections
        system_parts = [
            "You are a helpful, friendly AI assistant with persistent memory.",
            "You remember information about the user from past conversations.",
            "Always use the memory context below when relevant to the conversation.",
            "",
        ]

        if self.use_memory:
            # ── Profile section ──
            profile = state.get("user_profile", {})
            if profile:
                system_parts.append("═══ USER PROFILE ═══")
                for key, value in profile.items():
                    system_parts.append(f"• {key}: {value}")
                system_parts.append("")

            # ── Episodic section ──
            episodes = state.get("episodes", [])
            if episodes:
                system_parts.append("═══ PAST EPISODES ═══")
                for ep in episodes[:5]:
                    system_parts.append(f"• {ep.get('summary', 'N/A')}")
                    if ep.get("outcome"):
                        system_parts.append(f"  → {ep['outcome']}")
                system_parts.append("")

            # ── Semantic section ──
            semantic_hits = state.get("semantic_hits", [])
            if semantic_hits:
                system_parts.append("═══ RELEVANT KNOWLEDGE ═══")
                for i, hit in enumerate(semantic_hits, 1):
                    trimmed = trim_to_budget(hit, budget["semantic"] // max(len(semantic_hits), 1))
                    system_parts.append(f"[{i}] {trimmed}")
                system_parts.append("")

            # ── Recent conversation section ──
            recent = state.get("recent_conversation", "")
            if recent:
                system_parts.append("═══ RECENT CONVERSATION ═══")
                system_parts.append(recent)
                system_parts.append("")

        system_prompt = "\n".join(system_parts)
        system_prompt = trim_to_budget(system_prompt, Config.MEMORY_TOKEN_BUDGET)

        # Assemble final messages
        assembled = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=state["user_input"]),
        ]

        token_usage = {
            "system_prompt_tokens": estimate_tokens(system_prompt),
            "user_input_tokens": estimate_tokens(state["user_input"]),
        }

        return {
            "assembled_prompt": assembled,
            "token_usage": token_usage,
        }

    # ── Node: Call LLM ───────────────────────────────────────────────────

    def _call_llm(self, state: MemoryState) -> dict:
        """Invoke the LLM with the assembled prompt."""
        response = self.llm.invoke(state["assembled_prompt"])
        return {"assistant_response": response.content}

    # ── Node: Save Memory ────────────────────────────────────────────────

    def _save_memory(self, state: MemoryState) -> dict:
        """
        Extract facts/episodes from the conversation turn and save
        them to the appropriate memory backends.
        """
        user_input = state["user_input"]
        assistant_response = state["assistant_response"]

        # Always update short-term
        self.short_term.add_message("user", user_input)
        self.short_term.add_message("assistant", assistant_response)

        if not self.use_memory:
            return {}

        # Use LLM extractor to identify saveable memory
        context = state.get("recent_conversation", "")
        extracted = extract_memory_from_message(user_input, assistant_response, context)

        # Save profile facts
        for fact in extracted.get("profile_facts", []):
            if fact.get("key") and fact.get("value"):
                self.long_term.update_fact(fact["key"], fact["value"])

        # Save episodic memory
        episode = extracted.get("episode")
        if episode and episode.get("summary"):
            self.episodic.add_episode(
                summary=episode["summary"],
                outcome=episode.get("outcome", ""),
                tags=episode.get("tags", []),
                context=user_input[:200],
            )

        # Save knowledge to semantic memory
        knowledge = extracted.get("knowledge")
        if knowledge:
            self.semantic.add_document(knowledge, metadata={"source": "conversation"})

        return {}

    # ── Public API ───────────────────────────────────────────────────────

    def chat(self, user_input: str) -> str:
        """
        Process a user message through the full memory pipeline.
        Returns the assistant's response.
        """
        initial_state: MemoryState = {
            "messages": [],
            "user_input": user_input,
            "user_profile": {},
            "episodes": [],
            "semantic_hits": [],
            "recent_conversation": "",
            "assembled_prompt": [],
            "assistant_response": "",
            "memory_budget": Config.MEMORY_TOKEN_BUDGET,
            "token_usage": {},
        }

        result = self.graph.invoke(initial_state)
        return result["assistant_response"]

    def get_memory_status(self) -> dict:
        """Return a summary of all memory backends."""
        return {
            "short_term": {
                "messages": self.short_term.size,
                "window": self.short_term.window_size,
            },
            "long_term_profile": {
                "facts": len(self.long_term.get_all_facts()),
                "data": self.long_term.get_all_facts(),
            },
            "episodic": {
                "episodes": self.episodic.count,
                "recent": self.episodic.get_recent(3),
            },
            "semantic": {
                "documents": self.semantic.doc_count,
            },
        }

    def reset_all_memory(self) -> None:
        """Clear all memory backends (for benchmarking / privacy)."""
        self.short_term.clear()
        self.long_term.clear()
        self.episodic.clear()
        self.semantic.clear()
