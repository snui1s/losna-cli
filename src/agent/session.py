"""
session.py — Interactive session selection and management module.

Handles listing, resuming, and creating chat sessions interactively upon application launch.
"""

from datetime import datetime
from . import db
from . import prompts


def select_session():
    """
    Shows existing chat sessions with recent message previews and lets the user
    resume one or start a new one. Supports pressing Enter to resume the most recent session.

    Returns:
        tuple[int, list[dict]]: A tuple containing (session_id, conversation_history).
    """
    GREEN = "\033[1;32m"
    GOLD = "\033[38;5;220m"
    CYAN = "\033[1;36m"
    GRAY = "\033[38;5;244m"
    DARK_GRAY = "\033[38;5;238m"
    RESET = "\033[0m"

    sessions = db.list_sessions_with_preview()
    default_sid = sessions[0]["id"] if sessions else None

    if sessions:
        print(f"\n{CYAN}=== Existing Chat Sessions ==={RESET}")
        for s in sessions:
            msg_count_str = f"{s.get('msg_count', 0)} msgs"
            updated_str = s['updated_at'].split('.')[0].replace('T', ' ') if 'T' in str(s['updated_at']) else s['updated_at']
            is_default = f" {GREEN}(latest){RESET}" if s['id'] == default_sid else ""
            print(f"  {GOLD}[{s['id']}]{RESET} {s['title']}  {GRAY}({updated_str}, {msg_count_str}){RESET}{is_default}")

            last_msg = s.get("last_message")
            if last_msg:
                role = last_msg.get("role", "").lower()
                raw_content = (last_msg.get("content") or "").strip()
                lines = raw_content.splitlines()
                content = lines[0].strip() if lines else ""
                if content:
                    if len(content) > 75:
                        content = content[:72] + "..."
                    if role == "user":
                        badge = f"{GREEN}🧑 You:{RESET}"
                    elif role == "assistant":
                        badge = f"{GOLD}🌒 Losna:{RESET}"
                    else:
                        badge = f"{GRAY}[{role}]:{RESET}"
                    print(f"      {DARK_GRAY}└─{RESET} {badge} {GRAY}\"{content}\"{RESET}")
        print(f"\nType a session ID {GRAY}(or press Enter for [{default_sid}]){RESET}, or {CYAN}'/new <title>'{RESET} to start a new chat.\n")
    else:
        print("\nNo existing sessions yet. Start one with '/new <title>'.\n")

    prompt_label = f"Session [default: {default_sid}]: " if default_sid is not None else "Session: "

    while True:
        choice = input(prompt_label).strip()

        # Pressing Enter defaults to the most recent session
        if not choice and default_sid is not None:
            choice = str(default_sid)

        if choice.lower().startswith("/new"):
            title = choice[4:].strip() or f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            new_id = db.create_session(title)
            print(f"Created new session [{new_id}] '{title}'\n")
            history = [{"role": "system", "content": prompts.build_system_prompt()}]
            return new_id, history

        elif choice.isdigit() and db.session_exists(int(choice)):
            sid = int(choice)
            archived_count, last_summary = db.get_compaction_state(sid)
            history = db.load_messages(sid, skip=archived_count)
            system_content = prompts.build_system_prompt()
            if last_summary:
                system_content += f"\n\n[Previous Context Summary]: {last_summary}"
            if not history or history[0].get("role") != "system":
                history = [{"role": "system", "content": system_content}] + history
            else:
                history[0]["content"] = system_content
            print(f"Resumed session [{sid}] with {len(history)} message(s).\n")
            return sid, history

        else:
            print("Invalid input. Type a valid session ID or '/new <title>'.")
