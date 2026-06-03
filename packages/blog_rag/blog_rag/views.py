from rest_framework.response import Response
from rest_framework.views import APIView

from .rag.graph import rag_graph
from .rag.retriever import get_retriever
from .serializers import ChatRequestSerializer, SearchQuerySerializer


class ChatView(APIView):
    """POST {"message": "..."} → {"answer": "...", "sources": [...]}"""

    def post(self, request):
        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        question = serializer.validated_data["message"]
        result = rag_graph.invoke({
            "question": question,
            "documents": [],
            "answer": "",
            "sources": [],
        })
        return Response({"answer": result["answer"], "sources": result["sources"]})


class SearchView(APIView):
    """GET ?q=...&k=5 → [{"title": ..., "source": ..., "content": ...}]"""

    def get(self, request):
        serializer = SearchQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        query = serializer.validated_data["q"]
        k = serializer.validated_data.get("k")
        docs = get_retriever().invoke(query, k=k)
        return Response([
            {
                "title": doc.metadata.get("title", ""),
                "source": doc.metadata.get("source", ""),
                "content": doc.page_content,
            }
            for doc in docs
        ])
