from django.db import models
from pgvector.django import VectorField


class DocumentChunk(models.Model):
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
