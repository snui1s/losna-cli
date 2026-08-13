"""
diff_utils.py — Git diff and session memory visualization helpers.

Provides functions to extract git diffs for tracked and untracked files,
render syntax-highlighted diffs on the terminal using Rich, and display
structured session memory breakdowns.
"""

import os
import subprocess
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from . import db

console = Console()


def get_git_diff(filepath=None):
    """
    Retrieves the git diff output relative to HEAD.
    If filepath is provided, inspects changes for that specific file.
    Supports both tracked files and newly created untracked files.

    Args:
        filepath (str, optional): Relative path to a specific file to diff.

    Returns:
        str: Raw diff output text or empty string if no diff exists.
    """
    try:
        if filepath and os.path.exists(filepath):
            # 1. Try standard tracked file git diff
            cmd = ["git", "diff", "HEAD", "--", filepath]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace"
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()

            # 2. If empty, check if it's an untracked/new file using --no-index
            null_device = "NUL" if os.name == "nt" else "/dev/null"
            cmd_untracked = ["git", "diff", "--no-index", null_device, filepath]
            result_untracked = subprocess.run(
                cmd_untracked,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace"
            )
            if result_untracked.stdout.strip():
                return result_untracked.stdout.strip()
        else:
            cmd = ["git", "diff", "HEAD"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace"
            )
            if result.returncode == 0:
                return result.stdout.strip()

        return ""
    except Exception as e:
        return f"Error retrieving git diff: {str(e)}"


def render_git_diff(diff_text, title="Git Diff"):
    """
    Renders git diff text with rich syntax highlighting (+ green, - red).

    Args:
        diff_text (str): The raw git diff string to render.
        title (str, optional): Panel title header for the diff box.
    """
    if not diff_text or not diff_text.strip():
        console.print(f"\n[dim yellow]No git diff detected for {title}.[/dim yellow]\n")
        return

    syntax = Syntax(diff_text, "diff", theme="ansi_dark", line_numbers=False)
    panel = Panel(
        syntax,
        title=f"[bold gold1]🔍 {title}[/bold gold1]",
        border_style="cyan",
        expand=False
    )
    console.print(panel)


def show_auto_diff(filepath=None):
    """
    Helper function automatically triggered after AI finishes modifying files.

    Args:
        filepath (str, optional): Path to the file that was modified.
    """
    diff_text = get_git_diff(filepath)
    if diff_text:
        title = f"AI Changes Diff ({os.path.basename(filepath)})" if filepath else "AI Changes Diff"
        render_git_diff(diff_text, title=title)


def render_session_diff(session_id):
    """
    Displays a structured breakdown of the session's memory state and compaction history.

    Args:
        session_id (int): Database session ID to inspect.
    """
    archived_count, last_summary = db.get_compaction_state(session_id)
    all_msgs = db.load_messages(session_id, skip=0)
    pinned_facts = db.load_pinned_memory()

    table = Table(title=f"Session [{session_id}] Memory Structure & History", show_header=True, header_style="bold cyan")
    table.add_column("Property", style="bold green", width=25)
    table.add_column("Details", style="white")

    table.add_row("Total Messages Recorded", str(len(all_msgs)))
    table.add_row("Compacted Messages Count", str(archived_count))
    table.add_row("Active Pinned Facts", str(len(pinned_facts)))

    console.print()
    console.print(table)

    if last_summary:
        summary_panel = Panel(
            last_summary,
            title="[bold yellow]Compacted Memory Context Summary[/bold yellow]",
            border_style="yellow"
        )
        console.print(summary_panel)

    if pinned_facts:
        facts_text = "\n".join(f"- {fact}" for fact in pinned_facts)
        facts_panel = Panel(
            facts_text,
            title="[bold green]Core Memory / Active Pinned Facts[/bold green]",
            border_style="green"
        )
        console.print(facts_panel)

    console.print()
