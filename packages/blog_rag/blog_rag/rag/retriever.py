"""
Vector retriever backed by pgvector and Google Gemini embeddings.

PgVectorRetriever is a singleton — the first call to PgVectorRetriever()
builds the Gemini embeddings client (which opens an httpx connection pool).
Every subsequent call returns the same instance, avoiding the overhead of
rebuilding that pool on every request.

get_retriever() is the public entry point used by views and the agent tool.
"""

from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from pgvector.django import CosineDistance

from ..conf import get as rag_setting


class PgVectorRetriever:
    """
    Singleton retriever that performs cosine-distance search in PostgreSQL.

    On first instantiation it creates a GoogleGenerativeAIEmbeddings client
    (reads EMBEDDING_MODEL and GOOGLE_API_KEY from settings). The instance is
    cached on the class so the same client is reused for the lifetime of the
    process.
    """

    _instance: "PgVectorRetriever | None" = None

    def __new__(cls):
        """Return the existing instance, or create and cache a new one."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._embeddings = GoogleGenerativeAIEmbeddings(
                model=rag_setting("EMBEDDING_MODEL"),
                google_api_key=rag_setting("GOOGLE_API_KEY"),
            )
        return cls._instance

    def invoke(self, query: str, k: int | None = None) -> list[Document]:
        """
        Embed query and return the k most similar DocumentChunks.

        DocumentChunk is imported lazily here (not at module level) so that
        the module can be imported before Django's app registry is fully
        loaded — which matters during test collection.

        Args:
            query: natural-language search text.
            k:     number of results; falls back to the TOP_K setting if None.

        Returns:
            List of LangChain Document objects with page_content and metadata
            (source URL, title, and any extra fields from the chunk's metadata
            JSON column).
        """
        from ..models import DocumentChunk

        top_k = k or rag_setting("TOP_K")
        query_vector = self._embeddings.embed_query(query)

        chunks = (
            DocumentChunk.objects
            .order_by(CosineDistance("embedding", query_vector))[:top_k]
        )
        return [
            Document(
                page_content=chunk.content,
                metadata={
                    "source": chunk.source,
                    "title": chunk.title,
                    **chunk.metadata,
                },
            )
            for chunk in chunks
        ]


def get_retriever() -> PgVectorRetriever:
    """Return the singleton PgVectorRetriever instance."""
    return PgVectorRetriever()
