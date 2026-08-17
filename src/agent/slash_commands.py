"""
slash_commands.py — All slash command handlers for Losna CLI.

Dispatches user slash commands (/help, /sessions, /new, /switch, etc.)
and returns True if the command was handled, False if input should
fall through to the AI agent loop.
"""

import os
import json
from datetime import datetime
from . import config
from . import db
from . import prompts
from . import skills_loader
from . import plugin_manager
from . import diff_utils
from . import export_utils
from . import mention_utils
from .ui import print_banner, print_session_header

# Set of all built-in slash commands (used to detect unknown commands vs skill commands)
RESERVED_COMMANDS = {
    '/help', '/sessions', '/new', '/switch', '/delete_session', '/history',
    '/exit', '/quit', '/search', '/model', '/plugin', '/readonly', '/diff',
    '/enter2confirm', '/pin', '/unpin', '/pins', '/export', '/clear', 'clear',
    '/ls', 'ls', '/cd', 'cd', '/init-ai', '/init_ai', '/initai',
    '/max_tool_calls', '/max_tools', '/maxtools', '/max_tool_call',
    '/usage'
}


def _refresh_system_prompt(ctx):
    """Refreshes system prompt content in context and conversation history."""
    ctx["SYSTEM_PROMPT"] = prompts.build_system_prompt(read_only=config.READ_ONLY_MODE)
    if ctx["conversation_history"] and ctx["conversation_history"][0].get("role") == "system":
        ctx["conversation_history"][0]["content"] = ctx["SYSTEM_PROMPT"]


def _load_session(session_id, ctx):
    """Loads a session's messages and system prompt into context."""
    ctx["session_id"] = session_id
    archived_count, last_summary = db.get_compaction_state(session_id)
    loaded = db.load_messages(session_id, skip=archived_count)
    ctx["SYSTEM_PROMPT"] = prompts.build_system_prompt(previous_summary=last_summary)

    if not loaded or loaded[0].get("role") != "system":
        ctx["conversation_history"] = [{"role": "system", "content": ctx["SYSTEM_PROMPT"]}, *loaded]
    else:
        loaded[0]["content"] = ctx["SYSTEM_PROMPT"]
        ctx["conversation_history"] = loaded


def handle_slash_command(user_input, ctx):
    """
    Routes user input to the appropriate slash command handler.

    Args:
        user_input (str): Raw user input string.
        ctx (dict): Mutable command context with keys:
            - session_id (int)
            - conversation_history (list[dict])
            - SYSTEM_PROMPT (str)
            - skills (list[dict])

    Returns:
        bool: True if a command was handled (caller should continue loop),
              False if input should fall through to the AI agent loop.
    """
    lower = user_input.lower()
    command = user_input.split(maxsplit=1)[0].lower()

    # --- Exact match & prefix dispatch by first command token ---
    if command == "/help":
        return _cmd_help(ctx)
    if command == "/sessions":
        return _cmd_sessions(ctx)
    if command == "/pins":
        return _cmd_pins()
    if command == "/pin":
        return _cmd_pin(user_input, ctx)
    if command == "/unpin":
        return _cmd_unpin(user_input, ctx)
    if command == "/usage":
        return _cmd_usage(ctx)
    if command in ("/clear", "clear"):
        return _cmd_clear(ctx)
    if command == "/new":
        return _cmd_new(user_input, ctx)
    if command == "/switch":
        return _cmd_switch(user_input, ctx)
    if command == "/delete_session":
        return _cmd_delete_session(user_input, ctx)
    if command == "/history":
        return _cmd_history(user_input, ctx)
    if command == "/plugin":
        return _cmd_plugin(user_input, ctx)
    if command == "/model":
        return _cmd_model(user_input)
    if command == "/readonly":
        return _cmd_readonly(user_input, ctx)
    if command == "/diff":
        return _cmd_diff(user_input, ctx)
    if command == "/enter2confirm":
        return _cmd_enter2confirm(user_input)
    if command == "/export":
        return _cmd_export(user_input, ctx)
    if command in ("/max_tool_calls", "/max_tools", "/maxtools", "/max_tool_call"):
        return _cmd_max_tool_calls(user_input)
    if command in ("/init-ai", "/init_ai", "/initai"):
        return _cmd_init_ai()
    if command in ("/ls", "ls"):
        return _cmd_ls(user_input)
    if command in ("/cd", "cd"):
        return _cmd_cd(user_input)
    if command == "/search":
        return _cmd_search(user_input, ctx)

    # --- Dynamic skill commands ---
    if user_input.startswith("/") and command not in RESERVED_COMMANDS:
        return _cmd_skill(user_input, ctx)

    return False


