"""
export_utils.py — Chat session export module for Losna CLI.

Exports full conversation history from SQLite into a structured, clean Markdown document.
"""

import os
import json
from datetime import datetime
from . import db
from . import config


def export_session_to_markdown(session_id: int, custom_filepath: str = None) -> tuple[bool, str]:
    """
    Exports a chat session's full conversation history into a Markdown file.

    Args:
        session_id (int): Database ID of the session to export.
        custom_filepath (str, optional): Custom destination file path.

    Returns:
        tuple[bool, str]: (Success status, filepath or error message).
    """
    try:
        if not db.session_exists(session_id):
            return False, f"Error: Session [{session_id}] does not exist."

        # Fetch session metadata
        sessions = db.list_sessions()
        session_meta = next((s for s in sessions if s["id"] == session_id), None)
        title = session_meta["title"] if session_meta else f"Session {session_id}"
        updated_at = session_meta["updated_at"] if session_meta else datetime.now().isoformat()

        # Fetch all messages (including archived cold storage messages)
        archived_msgs = db.load_archived_messages(session_id)
        active_msgs = db.load_messages(session_id, skip=0)

        # Merge archived and active history
        all_msgs = []
        if archived_msgs:
            for am in archived_msgs:
                all_msgs.append({"role": am["role"], "content": am["content"], "archived": True})

        for msg in active_msgs:
            # Skip system prompt in body for clean reading
            if msg.get("role") == "system":
                continue
            all_msgs.append(msg)

        if not all_msgs:
            return False, f"Error: Session [{session_id}] has no recorded messages to export."

        # Determine target file path
        if custom_filepath:
            target_path = os.path.realpath(custom_filepath.strip())
        else:
            base_dir = os.path.realpath(os.getcwd())
            exports_dir = os.path.join(base_dir, "exports")
            os.makedirs(exports_dir, exist_ok=True)
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            target_path = os.path.join(exports_dir, f"export_session_{session_id}_{timestamp_str}.md")

        # Build Markdown content
        md_lines = [
            f"# Chat Session Export: {title}",
            "",
            f"- **Session ID**: `{session_id}`",
            f"- **Export Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"- **Last Updated**: {updated_at}",
            f"- **Model**: `{config.MODEL_NAME}`",
            f"- **Total Messages**: {len(all_msgs)}",
            "",
            "---",
            ""
        ]

        for idx, msg in enumerate(all_msgs, 1):
            role = msg.get("role", "unknown")
            content = msg.get("content", "")

            if role == "user":
                md_lines.append(f"### 👤 User")
                md_lines.append(content)
                md_lines.append("")

            elif role == "assistant":
                md_lines.append(f"### 🤖 Agent")
                md_lines.append(content)
                md_lines.append("")

                # Check tool calls
                tool_calls = msg.get("tool_calls")
                if tool_calls:
                    md_lines.append("> 🛠️ **Executed Tool Calls**:")
                    for tc in tool_calls:
                        if isinstance(tc, dict):
                            fn = tc.get("function", {})
                            name = fn.get("name", "tool")
                            args = fn.get("arguments", "")
                            md_lines.append(f"> - `{name}`: `{args}`")
                    md_lines.append("")

            elif role == "tool":
                tool_name = msg.get("name", "tool")
                md_lines.append(f"> 📥 **Tool Result** (`{tool_name}`):")
                # Wrap long tool result in collapsible details block or code fence
                md_lines.append("```text")
                md_lines.append(str(content)[:2000] + ("\n...[truncated]" if len(str(content)) > 2000 else ""))
                md_lines.append("```")
                md_lines.append("")

        # Save to file
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            f.write("\n".join(md_lines))

        return True, target_path

    except Exception as e:
        return False, f"Error exporting session [{session_id}]: {str(e)}"
