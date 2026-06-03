from django.conf import settings

DEFAULTS = {
    "GOOGLE_API_KEY": None,
    "EMBEDDING_MODEL": "models/gemini-embedding-001",
    "EMBEDDING_DIMENSIONS": 768,
    "OPENROUTER_API_KEY": None,
    "OPENROUTER_BASE_URL": "https://openrouter.ai/api/v1",
    "CHAT_MODEL": "openai/gpt-4o-mini",
    "TOP_K": 5,
    "CHUNK_SIZE": 500,
    "CHUNK_OVERLAP": 50,
}


def get(key: str):
    rag_settings = getattr(settings, "BLOG_RAG", {})
    return rag_settings.get(key, DEFAULTS[key])
