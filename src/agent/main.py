"""
main.py — Slim entrypoint orchestrator for Losna CLI.

Initializes the database, selects a session, and runs the main conversation loop.
Delegates slash command handling to slash_commands.py and AI agent calls to agent_loop.py.
"""

import os
import time
from . import config
from . import db
from . import prompts
from . import session
from . import skills_loader
from . import mention_utils
from .memory import compact_memory
from .ui import get_user_input, print_session_header, print_recent_messages_preview
from .slash_commands import handle_slash_command
from .agent_loop import run_agent_loop
from .usage_tracker import UsageTracker


def main():
    # --- Startup Initialization ---
    init_db_result = db.init_db()
    current_session_id, conversation_history = session.select_session()
    SYSTEM_PROMPT = conversation_history[0]["content"]
    usage_tracker = UsageTracker()

    # Print banner, session header, and trigger update check
    print_session_header(current_session_id)

    # Render recent message preview if resuming an existing session with history
    recent_msgs = db.get_recent_messages(current_session_id, limit=3)
    if recent_msgs:
        print_recent_messages_preview(recent_msgs, session_id=current_session_id)

    # --- Main Conversation Loop ---

    while True:
        skills = skills_loader.list_skills()
        user_input = get_user_input(skills)

        # Ignore empty inputs and prompt again
        if not user_input or not user_input.strip():
            continue

        # Check for loop termination command
        if user_input.lower() in ['/exit', '/quit']:
            exit_summary = usage_tracker.format_exit_summary()
            if exit_summary:
                print(exit_summary)
            print("Shutting down agent...")
            break

        # --- Build shared mutable context ---
        ctx = {
            "session_id": current_session_id,
            "conversation_history": conversation_history,
            "SYSTEM_PROMPT": SYSTEM_PROMPT,
            "skills": skills,
            "is_skill_cmd": False,
            "usage_tracker": usage_tracker,
        }

        # --- Try slash command dispatch ---
        handled = handle_slash_command(user_input, ctx)

        # Sync back any mutations from slash command handlers
        current_session_id = ctx["session_id"]
        conversation_history = ctx["conversation_history"]
        SYSTEM_PROMPT = ctx["SYSTEM_PROMPT"]
        is_skill_cmd = ctx.get("is_skill_cmd", False)

        if handled:
            continue

        # --- Check for @filepath mentions in user input ---
        mentioned_files = mention_utils.extract_file_mentions(user_input)
        if mentioned_files:
            attachments = mention_utils.load_file_attachments(mentioned_files)
            mention_block = mention_utils.build_mention_prompt_block(attachments)
            for att in attachments:
                print(f"  \033[1;36m[System]: Attached context from @{att['path']}\033[0m")

            conversation_history.append({
                "role": "system",
                "content": mention_block
            })
            db.save_message(current_session_id, "system", mention_block)

        if not is_skill_cmd:
            # State Update: Append the new user message to the active conversation history
            conversation_history.append({"role": "user", "content": user_input})
            _t0 = time.time()
            db.save_message(current_session_id, "user", user_input)
            if getattr(config, "DEBUG", False):
                print(f"  [DEBUG] db.save_message(user) took {time.time()-_t0:.3f}s")

        # --- State: Memory Compaction Logic ---
        if getattr(config, "DEBUG", False):
            print(f"  [DEBUG] conversation_history length: {len(conversation_history)} (compaction threshold: {config.MAX_ACTIVE_MESSAGES})")
        _t0 = time.time()
        conversation_history = compact_memory(
            conversation_history,
            config.MAX_ACTIVE_MESSAGES,
            config.KEEP_RECENT,
            config.COMPACTION_MODEL,
            SYSTEM_PROMPT,
            session_id=current_session_id
        )
        if getattr(config, "DEBUG", False):
            print(f"  [DEBUG] compact_memory took {time.time()-_t0:.3f}s")

        # --- Run Agent Loop ---
        ctx["conversation_history"] = conversation_history
        run_agent_loop(ctx)

        # Sync back after agent loop
        conversation_history = ctx["conversation_history"]


if __name__ == "__main__":
    main()
