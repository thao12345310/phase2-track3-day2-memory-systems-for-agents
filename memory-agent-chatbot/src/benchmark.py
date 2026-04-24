#!/usr/bin/env python3
"""
Benchmark Runner — runs 10 multi-turn conversations comparing
no-memory vs with-memory agent performance.

Generates BENCHMARK.md with results.
"""

from __future__ import annotations

import json
import os
import sys
import time
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import Config
from src.agent import MemoryAgent
from src.token_budget import estimate_tokens


# ═══════════════════════════════════════════════════════════════════════════
# BENCHMARK CONVERSATIONS
# ═══════════════════════════════════════════════════════════════════════════

BENCHMARK_CONVERSATIONS: list[dict[str, Any]] = [
    # 1. Profile recall — name
    {
        "id": 1,
        "scenario": "Profile recall: remember user name after multiple turns",
        "category": "profile_recall",
        "setup_turns": [
            "Xin chào, mình tên là Linh.",
            "Mình đang học ngành Computer Science ở VinUni.",
            "Hôm nay trời đẹp quá nhỉ?",
            "Bạn gợi ý cho mình một cuốn sách về AI đi.",
            "Cảm ơn bạn nhé!",
            "À, mình muốn hỏi thêm về machine learning.",
        ],
        "test_turn": "Bạn còn nhớ tên mình không?",
        "expected_keyword": "Linh",
        "description": "Agent should remember user's name (Linh) after 6+ turns",
    },
    # 2. Profile recall — allergy conflict update
    {
        "id": 2,
        "scenario": "Conflict update: correct an allergy fact",
        "category": "conflict_update",
        "setup_turns": [
            "Mình bị dị ứng sữa bò.",
            "Gợi ý cho mình một số món ăn healthy đi.",
        ],
        "correction_turn": "À nhầm, mình dị ứng đậu nành chứ không phải sữa bò.",
        "test_turn": "Mình bị dị ứng gì nhỉ?",
        "expected_keyword": "đậu nành",
        "not_expected": "sữa bò",
        "description": "Agent should update allergy to đậu nành, not keep sữa bò",
    },
    # 3. Episodic recall — remember a debugging lesson
    {
        "id": 3,
        "scenario": "Episodic recall: remember a past debugging experience",
        "category": "episodic_recall",
        "setup_turns": [
            "Hôm qua mình gặp bug Docker container không kết nối được database.",
            "Cuối cùng mình phát hiện là phải dùng docker service name thay vì localhost.",
            "Vấn đề đã giải quyết rồi, cảm ơn!",
        ],
        "test_turn": "Lần trước mình gặp lỗi Docker, mình đã fix bằng cách nào?",
        "expected_keyword": "service name",
        "description": "Agent recalls the Docker debugging resolution from episodic memory",
    },
    # 4. Semantic retrieval — FAQ knowledge
    {
        "id": 4,
        "scenario": "Semantic retrieval: retrieve relevant knowledge chunk",
        "category": "semantic_retrieval",
        "preload_knowledge": [
            "LangGraph là một framework để xây dựng agent workflows dạng graph. Nó cho phép define state, nodes, và edges để tạo flow xử lý phức tạp.",
            "ChromaDB là một vector database dùng để lưu trữ và tìm kiếm embeddings. Nó hỗ trợ persistent storage và cosine similarity search.",
            "Redis là một in-memory data store thường dùng làm cache, message broker, và database. Trong AI systems, Redis thường dùng để lưu user profiles và session data.",
        ],
        "setup_turns": [],
        "test_turn": "LangGraph dùng để làm gì?",
        "expected_keyword": "graph",
        "description": "Agent retrieves the LangGraph knowledge chunk from semantic memory",
    },
    # 5. Profile recall — multiple facts
    {
        "id": 5,
        "scenario": "Profile recall: remember multiple user facts",
        "category": "profile_recall",
        "setup_turns": [
            "Mình tên Minh, 22 tuổi, sống ở Hà Nội.",
            "Mình thích lập trình Python và hay dùng VS Code.",
            "Ngôn ngữ yêu thích của mình là Python và Rust.",
        ],
        "test_turn": "Tóm tắt những gì bạn biết về mình đi.",
        "expected_keyword": "Minh",
        "description": "Agent recalls name, age, location, and programming preferences",
    },
    # 6. Conflict update — job change
    {
        "id": 6,
        "scenario": "Conflict update: user changes job",
        "category": "conflict_update",
        "setup_turns": [
            "Mình hiện đang làm intern ở FPT Software.",
            "Công việc khá thú vị, mình học được nhiều.",
        ],
        "correction_turn": "Mình vừa chuyển sang làm full-time ở VNG rồi, không còn ở FPT nữa.",
        "test_turn": "Mình đang làm ở đâu?",
        "expected_keyword": "VNG",
        "not_expected": "FPT",
        "description": "Agent updates workplace from FPT to VNG",
    },
    # 7. Episodic recall — coding task
    {
        "id": 7,
        "scenario": "Episodic recall: finished coding task",
        "category": "episodic_recall",
        "setup_turns": [
            "Mình vừa hoàn thành xong project FastAPI cho môn Web Development.",
            "Project có REST API, authentication với JWT, và database PostgreSQL.",
            "Mình deploy lên Railway thành công rồi.",
        ],
        "test_turn": "Mình đã deploy project lên đâu?",
        "expected_keyword": "Railway",
        "description": "Agent recalls the deployment platform from episodic memory",
    },
    # 8. Semantic retrieval — technical knowledge
    {
        "id": 8,
        "scenario": "Semantic retrieval: technical concept search",
        "category": "semantic_retrieval",
        "preload_knowledge": [
            "RAG (Retrieval-Augmented Generation) kết hợp retrieval và generation. Bước 1: index documents thành embeddings. Bước 2: khi có query, tìm top-k documents tương tự. Bước 3: đưa documents vào prompt của LLM để generate câu trả lời.",
            "Prompt Engineering là kỹ thuật thiết kế prompt để tối ưu output của LLM. Các kỹ thuật phổ biến: zero-shot, few-shot, chain-of-thought, và role-playing.",
            "Fine-tuning là quá trình train thêm một pre-trained model trên dataset cụ thể. LoRA và QLoRA là các phương pháp fine-tuning hiệu quả cho LLMs lớn.",
        ],
        "setup_turns": [],
        "test_turn": "RAG hoạt động như thế nào?",
        "expected_keyword": "retrieval",
        "description": "Agent retrieves the RAG knowledge chunk and explains it",
    },
    # 9. Token budget / trim test
    {
        "id": 9,
        "scenario": "Token budget: agent handles long conversation without overflow",
        "category": "trim_token_budget",
        "setup_turns": [
            "Mình tên Hoa.",
            "Giải thích cho mình về machine learning.",
            "Supervised learning là gì?",
            "Unsupervised learning là gì?",
            "Deep learning khác gì machine learning?",
            "CNN dùng để làm gì?",
            "RNN dùng để làm gì?",
            "Transformer architecture hoạt động như thế nào?",
            "BERT và GPT khác nhau như nào?",
            "So sánh fine-tuning và prompt engineering.",
            "RAG là gì?",
            "LangChain dùng để làm gì?",
        ],
        "test_turn": "Bạn còn nhớ tên mình không?",
        "expected_keyword": "Hoa",
        "description": "After 12+ turns, agent still recalls user's name within token budget",
    },
    # 10. Combined memory test
    {
        "id": 10,
        "scenario": "Combined: profile + episodes + semantic in one response",
        "category": "combined",
        "preload_knowledge": [
            "PostgreSQL hỗ trợ JSON columns, full-text search, và nhiều advanced features. Nó là lựa chọn tốt cho applications cần ACID compliance.",
        ],
        "setup_turns": [
            "Mình tên Đức, đang làm backend developer.",
            "Hôm qua mình đã migrate database từ MySQL sang PostgreSQL thành công.",
        ],
        "test_turn": "Với kinh nghiệm migrate database hôm qua và vai trò backend developer, bạn gợi ý mình nên tìm hiểu thêm gì về PostgreSQL?",
        "expected_keyword": "PostgreSQL",
        "description": "Agent combines profile (backend dev), episode (migration), and semantic (PostgreSQL docs) for a contextual answer",
    },
]


