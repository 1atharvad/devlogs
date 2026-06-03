import os

from django.core.management.base import BaseCommand
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


class Command(BaseCommand):
    help = "Ingest markdown documents into the RAG vector store"

    def add_arguments(self, parser):
        parser.add_argument("path", help="Path to a markdown file or directory")
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete all existing chunks before ingesting",
        )
        parser.add_argument(
            "--glob",
            default="**/*.md",
            help="Glob pattern when path is a directory (default: **/*.md)",
        )

    def handle(self, *args, **options):
        from ...conf import get as rag_setting
        from ...models import DocumentChunk

        if options["clear"]:
            deleted, _ = DocumentChunk.objects.all().delete()
            self.stdout.write(f"Cleared {deleted} existing chunks")

        path = options["path"]
        embeddings = GoogleGenerativeAIEmbeddings(
            model=rag_setting("EMBEDDING_MODEL"),
            google_api_key=rag_setting("GOOGLE_API_KEY"),
            output_dimensionality=rag_setting("EMBEDDING_DIMENSIONS"),
        )
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=rag_setting("CHUNK_SIZE"),
            chunk_overlap=rag_setting("CHUNK_OVERLAP"),
        )

        if os.path.isdir(path):
            loader = DirectoryLoader(path, glob=options["glob"], loader_cls=TextLoader)
        else:
            loader = TextLoader(path)

        docs = loader.load()
        chunks = splitter.split_documents(docs)
        self.stdout.write(f"Loaded {len(docs)} docs → {len(chunks)} chunks")

        texts = [c.page_content for c in chunks]
        vectors = embeddings.embed_documents(texts)

        chunk_objects = [
            DocumentChunk(
                source=chunk.metadata.get("source", ""),
                title=os.path.splitext(
                    os.path.basename(chunk.metadata.get("source", ""))
                )[0].replace("-", " ").title(),
                content=chunk.page_content,
                metadata=chunk.metadata,
                embedding=vector,
            )
            for chunk, vector in zip(chunks, vectors)
        ]
        DocumentChunk.objects.bulk_create(chunk_objects)
        self.stdout.write(self.style.SUCCESS(f"Ingested {len(chunk_objects)} chunks"))
