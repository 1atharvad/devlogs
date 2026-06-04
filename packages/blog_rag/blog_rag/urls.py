"""
URL routing for the blog_rag package.

Mount these routes in the host project's urls.py with an include(), e.g.:

    path("rag/", include("blog_rag.urls")),

This exposes three endpoints:
    POST  rag/chat/    — conversational Q&A via the LangGraph agent
    GET   rag/search/  — raw vector similarity search, returns ranked chunks
    POST  rag/sync/    — webhook: re-syncs content from RSS (Vercel deploy hook)
"""

from django.urls import path

from .views import ChatView, SearchView, SyncView

urlpatterns = [
    path("chat/", ChatView.as_view(), name="blog-rag-chat"),
    path("search/", SearchView.as_view(), name="blog-rag-search"),
    path("sync/", SyncView.as_view(), name="blog-rag-sync"),
]
