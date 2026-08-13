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

    Args:
        texts (list[str]): List of input text passages to embed.
        is_query (bool, optional): Whether input is a search query. Defaults to False.

    Returns:
        list[list[float]]: List of vector embeddings.
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


def embed_passage(text):
    """
    Embed a single fact or code passage.

    Args:
        text (str): Input text string.

    Returns:
        list[float]: Vector embedding.
    """
    return get_embeddings([text], is_query=False)[0]


def embed_passages_batch(texts):
    """
    Embed multiple facts or passages in a single API call batch.

    Args:
        texts (list[str]): Input list of text strings.

    Returns:
        list[list[float]]: List of vector embeddings.
    """
    if not texts:
        return []
    return get_embeddings(texts, is_query=False)


def embed_query(text):
    """
    Embed a single search query or user prompt.

    Args:
        text (str): Query string.

    Returns:
        list[float]: Vector embedding.
    """
    return get_embeddings([text], is_query=True)[0]


def cosine_similarity(vec_a, vec_b):
    """
    Computes cosine similarity between two float vectors.

    Args:
        vec_a (list[float]): First vector.
        vec_b (list[float]): Second vector.

    Returns:
        float: Cosine similarity score between -1.0 and 1.0.
    """
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    na = math.sqrt(sum(a * a for a in vec_a))
    nb = math.sqrt(sum(b * b for b in vec_b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


def vector_to_json(vec):
    """
    Serialize a float vector to a JSON string for SQLite storage.

    Args:
        vec (list[float]): Vector embedding.

    Returns:
        str: JSON string representation of the vector.
    """
    return json.dumps(vec)


def vector_from_json(json_str):
    """
    Deserialize a float vector from a JSON string.

    Args:
        json_str (str): JSON string representation of vector.

    Returns:
        list[float]: Deserialized vector list.
    """
    if not json_str:
        return []
    try:
        return json.loads(json_str)
    except Exception:
        return []
