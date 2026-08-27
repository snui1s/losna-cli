"""
db.py - SQLite persistence layer for chat sessions, long-term memory, and audit history.
Hardened with WAL mode, busy timeout, BEGIN IMMEDIATE transactions, semantic fact search,
hybrid relevance retrieval, and Pinned Core Memory protection.
"""

import sqlite3
import os
import math
from datetime import datetime

from .embedding_utils import (
    embed_passage,
    embed_passages_batch,
    embed_query,
    cosine_similarity,
    vector_to_json,
    vector_from_json,
)

# Resolved to always place agent_data.db at the project root directory
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "agent_data.db"))


def get_connection(timeout=10.0):
    """
    Open a connection with foreign keys enforced, WAL mode, busy timeout, and autocommit mode
    (isolation_level = None) for explicit transaction control via BEGIN IMMEDIATE.
    """
    conn = sqlite3.connect(DB_PATH, timeout=timeout)
    conn.isolation_level = None  # Autocommit mode: manage transactions explicitly via BEGIN IMMEDIATE
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 10000")
    return conn


def init_db():
    """Create tables if they don't exist yet. Safe to call on every startup."""
    conn = get_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")
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
                embedding TEXT,
                source_session_id INTEGER,
                extracted_at TEXT NOT NULL,
                last_used_at TEXT NOT NULL,
                is_pinned INTEGER DEFAULT 0,
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

        cur.execute("""
            CREATE TABLE IF NOT EXISTS memory_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_fact_id INTEGER,
                fact_text TEXT NOT NULL,
                embedding TEXT,
                action TEXT NOT NULL,
                replaced_by_text TEXT,
                archived_at TEXT NOT NULL
            )
        """)

        # --- Migrations for existing DBs ---
        cur.execute("PRAGMA table_info(messages)")
        msg_cols = {row["name"] for row in cur.fetchall()}
        if "tool_calls_json" not in msg_cols:
            cur.execute("ALTER TABLE messages ADD COLUMN tool_calls_json TEXT")

        cur.execute("PRAGMA table_info(sessions)")
        ses_cols = {row["name"] for row in cur.fetchall()}
        if "archived_count" not in ses_cols:
            cur.execute("ALTER TABLE sessions ADD COLUMN archived_count INTEGER DEFAULT 0")
        if "last_summary" not in ses_cols:
            cur.execute("ALTER TABLE sessions ADD COLUMN last_summary TEXT")

        cur.execute("PRAGMA table_info(memory)")
        mem_cols = {row["name"] for row in cur.fetchall()}
        if "last_used_at" not in mem_cols:
            cur.execute("ALTER TABLE memory ADD COLUMN last_used_at TEXT")
            cur.execute("UPDATE memory SET last_used_at = extracted_at WHERE last_used_at IS NULL")
        if "embedding" not in mem_cols:
            cur.execute("ALTER TABLE memory ADD COLUMN embedding TEXT")
        if "is_pinned" not in mem_cols:
            cur.execute("ALTER TABLE memory ADD COLUMN is_pinned INTEGER DEFAULT 0")

        # --- Index creation after column migrations ---
        cur.execute("CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_archived_session ON archived_messages(session_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_memory_history_action ON memory_history(action)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_memory_pinned ON memory(is_pinned)")

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# --- Session management ---

