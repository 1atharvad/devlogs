"""
Database models for the blog RAG package.

DocumentChunk is the only model — it holds one piece of a blog post along with
its pgvector embedding so that semantic similarity search can be performed
directly in PostgreSQL.
"""

from django.db import models
from pgvector.django import VectorField


class DocumentChunk(models.Model):
    """
    A single text chunk from a blog post, stored with its vector embedding.

    Each post is split into overlapping chunks by sync_from_rss. Multiple
    DocumentChunk rows share the same document_id (the post's unique ID from
    the CMS). The embedding column uses pgvector so that cosine-distance
    queries can rank chunks by semantic similarity to a search query.

    Fields:
        document_id  — CMS post ID; used to find all chunks for one post.
        source       — Canonical URL of the post (used as the citation link).
        title        — Post title (copied to every chunk for display).
        content      — The raw text of this chunk.
        metadata     — Extra JSON: category, tags, pub_date from the RSS feed.
        embedding    — 3072-dimensional Gemini embedding of `content`.
        modified_time — Last-updated timestamp from the CMS; used by
                        sync_from_rss to skip posts that haven't changed.
        created_at   — Row creation time (set automatically).
    """
    document_id = models.CharField(max_length=512, db_index=True)
    source = models.CharField(max_length=512)
    title = models.CharField(max_length=255, blank=True)
    content = models.TextField()
    metadata = models.JSONField(default=dict)
    embedding = VectorField(dimensions=3072)
    modified_time = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title or self.source} [{self.id}]"
