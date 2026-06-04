from django.db import migrations, models
from pgvector.django import VectorField


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
                ("embedding", VectorField(dimensions=3072)),
                ("modified_time", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