# ═══════════════════════════════════════════════════════════════════════════
# BENCHMARK RUNNER
# ═══════════════════════════════════════════════════════════════════════════

class BenchmarkRunner:
    """Runs all benchmark conversations and generates the report."""

    def __init__(self):
        Config.validate()
        self.results: list[dict[str, Any]] = []

    def run_conversation(self, conv: dict[str, Any], use_memory: bool) -> dict[str, Any]:
        """Run a single benchmark conversation and return results."""
        agent = MemoryAgent(
            user_id=f"bench_{conv['id']}_{use_memory}",
            use_memory=use_memory,
        )

        # Preload semantic knowledge if specified
        if conv.get("preload_knowledge"):
            for doc in conv["preload_knowledge"]:
                agent.semantic.add_document(doc)

        # Run setup turns
        responses = []
        for turn in conv.get("setup_turns", []):
            resp = agent.chat(turn)
            responses.append({"role": "setup", "input": turn, "output": resp})

        # Run correction turn if present
        if conv.get("correction_turn"):
            resp = agent.chat(conv["correction_turn"])
            responses.append({"role": "correction", "input": conv["correction_turn"], "output": resp})

        # Run test turn
        test_resp = agent.chat(conv["test_turn"])
        responses.append({"role": "test", "input": conv["test_turn"], "output": test_resp})

        # Evaluate
        expected = conv["expected_keyword"].lower()
        passed = expected in test_resp.lower()

        # Check not_expected if present
        if passed and conv.get("not_expected"):
            not_exp = conv["not_expected"].lower()
            if not_exp in test_resp.lower():
                passed = False

        # Token estimate
        total_tokens = sum(estimate_tokens(r["output"]) for r in responses)

        return {
            "test_response": test_resp,
            "passed": passed,
            "total_tokens": total_tokens,
            "responses": responses,
            "memory_status": agent.get_memory_status() if use_memory else None,
        }

    def run_all(self) -> list[dict[str, Any]]:
        """Run all benchmark conversations."""
        print("=" * 60)
        print("🧪 Memory Agent Benchmark — 10 Multi-Turn Conversations")
        print("=" * 60)

        for conv in BENCHMARK_CONVERSATIONS:
            print(f"\n━━━ Test #{conv['id']}: {conv['scenario'][:50]}... ━━━")

            # Run WITHOUT memory
            print("  ▸ Running no-memory...")
            try:
                no_mem = self.run_conversation(conv, use_memory=False)
            except Exception as e:
                no_mem = {"test_response": f"ERROR: {e}", "passed": False, "total_tokens": 0}

            # Run WITH memory
            print("  ▸ Running with-memory...")
            try:
                with_mem = self.run_conversation(conv, use_memory=True)
            except Exception as e:
                with_mem = {"test_response": f"ERROR: {e}", "passed": False, "total_tokens": 0}

            result = {
                "id": conv["id"],
                "scenario": conv["scenario"],
                "category": conv["category"],
                "description": conv["description"],
                "expected": conv["expected_keyword"],
                "no_memory": no_mem,
                "with_memory": with_mem,
            }
            self.results.append(result)

            status = "✅ PASS" if with_mem["passed"] else "❌ FAIL"
            print(f"  {status} — expected '{conv['expected_keyword']}'")
            print(f"    no-mem: {no_mem['test_response'][:80]}...")
            print(f"    w-mem : {with_mem['test_response'][:80]}...")

        return self.results

    def generate_report(self) -> str:
        """Generate BENCHMARK.md report."""
        lines = [
            "# BENCHMARK.md — Lab 17: Multi-Memory Agent Benchmark",
            "",
            "## Overview",
            "",
            "Benchmark comparing **no-memory** vs **with-memory** agent across 10 multi-turn",
            "conversations covering all required test categories:",
            "",
            "- **Profile recall** (2 tests)",
            "- **Conflict update** (2 tests)",
            "- **Episodic recall** (2 tests)",
            "- **Semantic retrieval** (2 tests)",
            "- **Token budget / trim** (1 test)",
            "- **Combined memory** (1 test)",
            "",
            "---",
            "",
            "## Results Summary",
            "",
            "| # | Scenario | Category | No-Memory Result | With-Memory Result | Pass? |",
            "|---|----------|----------|------------------|---------------------|-------|",
        ]

        total_pass = 0
        for r in self.results:
            no_mem_short = r["no_memory"]["test_response"][:60].replace("|", "\\|").replace("\n", " ")
            with_mem_short = r["with_memory"]["test_response"][:60].replace("|", "\\|").replace("\n", " ")
            passed = "✅ Pass" if r["with_memory"]["passed"] else "❌ Fail"
            if r["with_memory"]["passed"]:
                total_pass += 1

            lines.append(
                f"| {r['id']} | {r['scenario'][:50]} | {r['category']} | "
                f"{no_mem_short} | {with_mem_short} | {passed} |"
            )

        lines.extend([
            "",
            f"**Score: {total_pass}/{len(self.results)} tests passed**",
            "",
            "---",
            "",
            "## Detailed Results",
            "",
        ])

        for r in self.results:
            lines.extend([
                f"### Test #{r['id']}: {r['scenario']}",
                "",
                f"**Category:** {r['category']}",
                f"**Description:** {r['description']}",
                f"**Expected keyword:** `{r['expected']}`",
                "",
                f"**No-memory response:**",
                f"> {r['no_memory']['test_response'][:200]}",
                "",
                f"**With-memory response:**",
                f"> {r['with_memory']['test_response'][:200]}",
                "",
                f"**Result:** {'✅ PASS' if r['with_memory']['passed'] else '❌ FAIL'}",
                "",
                f"**Token usage (with-memory):** ~{r['with_memory']['total_tokens']} tokens",
                "",
            ])

            # Show memory status for with-memory runs
            if r["with_memory"].get("memory_status"):
                ms = r["with_memory"]["memory_status"]
                lines.extend([
                    "**Memory status after test:**",
                    f"- Short-term: {ms['short_term']['messages']} messages",
                    f"- Profile facts: {json.dumps(ms['long_term_profile']['data'], ensure_ascii=False)}",
                    f"- Episodes: {ms['episodic']['episodes']} recorded",
                    f"- Semantic docs: {ms['semantic']['documents']}",
                    "",
                ])

            lines.append("---")
            lines.append("")

        # Token budget analysis
        lines.extend([
            "## Token Budget Analysis",
            "",
            "| # | Scenario | Total Tokens (with-memory) |",
            "|---|----------|---------------------------|",
        ])

        for r in self.results:
            lines.append(
                f"| {r['id']} | {r['scenario'][:40]} | ~{r['with_memory']['total_tokens']} |"
            )

        lines.extend([
            "",
            f"**Memory token budget:** {Config.MEMORY_TOKEN_BUDGET} tokens",
            f"**Short-term window:** {Config.SHORT_TERM_WINDOW} messages",
            "",
        ])

        return "\n".join(lines)


def main():
    runner = BenchmarkRunner()
    results = runner.run_all()

    # Generate report
    report = runner.generate_report()
    report_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "BENCHMARK.md",
    )
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    # Save raw results
    results_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data",
        "benchmark_results.json",
    )
    os.makedirs(os.path.dirname(results_path), exist_ok=True)
    with open(results_path, "w", encoding="utf-8") as f:
        # Serialize without non-serializable objects
        serializable = []
        for r in results:
            sr = {k: v for k, v in r.items()}
            serializable.append(sr)
        json.dump(serializable, f, ensure_ascii=False, indent=2, default=str)

    total_pass = sum(1 for r in results if r["with_memory"]["passed"])
    print(f"\n{'=' * 60}")
    print(f"📊 Benchmark complete: {total_pass}/{len(results)} tests passed")
    print(f"📄 Report saved to: {report_path}")
    print(f"📦 Raw results saved to: {results_path}")


if __name__ == "__main__":
    main()