def create_session(title):
    """Create a new chat session (tab) and return its id."""
    now = datetime.now().isoformat()
    conn = get_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO sessions (title, created_at, updated_at) VALUES (?, ?, ?)",
            (title, now, now)
        )
        session_id = cur.lastrowid
        conn.commit()
        return session_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def list_sessions():
    """Return all sessions, most recently updated first."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, title, created_at, updated_at FROM sessions ORDER BY updated_at DESC")
        rows = cur.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def touch_session(session_id):
    """Update a session's updated_at timestamp - call after every new message."""
    conn = get_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")
        cur = conn.cursor()
        cur.execute(
            "UPDATE sessions SET updated_at = ? WHERE id = ?",
            (datetime.now().isoformat(), session_id)
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def session_exists(session_id):
    """Return True if session_id is a valid, existing session."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM sessions WHERE id = ?", (session_id,))
        row = cur.fetchone()
        return bool(row)
    finally:
        conn.close()


def delete_session(session_id):
    """Delete a session by its ID. SQLite foreign keys ON DELETE CASCADE will wipe dependencies."""
    conn = get_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")
        cur = conn.cursor()
        cur.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def rename_session(session_id: int, new_title: str) -> bool:
    """Update a session's title."""
    if not new_title or not new_title.strip():
        return False
    conn = get_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")
        cur = conn.cursor()
        cur.execute(
            "UPDATE sessions SET title = ?, updated_at = ? WHERE id = ?",
            (new_title.strip(), datetime.now().isoformat(), session_id)
        )
        rowcount = cur.rowcount
        conn.commit()
        return rowcount > 0
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# --- Message management ---

def save_message(session_id, role, content, tool_call_id=None, tool_name=None, tool_calls_json=None):
    """Insert one message into a session's history."""
    conn = get_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO messages (session_id, role, content, tool_call_id, tool_name, tool_calls_json, timestamp)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (session_id, role, content, tool_call_id, tool_name, tool_calls_json, datetime.now().isoformat())
        )
        cur.execute(
            "UPDATE sessions SET updated_at = ? WHERE id = ?",
            (datetime.now().isoformat(), session_id)
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def load_messages(session_id, skip=0):
    """Load messages for a session in chronological order."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT role, content, tool_call_id, tool_name, tool_calls_json FROM messages WHERE session_id = ? ORDER BY id ASC",
            (session_id,)
        )
        rows = cur.fetchall()

        if skip:
            rows = rows[skip:]

        messages = []
        for row in rows:
            msg = {"role": row["role"], "content": row["content"]}
            if row["tool_call_id"]:
                msg["tool_call_id"] = row["tool_call_id"]
            if row["tool_name"]:
                msg["name"] = row["tool_name"]
            if row["tool_calls_json"]:
                try:
                    import json
                    msg["tool_calls"] = json.loads(row["tool_calls_json"])
                except (json.JSONDecodeError, TypeError):
                    pass
            messages.append(msg)
        return messages
    finally:
        conn.close()


def get_last_message_id(session_id: int) -> int:
    """Return the highest message ID in a session, or 0 if no messages exist."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT MAX(id) as max_id FROM messages WHERE session_id = ?", (session_id,))
        row = cur.fetchone()
        return row["max_id"] if row and row["max_id"] is not None else 0
    finally:
        conn.close()


def delete_messages_after(session_id: int, message_id: int):
    """Delete all messages in a session with id > message_id (used to roll back aborted turns)."""
    conn = get_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM messages WHERE session_id = ? AND id > ?",
            (session_id, message_id)
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_last_session_message(session_id):
    """Fetch the most recent user or assistant message for a session."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT role, content FROM messages WHERE session_id = ? AND role IN ('user', 'assistant') ORDER BY id DESC LIMIT 1",
            (session_id,)
        )
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_recent_messages(session_id, limit=3):
    """Fetch the last N user and assistant messages for a session in chronological order."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT role, content, timestamp FROM messages
               WHERE session_id = ? AND role IN ('user', 'assistant')
               ORDER BY id DESC LIMIT ?""",
            (session_id, limit)
        )
        rows = cur.fetchall()
        return [dict(r) for r in reversed(rows)]
    finally:
        conn.close()


def list_sessions_with_preview():
    """Return all sessions enriched with message count and latest message preview."""
    sessions = list_sessions()
    conn = get_connection()
    try:
        cur = conn.cursor()
        for s in sessions:
            sid = s["id"]
            cur.execute("SELECT COUNT(*) as cnt FROM messages WHERE session_id = ?", (sid,))
            s["msg_count"] = cur.fetchone()["cnt"]
            cur.execute(
                "SELECT role, content FROM messages WHERE session_id = ? AND role IN ('user', 'assistant') ORDER BY id DESC LIMIT 1",
                (sid,)
            )
            last_row = cur.fetchone()
            s["last_message"] = dict(last_row) if last_row else None
        return sessions
    finally:
        conn.close()


# --- Long-term memory & Pinned Facts ---

def get_all_fact_texts():
    """Fetch all existing fact texts from memory table."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT fact_text FROM memory")
        rows = cur.fetchall()
        return [row["fact_text"] for row in rows]
    finally:
        conn.close()


def load_pinned_memory():
    """Fetch all pinned Core Memory facts."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, fact_text FROM memory WHERE is_pinned = 1 ORDER BY id ASC")
        rows = cur.fetchall()
        return [r["fact_text"] for r in rows]
    finally:
        conn.close()


def load_pinned_memory_with_ids():
    """
    Fetch all pinned Core Memory facts with database IDs.

    Returns:
        list[dict]: List of dicts with 'id' and 'text'.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, fact_text FROM memory WHERE is_pinned = 1 ORDER BY id ASC")
        rows = cur.fetchall()
        return [{"id": r["id"], "text": r["fact_text"]} for r in rows]
    finally:
        conn.close()


