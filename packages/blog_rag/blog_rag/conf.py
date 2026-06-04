"""
Settings bridge between this package and the host Django project.

The host project configures the package by adding a BLOG_RAG dict to its
settings.py. Any key not present there falls back to the DEFAULTS below.

Example host settings.py:
    BLOG_RAG = {
        "GOOGLE_API_KEY": "...",
        "OPENROUTER_API_KEY": "...",
    }
"""

from django.conf import settings

DEFAULTS = {
    "GOOGLE_API_KEY": None,
    "EMBEDDING_MODEL": "models/gemini-embedding-001",
    "EMBEDDING_DIMENSIONS": 3072,
    "OPENROUTER_API_KEY": None,
    "OPENROUTER_BASE_URL": "https://openrouter.ai/api/v1",
    "CHAT_MODEL": "openai/gpt-4o-mini",
    "TOP_K": 5,
    "CHUNK_SIZE": 500,
    "CHUNK_OVERLAP": 50,
    "RSS_URL": "https://blog.atharvadevasthali.com/rss.xml",
    "SYNC_SECRET": None,       # Required — set a long random string
}


def get(key: str):
    """Return the setting value for key, preferring the host's BLOG_RAG override."""
    rag_settings = getattr(settings, "BLOG_RAG", {})
    return rag_settings.get(key, DEFAULTS[key])
