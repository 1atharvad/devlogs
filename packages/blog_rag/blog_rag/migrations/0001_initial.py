import pgvector.django
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []

    operations = [
        migrations.RunSQL(
            "CREATE EXTENSION IF NOT EXISTS vector;",
            reverse_sql="DROP EXTENSION IF EXISTS vector;",
        ),
        migrations.CreateModel(
            name="DocumentChunk",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("document_id", models.CharField(db_index=True, max_length=512)),
                ("source", models.CharField(max_length=512)),
                ("title", models.CharField(blank=True, max_length=255)),
                ("content", models.TextField()),
                ("metadata", models.JSONField(default=dict)),
                ("embedding", pgvector.django.VectorField(dimensions=1536)),
                ("modified_time", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.AddIndex(
            model_name="documentchunk",
            index=pgvector.django.HnswIndex(
                name="doc_chunk_embedding_hnsw_idx",
                fields=["embedding"],
                m=16,
                ef_construction=64,
                opclasses=["vector_cosine_ops"],
            ),
        ),
    ]