def delete_pinned_fact(identifier):
    """
    Unpin or remove a pinned memory item by integer ID or exact text string.

    Args:
        identifier (int | str): Database ID or fact text to remove.

    Returns:
        bool: True if an item was removed/unpinned, False otherwise.
    """
    conn = get_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")
        cur = conn.cursor()
        if isinstance(identifier, int) or (isinstance(identifier, str) and identifier.isdigit()):
            fact_id = int(identifier)
            cur.execute("DELETE FROM memory WHERE id = ? AND is_pinned = 1", (fact_id,))
        else:
            cur.execute("DELETE FROM memory WHERE fact_text = ? AND is_pinned = 1", (str(identifier),))
        rowcount = cur.rowcount
        conn.commit()
        return rowcount > 0
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def set_fact_pinned_status(fact_identifier, is_pinned=True):
    """Pin or unpin a memory fact by text or ID."""
    conn = get_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")
        cur = conn.cursor()
        pinned_val = 1 if is_pinned else 0
        if isinstance(fact_identifier, int):
            cur.execute("UPDATE memory SET is_pinned = ? WHERE id = ?", (pinned_val, fact_identifier))
        else:
            cur.execute("UPDATE memory SET is_pinned = ? WHERE fact_text = ?", (pinned_val, str(fact_identifier)))
        conn.commit()
        return cur.rowcount > 0
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def delete_fact_by_text(fact_text, replaced_by_text=None):
    """Archive a fact to memory_history before deleting (Soft Delete / Audit Trail)."""
    now = datetime.now().isoformat()
    conn = get_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")
        cur = conn.cursor()
        cur.execute("SELECT id, fact_text, embedding FROM memory WHERE fact_text = ?", (fact_text,))
        rows = cur.fetchall()
        for row in rows:
            cur.execute(
                "INSERT INTO memory_history (original_fact_id, fact_text, embedding, action, replaced_by_text, archived_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (row["id"], row["fact_text"], row["embedding"], "SUPERSEDED", replaced_by_text, now),
            )
        cur.execute("DELETE FROM memory WHERE fact_text = ?", (fact_text,))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def fact_exists(fact_text, similarity_threshold=0.88):
    """
    Semantic duplicate check using vector embedding similarity.
    Falls back to exact string matching if embedding calculation is unavailable.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT fact_text, embedding FROM memory")
        rows = cur.fetchall()
        if not rows:
            return False

        # Try semantic embedding check first
        try:
            query_vec = embed_passage(fact_text)
            for row in rows:
                if row["embedding"]:
                    vec = vector_from_json(row["embedding"])
                    if cosine_similarity(query_vec, vec) >= similarity_threshold:
                        return True
        except Exception:
            # Fallback to exact or case-insensitive string matching
            pass

        fact_lower = fact_text.strip().lower()
        for row in rows:
            if row["fact_text"].strip().lower() == fact_lower:
                return True
        return False
    finally:
        conn.close()


def save_memory_fact(fact_text, source_session_id=None, is_pinned=False):
    """Store one long-term fact, generating embeddings under a BEGIN IMMEDIATE transaction."""
    now = datetime.now().isoformat()
    try:
        vec = embed_passage(fact_text)
        vec_json = vector_to_json(vec)
    except Exception:
        vec_json = None

    conn = get_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")
        cur = conn.cursor()
        if source_session_id is not None:
            # Ensure session row exists if provided
            cur.execute(
                "INSERT OR IGNORE INTO sessions (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (source_session_id, f"Session #{source_session_id}", now, now)
            )
        cur.execute(
            "INSERT INTO memory (fact_text, embedding, source_session_id, extracted_at, last_used_at, is_pinned) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (fact_text, vec_json, source_session_id, now, now, 1 if is_pinned else 0),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# --- Hybrid Retrieval ---

MEMORY_FACT_LIMIT = 30
ALPHA_RECENCY = 0.3
BETA_SIMILARITY = 0.7
RECENCY_HALF_LIFE_HOURS = 24


def _recency_score(last_used_iso, now):
    try:
        last_used = datetime.fromisoformat(last_used_iso)
        hours_ago = max((now - last_used).total_seconds() / 3600, 0)
        return math.exp(-hours_ago / RECENCY_HALF_LIFE_HOURS)
    except Exception:
        return 0.5


def load_relevant_memory(current_message, limit=MEMORY_FACT_LIMIT,
                         alpha=ALPHA_RECENCY, beta=BETA_SIMILARITY,
                         session_id=None):
    """
    Hybrid retrieval for unpinned dynamic memory facts: score = alpha * recency + beta * cosine_similarity.
    Filters unpinned facts by session_id when provided, isolating session memories.
    Pinned facts are excluded here since they are loaded separately via load_pinned_memory().
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        if session_id is not None:
            cur.execute(
                "SELECT id, fact_text, embedding, last_used_at FROM memory "
                "WHERE (is_pinned = 0 OR is_pinned IS NULL) AND (source_session_id = ? OR source_session_id IS NULL)",
                (session_id,)
            )
        else:
            cur.execute("SELECT id, fact_text, embedding, last_used_at FROM memory WHERE (is_pinned = 0 OR is_pinned IS NULL)")
        rows = cur.fetchall()

        if not rows:
            return []

        now = datetime.now()
        scored = []

        try:
            query_vec = embed_query(current_message)
            for row in rows:
                sim = 0.0
                if row["embedding"]:
                    fact_vec = vector_from_json(row["embedding"])
                    sim = cosine_similarity(query_vec, fact_vec)
                rec = _recency_score(row["last_used_at"], now)
                scored.append((alpha * rec + beta * sim, row))
        except Exception:
            # Fallback to recency-only sorting if embedding lookup fails
            for row in rows:
                rec = _recency_score(row["last_used_at"], now)
                scored.append((rec, row))

        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[:limit]

        now_iso = now.isoformat()
        conn.execute("BEGIN IMMEDIATE")
        cur.executemany(
            "UPDATE memory SET last_used_at = ? WHERE id = ?",
            [(now_iso, item[1]["id"]) for item in top],
        )
        conn.commit()
        return [item[1]["fact_text"] for item in top]
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def load_all_memory(limit=MEMORY_FACT_LIMIT, session_id=None):
    """Backward-compat fallback: top N unpinned facts by last_used_at (scoped to session_id if provided)."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        if session_id is not None:
            cur.execute(
                "SELECT id, fact_text FROM memory "
                "WHERE (is_pinned = 0 OR is_pinned IS NULL) AND (source_session_id = ? OR source_session_id IS NULL) "
                "ORDER BY last_used_at DESC LIMIT ?",
                (session_id, limit)
            )
        else:
            cur.execute("SELECT id, fact_text FROM memory WHERE (is_pinned = 0 OR is_pinned IS NULL) ORDER BY last_used_at DESC LIMIT ?", (limit,))
        rows = cur.fetchall()

        if rows:
            now = datetime.now().isoformat()
            conn.execute("BEGIN IMMEDIATE")
            cur.executemany(
                "UPDATE memory SET last_used_at = ? WHERE id = ?",
                [(now, r["id"]) for r in rows],
            )
            conn.commit()

        return [r["fact_text"] for r in rows]
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def load_all_memory_with_ids(limit=MEMORY_FACT_LIMIT, session_id=None):
    """Fetch top N unpinned facts along with database IDs [(id, fact_text), ...] (scoped to session_id if provided)."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        if session_id is not None:
            cur.execute(
                "SELECT id, fact_text FROM memory "
                "WHERE (is_pinned = 0 OR is_pinned IS NULL) AND (source_session_id = ? OR source_session_id IS NULL) "
                "ORDER BY last_used_at DESC LIMIT ?",
                (session_id, limit)
            )
        else:
            cur.execute("SELECT id, fact_text FROM memory WHERE (is_pinned = 0 OR is_pinned IS NULL) ORDER BY last_used_at DESC LIMIT ?", (limit,))
        rows = cur.fetchall()

        if rows:
            now = datetime.now().isoformat()
            conn.execute("BEGIN IMMEDIATE")
            cur.executemany(
                "UPDATE memory SET last_used_at = ? WHERE id = ?",
                [(now, r["id"]) for r in rows],
            )
            conn.commit()

        return [(r["id"], r["fact_text"]) for r in rows]
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def count_memory(include_pinned=True, session_id=None):
    """Total number of long-term facts in the DB (optionally filtering by session_id)."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        if include_pinned:
            cur.execute("SELECT COUNT(*) AS cnt FROM memory")
        elif session_id is not None:
            cur.execute(
                "SELECT COUNT(*) AS cnt FROM memory "
                "WHERE (is_pinned = 0 OR is_pinned IS NULL) AND (source_session_id = ? OR source_session_id IS NULL)",
                (session_id,)
            )
        else:
            cur.execute("SELECT COUNT(*) AS cnt FROM memory WHERE (is_pinned = 0 OR is_pinned IS NULL)")
        return cur.fetchone()["cnt"]
    finally:
        conn.close()


def replace_all_memory(new_facts, target_ids=None, min_retention_ratio=0.5, source_session_id=None):
    """
    Safely swap unpinned facts with a consolidated set.
    Pinned facts are strictly protected and will never be deleted by consolidation.
    1. If target_ids is provided: ONLY delete & archive the specific unpinned facts that were target of consolidation.
    2. Safety Guardrail: Rejects replacement if facts drop by >50% unexpectedly to prevent hallucination loss.
    3. Audit Trail: Archives target old facts to `memory_history` before deletion.
    """
    if not new_facts:
        print("  [Safety Alert]: Consolidation proposed empty facts list. Aborting replace_all_memory.")
        return False

    conn = get_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")
        cur = conn.cursor()

        if target_ids is not None:
            if not target_ids:
                conn.rollback()
                return True
            placeholders = ",".join("?" * len(target_ids))
            cur.execute(f"SELECT id, fact_text, embedding FROM memory WHERE id IN ({placeholders}) AND (is_pinned = 0 OR is_pinned IS NULL)", tuple(target_ids))
            old_rows = cur.fetchall()
        else:
            cur.execute("SELECT id, fact_text, embedding FROM memory WHERE (is_pinned = 0 OR is_pinned IS NULL)")
            old_rows = cur.fetchall()

        # Safety Guardrail: If old target memory had >= 5 facts, ensure LLM doesn't wipe out >50% in one go
        if len(old_rows) >= 5 and len(new_facts) < (len(old_rows) * min_retention_ratio):
            print(f"  [Safety Alert]: Consolidation dropped facts from {len(old_rows)} to {len(new_facts)} (>50% drop). Aborting to prevent hallucination loss.")
            conn.rollback()
            return False

        now = datetime.now().isoformat()
        # 1. Audit Log: Archive target old facts before deleting
        for r in old_rows:
            cur.execute(
                "INSERT INTO memory_history (original_fact_id, fact_text, embedding, action, replaced_by_text, archived_at) "
                "VALUES (?, ?, ?, ?, NULL, ?)",
                (r["id"], r["fact_text"], r["embedding"], "CONSOLIDATED_ARCHIVED", now),
            )

        # 2. Delete targeted old unpinned facts
        if target_ids is not None:
            placeholders = ",".join("?" * len(target_ids))
            cur.execute(f"DELETE FROM memory WHERE id IN ({placeholders}) AND (is_pinned = 0 OR is_pinned IS NULL)", tuple(target_ids))
        else:
            cur.execute("DELETE FROM memory WHERE (is_pinned = 0 OR is_pinned IS NULL)")

        # 3. Re-embed and insert new consolidated facts (as unpinned, tied to source_session_id if provided)
        try:
            vectors = embed_passages_batch(new_facts)
            cur.executemany(
                "INSERT INTO memory (fact_text, embedding, source_session_id, extracted_at, last_used_at, is_pinned) "
                "VALUES (?, ?, ?, ?, ?, 0)",
                [(f, vector_to_json(v), source_session_id, now, now) for f, v in zip(new_facts, vectors)],
            )
        except Exception:
            cur.executemany(
                "INSERT INTO memory (fact_text, embedding, source_session_id, extracted_at, last_used_at, is_pinned) "
                "VALUES (?, NULL, ?, ?, ?, 0)",
                [(f, source_session_id, now, now) for f in new_facts],
            )

        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"  [Error]: replace_all_memory failed ({e})")
        return False
    finally:
        conn.close()


def archive_messages(session_id, messages):
    """Move compacted-out messages into cold storage."""
    if not messages:
        return
    now = datetime.now().isoformat()
    conn = get_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")
        cur = conn.cursor()
        cur.executemany(
            "INSERT OR IGNORE INTO archived_messages (session_id, role, content, archived_at) VALUES (?, ?, ?, ?)",
            [(session_id, m.get("role", "unknown"), m.get("content") or "", now) for m in messages]
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def load_archived_messages(session_id):
    """Load a session's archived messages."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT role, content, archived_at FROM archived_messages WHERE session_id = ? ORDER BY id ASC",
            (session_id,)
        )
        rows = cur.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


# --- Compaction watermark ---

def get_compaction_state(session_id):
    """Return (archived_count, last_summary) for a session."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT archived_count, last_summary FROM sessions WHERE id = ?", (session_id,))
        row = cur.fetchone()
        if row:
            return row["archived_count"] or 0, row["last_summary"]
        return 0, None
    finally:
        conn.close()


def update_compaction_state(session_id, archived_count, summary):
    """Persist compaction watermark and summary for a session."""
    conn = get_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")
        cur = conn.cursor()
        cur.execute(
            "UPDATE sessions SET archived_count = ?, last_summary = ? WHERE id = ?",
            (archived_count, summary, session_id)
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()