# ────────────────────────────────────────────────────────────────────
# Individual command handlers
# ────────────────────────────────────────────────────────────────────

def _cmd_help(ctx):
    skills = ctx.get("skills", [])
    print("=== Available Commands ===")
    print("  /help          - Show this help menu with all available commands")
    print("  /sessions      - List all chat sessions (tabs) and see their IDs")
    print("  /new <title>   - Start a new chat session (e.g. '/new Web Development')")
    print("  /switch <id>   - Switch to an existing chat session by its ID (e.g. '/switch 3')")
    print("  /delete_session <id> - Delete an existing chat session by its ID")
    print("  /history [id]  - View the chat logs and tool call history for a session (defaults to current)")
    print("  /model         - View current OpenRouter model or switch to a new model ID")
    print("  /readonly      - Toggle Read-Only Mode (blocks file modification & shell execution)")
    print("  /diff [file|session] - View colored git diff for a file or session memory state")
    print("  /enter2confirm - Toggle double-Enter requirement before sending prompts to AI")
    print("  /pin <text>    - Pin a custom rule/fact to AI Core Memory (remembered forever across sessions)")
    print("  /pins          - List all pinned Core Memory rules with their IDs")
    print("  /unpin <id>    - Unpin/remove a Core Memory rule by ID")
    print("  /export [path] - Export current chat session history to a Markdown document")
    print("  /clear         - Clear terminal screen and re-render header banner")
    print("  /ls [path]     - List directory files and folders in clean formatted view")
    print("  /cd <path>     - Change working directory (supports '..', '~', and '-')")
    print("  /init-ai       - Generate starter 'ai.txt' blueprint file for project")
    print("  @<filepath>    - Attach local file content directly into AI context (e.g. '@README.md')")
    print("  /max_tool_calls [n] - View or set max tool calls limit per turn (persisted in ~/.losnarc)")
    print("  /plugin add <url> [--skill <name>] - Download and install a custom skill plugin from GitHub")
    print("  /plugin remove <name> - Uninstall/remove a custom skill plugin from local project")
    print("  /search <q>    - Search the web directly using Tavily (prompts for key if missing)")
    print("  /usage         - Show token usage and estimated cost for this session")
    print("  /exit, /quit   - Terminate the agent harness session")
    if skills:
        print("\n=== Skill Commands (loads skill prompt dynamically) ===")
        for s in skills:
            print(f"  /{s['name']:<14} - {s['description']}")

    print("\n=== Command Usage Examples ===")
    print("  @src/agent/main.py Summarize what this file does")
    print("  /plugin add https://github.com/JuliusBrussee/caveman")
    print("  /plugin add https://github.com/vercel-labs/agent-skills --skill vercel-react-best-practices")
    print("  /plugin remove caveman")
    print("  /pin Always write type hints for functions")
    print("  /unpin 1")
    print("  /max_tool_calls 50")
    print("  /diff src/agent/main.py")
    print("  /export ./exports/my_chat.md")
    print("  /switch 3")
    print()
    return True


def _cmd_sessions(ctx):
    current_session_id = ctx["session_id"]
    for s in db.list_sessions():
        marker = " (current)" if s["id"] == current_session_id else ""
        print(f"  [{s['id']}] {s['title']}  (last updated: {s['updated_at']}){marker}")
    print()
    return True


