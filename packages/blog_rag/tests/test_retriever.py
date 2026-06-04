import pytest
from unittest.mock import MagicMock, patch
from langchain_core.documents import Document


@patch("blog_rag.rag.retriever.GoogleGenerativeAIEmbeddings")
@patch("blog_rag.models.DocumentChunk")
def test_returns_documents(mock_chunk_cls, mock_embeddings_cls, sample_docs):
    from blog_rag.rag.retriever import PgVectorRetriever
    PgVectorRetriever._instance = None

    mock_embeddings_cls.return_value.embed_query.return_value = [0.1] * 3072

    mock_chunk = MagicMock()
    mock_chunk.content = sample_docs[0].page_content
    mock_chunk.source = sample_docs[0].metadata["source"]
    mock_chunk.title = sample_docs[0].metadata["title"]
    mock_chunk.metadata = {}

    mock_chunk_cls.objects.order_by.return_value.__getitem__ = MagicMock(
        return_value=iter([mock_chunk])
    )

    retriever = PgVectorRetriever()
    docs = retriever.invoke("rate limiting")

    assert isinstance(docs, list)
    for doc in docs:
        assert isinstance(doc, Document)
        assert "source" in doc.metadata
        assert "title" in doc.metadata


@patch("blog_rag.rag.retriever.GoogleGenerativeAIEmbeddings")
@patch("blog_rag.models.DocumentChunk")
def test_embed_query_called_with_query(mock_chunk_cls, mock_embeddings_cls):
    from blog_rag.rag.retriever import PgVectorRetriever
    PgVectorRetriever._instance = None

    mock_embed = mock_embeddings_cls.return_value
    mock_embed.embed_query.return_value = [0.1] * 3072
    mock_chunk_cls.objects.order_by.return_value.__getitem__ = MagicMock(
        return_value=iter([])
    )

    retriever = PgVectorRetriever()
    retriever.invoke("nginx config")

    mock_embed.embed_query.assert_called_once_with("nginx config")
