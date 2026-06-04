import pytest
from blog_rag.conf import get


def test_defaults_returned_when_not_overridden():
    assert get("EMBEDDING_MODEL") == "models/gemini-embedding-001"
    assert get("EMBEDDING_DIMENSIONS") == 3072
    assert get("TOP_K") == 5
    assert get("CHUNK_SIZE") == 500
    assert get("CHUNK_OVERLAP") == 50
    assert get("CHAT_MODEL") == "openai/gpt-4o-mini"


def test_overrides_from_blog_rag_settings():
    assert get("GOOGLE_API_KEY") == "test-key"
    assert get("OPENROUTER_API_KEY") == "test-key"


def test_unknown_key_raises():
    with pytest.raises(KeyError):
        get("NONEXISTENT_KEY")
