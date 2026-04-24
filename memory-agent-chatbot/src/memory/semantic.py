"""
Semantic Memory — Vector-search knowledge store using ChromaDB.

Stores and retrieves knowledge chunks (documents, FAQs, past conversations)
using embedding-based semantic similarity search.
Falls back to keyword search if ChromaDB is unavailable.
"""

from __future__ import annotations

import hashlib
import os
import uuid
from typing import Any, Optional

from src.config import Config


class SemanticMemory:
    """
    Vector store backed by ChromaDB for semantic retrieval.

    Falls back to simple keyword-search if chromadb import fails.
    """

    def __init__(self, collection_name: str = "agent_knowledge") -> None:
        self.collection_name = collection_name
        self._use_chroma = False
        self._collection = None
        self._fallback_docs: list[dict[str, Any]] = []

        self._init_chroma()

    # ── ChromaDB backend ─────────────────────────────────────────────────

    def _init_chroma(self) -> None:
        """Try to initialize ChromaDB; fall back to keyword search."""
        try:
            import chromadb
            from chromadb.config import Settings

            persist_dir = Config.CHROMA_DIR
            os.makedirs(persist_dir, exist_ok=True)

            self._client = chromadb.PersistentClient(path=persist_dir)
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            self._use_chroma = True
        except Exception as e:
            print(f"[SemanticMemory] ChromaDB unavailable ({e}), using keyword fallback.")
            self._use_chroma = False

    # ── Public API ───────────────────────────────────────────────────────

    def add_document(
        self,
        text: str,
        metadata: dict[str, Any] | None = None,
        doc_id: str | None = None,
    ) -> str:
        """
        Add a document/chunk to the semantic store.
        Returns the document ID.
        """
        if doc_id is None:
            doc_id = hashlib.md5(text.encode()).hexdigest()[:12]

        meta = metadata or {}

        if self._use_chroma and self._collection is not None:
            self._collection.upsert(
                documents=[text],
                metadatas=[meta],
                ids=[doc_id],
            )
        else:
            self._fallback_docs.append(
                {"id": doc_id, "text": text, "metadata": meta}
            )

        return doc_id

    def search(self, query: str, top_k: int | None = None) -> list[dict[str, Any]]:
        """
        Retrieve the top-k most relevant documents for the query.

        Returns list of { "text": str, "metadata": dict, "score": float }.
        """
        k = top_k or Config.SEMANTIC_TOP_K

        if self._use_chroma and self._collection is not None:
            results = self._collection.query(
                query_texts=[query],
                n_results=k,
            )
            hits = []
            if results and results["documents"]:
                for i, doc in enumerate(results["documents"][0]):
                    hit = {
                        "text": doc,
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "score": 1.0 - (results["distances"][0][i] if results["distances"] else 0),
                    }
                    hits.append(hit)
            return hits
        else:
            return self._keyword_search(query, k)

    def _keyword_search(self, query: str, top_k: int) -> list[dict[str, Any]]:
        """Fallback keyword search when ChromaDB is not available."""
        query_terms = query.lower().split()
        scored = []
        for doc in self._fallback_docs:
            text_lower = doc["text"].lower()
            score = sum(1 for term in query_terms if term in text_lower) / max(len(query_terms), 1)
            if score > 0:
                scored.append({"text": doc["text"], "metadata": doc["metadata"], "score": score})
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    def get_formatted(self, query: str, top_k: int | None = None) -> str:
        """Return search results as formatted text for prompt injection."""
        results = self.search(query, top_k)
        if not results:
            return "No relevant knowledge found."
        lines = []
        for i, hit in enumerate(results, 1):
            lines.append(f"[{i}] (relevance: {hit['score']:.2f}) {hit['text']}")
        return "\n".join(lines)

    def clear(self) -> None:
        """Remove all documents."""
        if self._use_chroma and self._collection is not None:
            # Delete and recreate collection
            self._client.delete_collection(self.collection_name)
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        self._fallback_docs.clear()

    @property
    def doc_count(self) -> int:
        if self._use_chroma and self._collection is not None:
            return self._collection.count()
        return len(self._fallback_docs)

    def __repr__(self) -> str:
        backend = "ChromaDB" if self._use_chroma else "keyword-fallback"
        return f"SemanticMemory(backend={backend}, docs={self.doc_count})"
