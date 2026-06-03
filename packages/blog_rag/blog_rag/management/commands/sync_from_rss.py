import json
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime

from django.core.management.base import BaseCommand
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


class Command(BaseCommand):
    help = "Sync blog posts from RSS feed into the RAG vector store"

    def add_arguments(self, parser):
        parser.add_argument("rss_url", help="URL of the RSS feed")
        parser.add_argument(
            "--force",
            action="store_true",
            help="Re-embed all posts regardless of modified time",
        )

    def handle(self, *args, **options):
        from ...conf import get as rag_setting
        from ...models import DocumentChunk

        rss_url = options["rss_url"]
        force = options["force"]

        self.stdout.write(f"Fetching RSS: {rss_url}")
        with urllib.request.urlopen(rss_url) as r:
            root = ET.fromstring(r.read())

        items = root.findall("./channel/item")
        self.stdout.write(f"Found {len(items)} posts\n")

        embeddings = GoogleGenerativeAIEmbeddings(
            model=rag_setting("EMBEDDING_MODEL"),
            google_api_key=rag_setting("GOOGLE_API_KEY"),
            output_dimensionality=rag_setting("EMBEDDING_DIMENSIONS"),
        )
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=rag_setting("CHUNK_SIZE"),
            chunk_overlap=rag_setting("CHUNK_OVERLAP"),
        )

        stats = {"new": 0, "updated": 0, "skipped": 0}

        for item in items:
            api_url = item.findtext("apiUrl")
            if not api_url:
                continue

            with urllib.request.urlopen(api_url) as r:
                post = json.loads(r.read())

            document_id = post["id"]
            updated_str = post.get("updatedDate") or post["pubDate"]
            updated_at = datetime.fromisoformat(updated_str.replace("Z", "+00:00"))

            existing = DocumentChunk.objects.filter(document_id=document_id).first()

            if existing and not force:
                if existing.modified_time and existing.modified_time >= updated_at:
                    self.stdout.write(f"  skip    {document_id}")
                    stats["skipped"] += 1
                    continue
                DocumentChunk.objects.filter(document_id=document_id).delete()
                self.stdout.write(f"  update  {document_id}")
                stats["updated"] += 1
            else:
                if existing:
                    DocumentChunk.objects.filter(document_id=document_id).delete()
                self.stdout.write(f"  new     {document_id}")
                stats["new"] += 1

            chunks = splitter.split_text(post["body"])
            vectors = embeddings.embed_documents(chunks)

            DocumentChunk.objects.bulk_create([
                DocumentChunk(
                    document_id=document_id,
                    source=post["url"],
                    title=post["title"],
                    content=chunk,
                    metadata={
                        "category": post.get("category", ""),
                        "tags": post.get("tags", []),
                        "pub_date": post["pubDate"],
                    },
                    embedding=vector,
                    modified_time=updated_at,
                )
                for chunk, vector in zip(chunks, vectors)
            ])

        self.stdout.write(self.style.SUCCESS(
            f"\nDone — new: {stats['new']}  updated: {stats['updated']}  skipped: {stats['skipped']}"
        ))
