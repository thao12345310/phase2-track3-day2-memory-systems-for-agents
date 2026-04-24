#!/usr/bin/env python3
"""
Interactive CLI chat interface for the Memory Agent.
Uses Rich for a polished terminal experience.
"""

from __future__ import annotations

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich import box

from src.config import Config
from src.agent import MemoryAgent


console = Console()


def print_welcome():
    """Print welcome banner."""
    console.print(Panel(
        "[bold cyan]🧠 Memory Agent Chatbot[/bold cyan]\n"
        "[dim]Lab 17 — Multi-Memory Agent with LangGraph[/dim]\n\n"
        "[green]Commands:[/green]\n"
        "  /memory  — Show memory status\n"
        "  /clear   — Reset all memory\n"
        "  /quit    — Exit\n",
        title="Welcome",
        border_style="bright_blue",
        box=box.DOUBLE,
    ))


def print_memory_status(agent: MemoryAgent):
    """Display memory status table."""
    status = agent.get_memory_status()

    table = Table(title="🧠 Memory Status", box=box.ROUNDED, border_style="cyan")
    table.add_column("Backend", style="bold")
    table.add_column("Details", style="green")

    # Short-term
    st = status["short_term"]
    table.add_row(
        "📝 Short-Term",
        f"{st['messages']}/{st['window']} messages in window",
    )

    # Long-term profile
    lt = status["long_term_profile"]
    facts_str = ", ".join(f"{k}={v}" for k, v in lt["data"].items()) if lt["data"] else "empty"
    table.add_row(
        "👤 Long-Term Profile",
        f"{lt['facts']} facts: {facts_str[:80]}",
    )

    # Episodic
    ep = status["episodic"]
    table.add_row(
        "📖 Episodic",
        f"{ep['episodes']} episodes recorded",
    )

    # Semantic
    sem = status["semantic"]
    table.add_row(
        "🔍 Semantic",
        f"{sem['documents']} documents indexed",
    )

    console.print(table)


def main():
    """Main chat loop."""
    Config.validate()
    print_welcome()

    console.print("[dim]Initializing agent...[/dim]")
    agent = MemoryAgent(user_id="interactive_user", use_memory=True)
    console.print("[green]✓ Agent ready![/green]\n")

    while True:
        try:
            user_input = console.input("[bold blue]You:[/bold blue] ").strip()

            if not user_input:
                continue

            if user_input.lower() in ("/quit", "/exit", "quit", "exit"):
                console.print("[dim]Goodbye! 👋[/dim]")
                break

            if user_input.lower() == "/memory":
                print_memory_status(agent)
                continue

            if user_input.lower() == "/clear":
                agent.reset_all_memory()
                console.print("[yellow]🗑️ All memory cleared.[/yellow]")
                continue

            # Process through the memory agent pipeline
            with console.status("[cyan]Thinking...[/cyan]"):
                response = agent.chat(user_input)

            console.print(f"\n[bold green]Assistant:[/bold green] {response}\n")

        except KeyboardInterrupt:
            console.print("\n[dim]Goodbye! 👋[/dim]")
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


if __name__ == "__main__":
    main()
