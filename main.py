"""CLI entrypoint for the deep research agent.

Usage:
    uv run python main.py "your research question"
    uv run python main.py  # interactive mode
"""

import sys
import uuid

from rich.console import Console
from rich.panel import Panel

from agent import agent
from utils import format_messages

console = Console()


def run_research(question: str) -> None:
    """Run a research query and display results."""
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    console.print(Panel(question, title="[bold blue]Research Question[/bold blue]", border_style="blue"))

    result = agent.invoke(
        {"messages": [{"role": "user", "content": question}]},
        config=config,
    )

    messages = result.get("messages", [])
    format_messages(messages[-3:])  # Show last few messages

    # Print final report if written to filesystem
    files = result.get("files", {})
    if "/final_report.md" in files:
        report = files["/final_report.md"].get("content", "")
        console.print(Panel(report, title="[bold green]Final Report[/bold green]", border_style="green"))


def main() -> None:
    """Main entry point."""
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
        run_research(question)
    else:
        console.print("[bold]Deep Research Agent[/bold] — Enter your question (Ctrl+C to exit)\n")
        while True:
            try:
                question = input("Research: ").strip()
                if question:
                    run_research(question)
                    print()
            except (KeyboardInterrupt, EOFError):
                console.print("\n[dim]Goodbye.[/dim]")
                break


if __name__ == "__main__":
    main()