def _cmd_new(user_input, ctx):
    title = user_input[4:].strip() or f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    ctx["session_id"] = db.create_session(title)
    ctx["SYSTEM_PROMPT"] = prompts.build_system_prompt()
    ctx["conversation_history"] = [{"role": "system", "content": ctx["SYSTEM_PROMPT"]}]
    print(f"Switched to new session [{ctx['session_id']}] '{title}'\n")
    return True


def _cmd_switch(user_input, ctx):
    target = user_input[7:].strip()
    if target.isdigit() and db.session_exists(int(target)):
        _load_session(int(target), ctx)
        print(f"Switched to session [{ctx['session_id']}] with {len(ctx['conversation_history'])} message(s)\n")
    else:
        if not target:
            print("Usage: /switch <session_id>  (e.g. '/switch 3'). Use '/sessions' to see available chats.\n")
        else:
            print(f"Session '{target}' not found. Use '/sessions' to see available chats.\n")
    return True


def _cmd_delete_session(user_input, ctx):
    target = user_input[15:].strip()
    if target.isdigit() and db.session_exists(int(target)):
        target_id = int(target)
        if target_id == ctx["session_id"]:
            all_sessions = db.list_sessions()
            other_sessions = [s for s in all_sessions if s["id"] != ctx["session_id"]]
            if other_sessions:
                new_session = other_sessions[0]
                ctx["session_id"] = new_session["id"]
                archived_count, last_summary = db.get_compaction_state(ctx["session_id"])
                loaded = db.load_messages(ctx["session_id"], skip=archived_count)
                ctx["SYSTEM_PROMPT"] = prompts.build_system_prompt(previous_summary=last_summary)
                if not loaded or loaded[0].get("role") != "system":
                    loaded = [{"role": "system", "content": ctx["SYSTEM_PROMPT"]}] + loaded
                else:
                    loaded[0]["content"] = ctx["SYSTEM_PROMPT"]
                ctx["conversation_history"] = loaded
                db.delete_session(target_id)
                print(f"Deleted current session. Switched to session [{ctx['session_id']}] '{new_session['title']}'\n")
            else:
                db.delete_session(target_id)
                ctx["session_id"] = db.create_session("New Chat")
                ctx["SYSTEM_PROMPT"] = prompts.build_system_prompt()
                ctx["conversation_history"] = [{"role": "system", "content": ctx["SYSTEM_PROMPT"]}]
                print(f"Deleted final session. Created and switched to a fresh session [{ctx['session_id']}] 'New Chat'\n")
        else:
            db.delete_session(target_id)
            print(f"Deleted session [{target_id}] successfully.\n")
    else:
        print(f"Session '{target}' not found. Use '/sessions' to view IDs.\n")
    return True


def _cmd_history(user_input, ctx):
    target = user_input[8:].strip()
    target_id = ctx["session_id"]
    if target:
        if target.isdigit() and db.session_exists(int(target)):
            target_id = int(target)
        else:
            print(f"Session '{target}' not found. Use '/sessions' to view valid IDs.\n")
            return True

    all_msgs = db.load_messages(target_id, skip=0)
    _, last_summary = db.get_compaction_state(target_id)

    print(f"\n=== Chat History for Session [{target_id}] ===")
    if last_summary:
        print(f"\033[1;33m[Compacted Context Summary]:\033[0m {last_summary}\n")

    has_messages = False
    for m in all_msgs:
        role = m.get("role", "unknown").upper()
        content = (m.get("content") or "").strip()
        if role == "SYSTEM":
            continue

        has_messages = True
        if role == "USER":
            print(f"\033[1;32mUser:\033[0m {content}")
        elif role == "ASSISTANT":
            if m.get("tool_calls"):
                for tc in m["tool_calls"]:
                    print(f"\033[1;36mAssistant requested tool:\033[0m {tc.get('function', {}).get('name')} {tc.get('function', {}).get('arguments')}")
            if content:
                print(f"\033[1;34mAssistant:\033[0m {content}")
        elif role == "TOOL":
            print(f"  \033[1;30m[Tool Return ({m.get('name')}):\033[0m \033[0;37m{content}\033[1;30m]\033[0m")
        print("-" * 50)

    if not has_messages:
        print("No user or assistant messages in this session yet.")
    print()
    return True


