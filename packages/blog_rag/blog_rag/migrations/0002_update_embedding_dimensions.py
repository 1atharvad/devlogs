import pgvector.django
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("blog_rag", "0001_initial"),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name="documentchunk",
            name="doc_chunk_embedding_hnsw_idx",
        ),
        migrations.AlterField(
            model_name="documentchunk",
            name="embedding",
            field=pgvector.django.VectorField(dimensions=768),
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
