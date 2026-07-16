from datetime import datetime
from . import db
from . import prompts

def select_session():
    """Show existing chat sessions and let the user resume one or start a new one.
    Returns (session_id, conversation_history)."""
    sessions = db.list_sessions()

    if sessions:
        print("=== Existing Chat Sessions ===")
        for s in sessions:
            print(f"  [{s['id']}] {s['title']}  (last updated: {s['updated_at']})")
        print("Type a session ID to resume it, or '/new <title>' to start a new chat.\n")
    else:
        print("No existing sessions yet. Start one with '/new <title>'.\n")

    while True:
        choice = input("Session: ").strip()

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