def _cmd_plugin(user_input, ctx):
    parts = user_input.split()
    if len(parts) >= 3 and parts[1].lower() == "add":
        repo_url = parts[2]
        skill_name = None
        if "--skill" in parts:
            try:
                idx = parts.index("--skill")
                if idx + 1 < len(parts):
                    skill_name = parts[idx + 1]
            except ValueError:
                pass

        print(f"  [System]: Attempting to install plugin...")
        result_msg = plugin_manager.install_plugin(repo_url, skill_name)
        print(f"\n{result_msg}\n")
    elif len(parts) >= 2 and parts[1].lower() == "enable":
        if len(parts) >= 3:
            sk = parts[2].strip().lstrip("/")
            config.enable_skill(sk)
            print(f"  \033[1;32m[System]: Skill '{sk}' is now ENABLED.\033[0m\n")
        else:
            print("Usage: /plugin enable <skill_name>\n")
    elif len(parts) >= 2 and parts[1].lower() == "disable":
        if len(parts) >= 3:
            sk = parts[2].strip().lstrip("/")
            config.disable_skill(sk)
            print(f"  \033[1;33m[System]: Skill '{sk}' is now DISABLED.\033[0m\n")
        else:
            print("Usage: /plugin disable <skill_name>\n")
    elif len(parts) >= 2 and parts[1].lower() == "list":
        current_skills = skills_loader.list_skills()
        if not current_skills:
            print("  [System]: No plugins/skills are currently installed.\n")
        else:
            print("=== Installed Plugins/Skills ===")
            for idx, s in enumerate(current_skills, start=1):
                is_dis = config.is_skill_disabled(s['name'])
                status = "\033[1;31m[DISABLED]\033[0m" if is_dis else "\033[1;32m[ENABLED]\033[0m"
                print(f"  [{idx}] /{s['name']:<14} {status} - {s['description']}")
            print()
    elif len(parts) >= 2 and parts[1].lower() == "remove":
        skill_to_remove = parts[2] if len(parts) >= 3 else None

        if not skill_to_remove:
            current_skills = skills_loader.list_skills()
            if not current_skills:
                print("  [System]: No plugins/skills are currently installed.\n")
                return True

            print("\nInstalled Plugins/Skills:")
            for idx, s in enumerate(current_skills, start=1):
                print(f"  [{idx}] /{s['name']} - {s['description']}")
            print()

            choice = input("Enter the number of the plugin to delete (or Press Enter to cancel): ").strip()
            if choice.isdigit():
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(current_skills):
                    skill_to_remove = current_skills[choice_idx]["name"]
                else:
                    print("Invalid number. Operation canceled.\n")
                    return True
            else:
                print("Operation canceled.\n")
                return True

        print(f"  [System]: Attempting to remove plugin '{skill_to_remove}'...")
        result_msg = plugin_manager.remove_plugin(skill_to_remove)
        print(f"\n{result_msg}\n")
    else:
        print("=== Plugin Management Usage ===")
        print("  /plugin add <repository_url> [--skill <skill_name>]")
        print("  /plugin enable <skill_name>  |  /plugin disable <skill_name>")
        print("  /plugin list                |  /plugin remove [skill_name]\n")
        print("Examples:")
        print("  /plugin add https://github.com/JuliusBrussee/caveman")
        print("  /plugin disable caveman  (or '/caveman off')")
        print("  /plugin enable caveman   (or '/caveman on')")
        print("  /plugin list\n")
    return True


def _cmd_model(user_input):
    print(f"\nCurrent Model: \033[1;36m{config.MODEL_NAME}\033[0m")
    new_model = input("Enter OpenRouter Model ID (e.g. 'google/gemini-2.5-pro'): ").strip()
    if new_model:
        config.update_model_name(new_model)
    else:
        print("Model change canceled.")
    print()
    return True


