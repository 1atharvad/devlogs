from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from pgvector.django import CosineDistance

from ..conf import get as rag_setting


class PgVectorRetriever:
    def __init__(self):
        self._embeddings = GoogleGenerativeAIEmbeddings(
            model=rag_setting("EMBEDDING_MODEL"),
            google_api_key=rag_setting("GOOGLE_API_KEY"),
            output_dimensionality=rag_setting("EMBEDDING_DIMENSIONS"),
        )

    def invoke(self, query: str, k: int | None = None) -> list[Document]:
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
    return PgVectorRetriever()
