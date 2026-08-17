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
from .ui import get_user_input, print_banner
from .slash_commands import handle_slash_command
from .agent_loop import run_agent_loop
from .usage_tracker import UsageTracker


def main():
    # --- Startup Initialization ---
    init_db_result = db.init_db()
    current_session_id, conversation_history = session.select_session()
    SYSTEM_PROMPT = conversation_history[0]["content"]
    usage_tracker = UsageTracker()

    # Format model name and path for the banner display
    model_display = "Deepseek V4 flash" if "deepseek-v4-flash" in config.MODEL_NAME else config.MODEL_NAME.split("/")[-1].replace("-", " ").title()
    project_path = os.path.realpath(os.getcwd()).replace("\\", "/")

    # Print the customized Losna CLI gold crescent moon banner
    print_banner(model_display, project_path)
    print(f"Current session: [{current_session_id}]")

    auto_fname, auto_fpath, _ = prompts.load_auto_ai_context()
    if auto_fname:
        print(f"  \033[1;36m[System]: Auto-loaded project AI instructions from '{auto_fname}' ({auto_fpath})\033[0m")

    print("Commands: '/new <title>' new chat | '/switch <id>' change chat | '@file' attach file | '/ls' list dir | '/help' help menu | '/exit' or '/quit' to leave.\n")

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
            print(f"  [DEBUG] db.save_message(user) took {time.time()-_t0:.3f}s")

        # --- State: Memory Compaction Logic ---
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
        print(f"  [DEBUG] compact_memory took {time.time()-_t0:.3f}s")

        # --- Run Agent Loop ---
        ctx["conversation_history"] = conversation_history
        run_agent_loop(ctx)

        # Sync back after agent loop
        conversation_history = ctx["conversation_history"]


if __name__ == "__main__":
    main()