def _cmd_readonly(user_input, ctx):
    parts = user_input.split()
    if len(parts) > 1:
        arg = parts[1].lower()
        if arg in ['on', 'true', '1']:
            config.set_read_only_mode(True)
        elif arg in ['off', 'false', '0']:
            config.set_read_only_mode(False)
        elif arg == 'status':
            pass
        else:
            print("Usage: /readonly [on|off|status]\n")
            return True
    else:
        config.set_read_only_mode(not config.READ_ONLY_MODE)

    CYAN = "\033[1;36m"
    GREEN = "\033[1;32m"
    RESET = "\033[0m"
    status_text = f"{CYAN}ENABLED (Read-Only Mode){RESET}" if config.READ_ONLY_MODE else f"{GREEN}DISABLED (Full Access){RESET}"
    print(f"  [System]: Read-Only Mode is now {status_text}\n")

    _refresh_system_prompt(ctx)
    return True


def _cmd_diff(user_input, ctx):
    parts = user_input.split(maxsplit=1)
    arg = parts[1].strip() if len(parts) > 1 else ""
    if arg.lower() == "session":
        diff_utils.render_session_diff(ctx["session_id"])
    else:
        diff_text = diff_utils.get_git_diff(arg if arg else None)
        title = f"Git Diff ({arg})" if arg else "Git Workspace Diff"
        diff_utils.render_git_diff(diff_text, title=title)
    return True


def _cmd_enter2confirm(user_input):
    parts = user_input.split()
    if len(parts) > 1:
        arg = parts[1].lower()
        if arg in ['on', 'true', '1']:
            config.set_enter_2_confirm(True)
        elif arg in ['off', 'false', '0']:
            config.set_enter_2_confirm(False)
        elif arg == 'status':
            pass
        else:
            print("Usage: /enter2confirm [on|off|status]\n")
            return True
    else:
        config.set_enter_2_confirm(not config.ENTER_2_CONFIRM)

    CYAN = "\033[1;36m"
    GREEN = "\033[1;32m"
    RESET = "\033[0m"
    status_text = f"{CYAN}ENABLED (Press Enter 2x to send){RESET}" if config.ENTER_2_CONFIRM else f"{GREEN}DISABLED (Single Enter to send){RESET}"
    print(f"  [System]: Double-Enter Confirmation is now {status_text}\n")
    return True


def _cmd_pins():
    pinned_items = db.load_pinned_memory_with_ids()
    if not pinned_items:
        print("  [System]: No pinned Core Memory rules found.\n")
    else:
        print("=== Pinned Core Memory Rules ===")
        for item in pinned_items:
            print(f"  [{item['id']}] {item['text']}")
        print()
    return True


def _cmd_usage(ctx):
    tracker = ctx.get("usage_tracker")
    if tracker:
        print(tracker.format_summary())
    else:
        print("  [System]: Usage tracking not available.\n")
    return True


def _cmd_pin(user_input, ctx):
    parts = user_input.split(maxsplit=1)
    rule_text = parts[1].strip() if len(parts) > 1 else ""
    if not rule_text:
        print("Usage: /pin <rule_text>  (e.g. '/pin Always use type hints')\n")
        return True
    db.save_memory_fact(rule_text, source_session_id=ctx["session_id"], is_pinned=True)
    _refresh_system_prompt(ctx)
    print(f"  [System]: Pinned to Core Memory: '{rule_text}'\n")
    return True


def _cmd_unpin(user_input, ctx):
    parts = user_input.split(maxsplit=1)
    target = parts[1].strip() if len(parts) > 1 else ""
    if not target:
        print("Error: Please specify an ID or fact text to unpin, e.g. '/unpin 1'\n")
        return True
    success = db.delete_pinned_fact(target)
    if success:
        _refresh_system_prompt(ctx)
        print(f"  [System]: Successfully unpinned Core Memory item [{target}]\n")
    else:
        print(f"  [System]: Could not find pinned Core Memory item matching '{target}'\n")
    return True


