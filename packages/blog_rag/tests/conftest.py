import pytest
from django.conf import settings


def pytest_configure():
    settings.configure(
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": "blog_rag_test",
                "USER": "postgres",
                "PASSWORD": "",
                "HOST": "localhost",
                "PORT": "5432",
            }
        },
        INSTALLED_APPS=[
            "django.contrib.contenttypes",
            "django.contrib.auth",
            "rest_framework",
            "blog_rag",
        ],
        ROOT_URLCONF="blog_rag.urls",
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            }
        },
        BLOG_RAG={
            "GOOGLE_API_KEY": "test-key",
            "OPENROUTER_API_KEY": "test-key",
            "EMBEDDING_MODEL": "models/gemini-embedding-001",
            "EMBEDDING_DIMENSIONS": 3072,
            "TOP_K": 5,
        },
    )


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def sample_docs():
    from langchain_core.documents import Document
    return [
        Document(
            page_content="Rate limiting controls how many requests a client can make.",
            metadata={
                "source": "https://blog.example.com/rate-limiting",
                "title": "Rate Limiting with Nginx",
            },
        ),
        Document(
            page_content="Nginx proxy_pass forwards requests to upstream servers.",
            metadata={
                "source": "https://blog.example.com/nginx-proxy",
                "title": "Nginx Reverse Proxy",
            },
        ),
    ]
