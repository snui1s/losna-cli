"""
embedding_utils.py — OpenRouter vector embedding helpers.
Uses requests.post to send texts to OpenRouter google/gemini-embedding-2.
"""

import json
import math
import requests

from . import config

OPENROUTER_EMBEDDING_URL = "https://openrouter.ai/api/v1/embeddings"
EMBEDDING_MODEL = "google/gemini-embedding-2"


def get_embeddings(texts, is_query=False):
    """
    Fetch embeddings from OpenRouter using google/gemini-embedding-2.
    """
    api_key = config.OPENROUTER_API_KEY
    if not api_key:
        raise ValueError(
            "OPENROUTER_API_KEY is not set in configuration."
        )

    resp = requests.post(
        OPENROUTER_EMBEDDING_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost",
            "X-Title": "Losna CLI Agent"
        },
        json={"model": EMBEDDING_MODEL, "input": texts},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()

    # Sort by index to preserve input order
    items = sorted(data["data"], key=lambda x: x["index"])
    return [item["embedding"] for item in items]


# ── convenience wrappers ──────────────────────────────────────────

def embed_passage(text):
    """Embed a single fact/passage."""
    return get_embeddings([text], is_query=False)[0]


def embed_passages_batch(texts):
    """Embed multiple facts/passages in one API call."""
    if not texts:
        return []
    return get_embeddings(texts, is_query=False)


def embed_query(text):
    """Embed a single query/user message."""
    return get_embeddings([text], is_query=True)[0]


# ── vector math ───────────────────────────────────────────────────

def cosine_similarity(vec_a, vec_b):
    """Cosine similarity between two float vectors."""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    na = math.sqrt(sum(a * a for a in vec_a))
    nb = math.sqrt(sum(b * b for b in vec_b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


def vector_to_json(vec):
    """Serialize a float vector to a JSON string (for SQLite TEXT column)."""
    return json.dumps(vec)


def vector_from_json(json_str):
    """Deserialize a float vector from a JSON string."""
    if not json_str:
        return []
    try:
        return json.loads(json_str)
    except Exception:
        return []