def _cmd_export(user_input, ctx):
    parts = user_input.split(maxsplit=1)
    path_arg = parts[1].strip() if len(parts) > 1 else None
    success, result_path = export_utils.export_session_to_markdown(ctx["session_id"], custom_filepath=path_arg)
    if success:
        print(f"  [System]: Successfully exported chat session to: {result_path}\n")
    else:
        print(f"  [System]: Export failed - {result_path}\n")
    return True


def _cmd_clear(ctx):
    os.system("cls" if os.name == "nt" else "clear")
    print_session_header(ctx["session_id"])
    return True


def _cmd_max_tool_calls(user_input):
    parts = user_input.split()
    if len(parts) > 1:
        if parts[1].isdigit():
            new_val = int(parts[1])
            if new_val > 0:
                config.set_max_tool_calls(new_val)
                print(f"  [System]: MAX_TOOL_CALLS limit updated and persisted to {new_val}\n")
            else:
                print("Error: Please provide a positive integer greater than 0.\n")
        else:
            print("Error: Please provide a positive integer greater than 0.\n")
    else:
        print(f"  [System]: Current MAX_TOOL_CALLS limit: {config.MAX_TOOL_CALLS}\n")
    return True


def _cmd_init_ai():
    target_path = os.path.join(os.getcwd(), "ai.txt")
    if os.path.exists(target_path):
        print(f"  [System]: 'ai.txt' already exists at {target_path}\n")
        return True

    folder_name = os.path.basename(os.getcwd())
    starter_content = f"""# Project AI Instructions: {folder_name}

## Overview
Briefly describe what this project does and key goals.

## Project Structure
- src/: Source code files
- tests/: Unit test suite (Source of Truth)

## Coding Standards & Guidelines
- Write clean, type-hinted code.
- Always verify changes with unit tests before completing tasks.
"""
    try:
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(starter_content)
        print(f"  \033[1;32m[System]: Successfully created 'ai.txt' blueprint at: {target_path}\033[0m\n")
    except Exception as e:
        print(f"Error creating ai.txt: {e}\n")
    return True


def _cmd_ls(user_input):
    parts = user_input.split(maxsplit=1)
    target_path = parts[1].strip() if len(parts) > 1 else "."

    abs_target = os.path.abspath(target_path)
    if not os.path.exists(abs_target):
        print(f"Error: Directory or file '{target_path}' does not exist.\n")
        return True

    if os.path.isfile(abs_target):
        size = os.path.getsize(abs_target)
        print(f"  📄 {os.path.basename(abs_target)} ({size:,} bytes)\n")
        return True

    try:
        items = sorted(os.listdir(abs_target))
        rel_path = os.path.relpath(abs_target, os.getcwd()).replace("\\", "/")
        display_path = "." if rel_path == "." else f"./{rel_path}"
        print(f"=== Directory Listing: {display_path} ===")

        dirs = []
        files = []
        for item in items:
            if item.startswith(".") and item not in [".env", ".losnarc"]:
                continue
            full_item = os.path.join(abs_target, item)
            if os.path.isdir(full_item):
                dirs.append(f"  \033[1;36m📁 {item}/\033[0m")
            else:
                size = os.path.getsize(full_item)
                files.append(f"  \033[38;5;253m📄 {item}\033[0m \033[38;5;244m({size:,} bytes)\033[0m")

        for d in dirs:
            print(d)
        for f in files:
            print(f)
        if not dirs and not files:
            print("  (directory is empty)")
        print()
    except Exception as e:
        print(f"Error reading directory: {e}\n")
    return True


