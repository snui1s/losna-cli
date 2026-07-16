"""
db.py - SQLite persistence layer for chat sessions and long-term memory.

Tables:
    sessions - one row per chat "tab" (like Claude's sidebar)
    messages - all messages belonging to a session
    memory   - long-term facts extracted from conversations, shared across all sessions
"""

import sqlite3
import os
from datetime import datetime

# Resolved to always place agent_data.db at the project root directory
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "agent_data.db"))


def get_connection():
    """Open a connection with foreign keys enforced and Row access by column name."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create tables if they don't exist yet. Safe to call every startup."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            tool_call_id TEXT,
            tool_name TEXT,
            tool_calls_json TEXT,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fact_text TEXT NOT NULL,
            source_session_id INTEGER,
            extracted_at TEXT NOT NULL,
            FOREIGN KEY (source_session_id) REFERENCES sessions(id) ON DELETE SET NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS archived_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            archived_at TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
            UNIQUE(session_id, role, content)
        )
    """)

    # Speeds up "load all messages for session X ordered by time"
    cur.execute("CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_archived_session ON archived_messages(session_id)")

    # --- Migration: add tool_calls_json column to existing databases ---
    cur.execute("PRAGMA table_info(messages)")
    existing_columns = {row["name"] for row in cur.fetchall()}
    if "tool_calls_json" not in existing_columns:
        cur.execute("ALTER TABLE messages ADD COLUMN tool_calls_json TEXT")

    # --- Migration: add compaction watermark columns to sessions ---
    # archived_count tracks how many of this session's messages have already
    # been compacted away, so reloading the session doesn't re-compact them
    # (and re-bill an LLM call) every single time it's reopened.
    cur.execute("PRAGMA table_info(sessions)")
    session_columns = {row["name"] for row in cur.fetchall()}
    if "archived_count" not in session_columns:
        cur.execute("ALTER TABLE sessions ADD COLUMN archived_count INTEGER DEFAULT 0")
    if "last_summary" not in session_columns:
        cur.execute("ALTER TABLE sessions ADD COLUMN last_summary TEXT")

    conn.commit()
    conn.close()


# --- Session management ---

def create_session(title):
    """Create a new chat session (tab) and return its id."""
    now = datetime.now().isoformat()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO sessions (title, created_at, updated_at) VALUES (?, ?, ?)",
        (title, now, now)
    )
    session_id = cur.lastrowid
    conn.commit()
    conn.close()
    return session_id


def list_sessions():
    """Return all sessions, most recently updated first."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, title, created_at, updated_at FROM sessions ORDER BY updated_at DESC")
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def touch_session(session_id):
    """Update a session's updated_at timestamp - call after every new message."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE sessions SET updated_at = ? WHERE id = ?",
        (datetime.now().isoformat(), session_id)
    )
    conn.commit()
    conn.close()


def session_exists(session_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM sessions WHERE id = ?", (session_id,))
    exists = cur.fetchone() is not None
    conn.close()
    return exists


# --- Message management ---

def save_message(session_id, role, content, tool_call_id=None, tool_name=None, tool_calls_json=None):
    """Insert one message into a session's history. Call this right after every
    user input, assistant reply, tool-call request, or tool result.

    For assistant messages that invoke tools, pass the serialized tool_calls
    array as `tool_calls_json` so the full interaction is recoverable."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO messages (session_id, role, content, tool_call_id, tool_name, tool_calls_json, timestamp)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (session_id, role, content, tool_call_id, tool_name, tool_calls_json, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()
    touch_session(session_id)


def load_messages(session_id, skip=0):
    """Load messages for a session, in chronological order, as plain dicts
    ready to drop into conversation_history.

    `skip` lets the caller drop the oldest N messages that have already been
    compacted away (see get_compaction_state/update_compaction_state) - without
    this, reopening a session would re-see the full raw history and trigger
    compaction all over again every time.

    Assistant messages that originally carried tool_calls are reconstructed
    with the proper 'tool_calls' key so the LLM sees a valid history."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT role, content, tool_call_id, tool_name, tool_calls_json FROM messages WHERE session_id = ? ORDER BY id ASC",
        (session_id,)
    )
    rows = cur.fetchall()
    conn.close()

    if skip:
        rows = rows[skip:]

    messages = []
    for row in rows:
        msg = {"role": row["role"], "content": row["content"]}
        if row["tool_call_id"]:
            msg["tool_call_id"] = row["tool_call_id"]
        if row["tool_name"]:
            msg["name"] = row["tool_name"]
        # Reconstruct tool_calls for assistant messages that invoked tools
        if row["tool_calls_json"]:
            try:
                import json
                msg["tool_calls"] = json.loads(row["tool_calls_json"])
            except (json.JSONDecodeError, TypeError):
                pass
        messages.append(msg)
    return messages


# --- Long-term memory ---

def fact_exists(fact_text, similarity_threshold=0.85):
    """Check if a near-duplicate fact already exists in memory, to avoid
    saving the same fact over and over (e.g. 'User's name is Nell' repeated
    every compaction cycle)."""
    import difflib
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT fact_text FROM memory")
    existing = [row["fact_text"] for row in cur.fetchall()]
    conn.close()

    for old_fact in existing:
        ratio = difflib.SequenceMatcher(None, fact_text.lower(), old_fact.lower()).ratio()
        if ratio >= similarity_threshold:
            return True
    return False


def save_memory_fact(fact_text, source_session_id=None):
    """Store one extracted long-term fact."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO memory (fact_text, source_session_id, extracted_at) VALUES (?, ?, ?)",
        (fact_text, source_session_id, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def load_all_memory():
    """Load every long-term fact across all sessions - used to build the system prompt."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT fact_text FROM memory ORDER BY id ASC")
    rows = cur.fetchall()
    conn.close()
    return [row["fact_text"] for row in rows]


def archive_messages(session_id, messages):
    """Move compacted-out messages into cold storage, scoped to their session.
    Uses INSERT OR IGNORE against the UNIQUE(session_id, role, content) constraint
    so re-archiving the same messages (e.g. from a stale in-memory reload) is a
    harmless no-op instead of piling up duplicates."""
    if not messages:
        return
    now = datetime.now().isoformat()
    conn = get_connection()
    cur = conn.cursor()
    cur.executemany(
        "INSERT OR IGNORE INTO archived_messages (session_id, role, content, archived_at) VALUES (?, ?, ?, ?)",
        [(session_id, m.get("role", "unknown"), m.get("content") or "", now) for m in messages]
    )
    conn.commit()
    conn.close()


def load_archived_messages(session_id):
    """Load a session's archived messages - scoped strictly to one session."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT role, content, archived_at FROM archived_messages WHERE session_id = ? ORDER BY id ASC",
        (session_id,)
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


# --- Compaction watermark (prevents re-compacting on every session reload) ---

def get_compaction_state(session_id):
    """Return (archived_count, last_summary) for a session - how many of its
    messages have already been compacted away, and the most recent summary."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT archived_count, last_summary FROM sessions WHERE id = ?", (session_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        return row["archived_count"] or 0, row["last_summary"]
    return 0, None


def update_compaction_state(session_id, archived_count, summary):
    """Persist how far compaction has progressed for a session, so reloading
    it later picks up from here instead of re-processing already-compacted
    messages (and paying for another LLM call to re-summarize them)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE sessions SET archived_count = ?, last_summary = ? WHERE id = ?",
        (archived_count, summary, session_id)
    )
    conn.commit()
    conn.close()