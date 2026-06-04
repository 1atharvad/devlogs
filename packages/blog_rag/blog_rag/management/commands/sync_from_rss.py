"""
Management command: sync_from_rss

Reads a blog's RSS feed, fetches the full post body for each item via the
apiUrl field in the feed, splits the text into overlapping chunks, embeds
each chunk with Gemini, and upserts the results into the DocumentChunk table.

Usage:
    python manage.py sync_from_rss <rss_url> [--force]

Skip/update logic:
    - If a post's document_id already exists in the DB and modified_time has
      not changed, the post is skipped.
    - If modified_time is newer, the old chunks are deleted and re-embedded.
    - --force re-embeds every post regardless of modified_time.

Rate limiting:
    Gemini's embedding API enforces per-minute quotas. _embed_with_retry
    catches HTTP 429 responses and waits 60 seconds before retrying (up to
    3 attempts total).
"""

import json
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime

from django.core.management.base import BaseCommand
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_google_genai._common import GoogleGenerativeAIError
from langchain_text_splitters import RecursiveCharacterTextSplitter


class Command(BaseCommand):
    help = "Sync blog posts from RSS feed into the RAG vector store"

    def add_arguments(self, parser):
        """Register CLI arguments: rss_url (positional) and --force (flag)."""
        parser.add_argument("rss_url", help="URL of the RSS feed")
        parser.add_argument(
            "--force",
            action="store_true",
            help="Re-embed all posts regardless of modified time",
        )

    def _embed_with_retry(self, embeddings, chunks, max_retries=3):
        """
        Call embeddings.embed_documents(chunks), retrying on HTTP 429.

        Waits 60 seconds between attempts. Raises the original error if all
        retries are exhausted or if the error is not rate-limit related.
        """
        for attempt in range(max_retries):
            try:
                return embeddings.embed_documents(chunks)
            except GoogleGenerativeAIError as e:
                if "429" in str(e) and attempt < max_retries - 1:
                    self.stdout.write(f"  rate limited, waiting 60s...")
                    time.sleep(60)
                else:
                    raise

    def handle(self, *args, **options):
        """
        Main entry point called by Django's management framework.

        Fetches the RSS feed, iterates over every <item>, and for each post:
        1. Checks whether a chunk with the same document_id already exists.
        2. Skips, deletes-and-re-embeds, or creates fresh chunks as needed.
        3. Prints a one-line status per post (skip / update / new).
        4. Prints a summary count at the end.
        """
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
            vectors = self._embed_with_retry(embeddings, chunks)

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