def _cmd_cd(user_input):
    parts = user_input.split(maxsplit=1)
    target = parts[1].strip() if len(parts) > 1 else config.PROJECT_ROOT

    if target == "~":
        target = os.path.expanduser("~")
    elif target == "-":
        target = getattr(config, "_PREV_PWD", config.PROJECT_ROOT)

    try:
        abs_target = os.path.abspath(target)
        if not os.path.exists(abs_target):
            print(f"Error: Directory '{target}' does not exist.\n")
            return True
        if not os.path.isdir(abs_target):
            print(f"Error: Path '{target}' is a file, not a directory.\n")
            return True

        config._PREV_PWD = os.getcwd()
        os.chdir(abs_target)
        rel_path = os.path.relpath(abs_target, config.PROJECT_ROOT).replace("\\", "/")
        display_path = "." if rel_path == "." else f"./{rel_path}"
        print(f"  \033[1;32m[System]: Changed working directory to: {display_path}\033[0m  ({abs_target})\n")
    except Exception as e:
        print(f"Error changing directory: {e}\n")
    return True


def _cmd_search(user_input, ctx):
    """Handles /search <query> — injects system guide and user message, returns False to fall through to agent loop."""
    query = user_input[7:].strip()
    if not query:
        print("Error: Please provide a query to search, e.g. '/search python 3.14 features'\n")
        return True

    ctx["conversation_history"].append({
        "role": "system",
        "content": "CRITICAL: The user wants to search the web. You MUST execute the 'web_search' tool on the query provided below to answer their question."
    })
    db.save_message(ctx["session_id"], "system", "CRITICAL: The user wants to search the web. You MUST execute the 'web_search' tool on the query provided below to answer their question.")

    ctx["conversation_history"].append({"role": "user", "content": query})
    db.save_message(ctx["session_id"], "user", query)
    ctx["is_skill_cmd"] = True
    return False  # Fall through to agent loop


def _cmd_skill(user_input, ctx):
    """Handles dynamic skill commands like /unit-testing <query>."""
    parts = user_input.split(maxsplit=1)
    cmd_name = parts[0][1:].strip().lower()
    query = parts[1].strip() if len(parts) > 1 else ""
    skills = ctx.get("skills", [])

    matching_skills = [s for s in skills if s["name"].lower() == cmd_name]
    if matching_skills:
        skill = matching_skills[0]
        sub_arg = query.strip().lower()

        # Handle direct toggle subcommands: /<skill> off|disable|on|enable|status
        if sub_arg in ["off", "disable", "disabled", "0"]:
            config.disable_skill(skill["name"])
            print(f"  \033[1;33m[System]: Skill '{skill['name']}' is now DISABLED.\033[0m\n")
            return True
        elif sub_arg in ["on", "enable", "enabled", "1"]:
            config.enable_skill(skill["name"])
            print(f"  \033[1;32m[System]: Skill '{skill['name']}' is now ENABLED.\033[0m\n")
            return True
        elif sub_arg in ["status"]:
            status_str = "\033[1;31mDISABLED\033[0m" if config.is_skill_disabled(skill["name"]) else "\033[1;32mENABLED\033[0m"
            print(f"  [System]: Skill '{skill['name']}' is currently {status_str}.\n")
            return True

        # If skill is disabled, block execution
        if config.is_skill_disabled(skill["name"]):
            print(f"  \033[1;31m[System]: Skill '{skill['name']}' is currently DISABLED.\033[0m")
            print(f"  Type '/{skill['name']} on' or '/plugin enable {skill['name']}' to enable it.\n")
            return True

        print(f"  [System]: Invoking skill '{skill['name']}'...")
        skill_content = skills_loader.read_skill(skill["name"])

        ctx["conversation_history"].append({
            "role": "system",
            "content": f"[Invoked Skill Instructions: {skill['name']}]\n{skill_content}"
        })
        db.save_message(ctx["session_id"], "system", f"[Invoked Skill: {skill['name']}]\n{skill_content}")

        user_msg = query if query else f"I want you to use the '{skill['name']}' skill."
        ctx["conversation_history"].append({"role": "user", "content": user_msg})
        db.save_message(ctx["session_id"], "user", user_msg)
        ctx["is_skill_cmd"] = True
        return False  # Fall through to agent loop
    else:
        print(f"  [System]: Unknown slash command '/{cmd_name}'. Type '/help' to see available commands.\n")
        return True
