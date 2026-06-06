"""
DRF API views exposed by the blog_rag package.

ChatView   — conversational endpoint backed by the LangGraph ReAct agent.
             Maintains per-session memory via session_id / thread_id.
SearchView — thin wrapper around the vector retriever for direct similarity
             search without going through the LLM.
SyncView   — called by GitHub Actions on deployment_status success.
             Runs sync_from_rss in a background thread so the response
             returns immediately.
"""

import hmac
import io
import queue
import re
import threading
import uuid

from django.http import StreamingHttpResponse

_sync_jobs: dict[str, queue.Queue] = {}

from langchain_core.messages import HumanMessage, ToolMessage
from rest_framework.response import Response
from rest_framework.views import APIView

_SOURCE_RE = re.compile(r'^\[(.+?)\]\((.+?)\)', re.MULTILINE)


def _extract_sources(messages: list) -> list[dict]:
    """
    Pull cited sources out of the agent's ToolMessage results.

    search_blog returns each chunk as "[Title](url)\ncontent". This function
    finds every such header across all tool call results for the current turn,
    deduplicates by URL, and returns them as {"title", "source"} dicts —
    matching the format the previous n8n pipeline used.
    """
    sources, seen = [], set()
    for msg in messages:
        if isinstance(msg, ToolMessage):
            for title, url in _SOURCE_RE.findall(msg.content):
                if url not in seen:
                    seen.add(url)
                    sources.append({"title": title, "source": url})
    return sources


from .conf import get as rag_setting
from .rag.graph import rag_agent
from .rag.retriever import get_retriever
from .serializers import ChatRequestSerializer, SearchQuerySerializer


class ChatView(APIView):
    """
    POST /chat/ — send a message to the RAG agent and get an answer.

    Request body (JSON):
        message     (str, required)  — the user's question.
        session_id  (str, optional)  — conversation thread identifier.
                                       Omit to start a new session; the
                                       generated UUID is returned so the
                                       client can pass it back on follow-ups.
        link        (str, optional)  — URL of the page the user is on.
                                       Appended to the message so the agent
                                       can treat it as additional context.

    Response (JSON):
        answer      (str)   — the agent's markdown-formatted response.
        session_id  (str)   — echo of the session_id used for this turn.
        sources     (list)  — deduplicated list of {"title", "source"} dicts
                              for every blog post the agent retrieved. Empty
                              list if the agent answered from history without
                              searching.
    """

    def post(self, request):
        """Validate input, invoke the agent, and return the answer."""
        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        question = serializer.validated_data["message"]
        link = serializer.validated_data.get("link", "")
        session_id = serializer.validated_data.get("session_id") or str(uuid.uuid4())

        input_message = f"{question}\n\n[User is currently viewing: {link}]" if link else question

        config = {"configurable": {"thread_id": session_id}}
        result = rag_agent.invoke(
            {"messages": [HumanMessage(content=input_message)]},
            config=config,
        )

        answer = result["messages"][-1].content
        sources = _extract_sources(result["messages"])
        return Response({"answer": answer, "session_id": session_id, "sources": sources})


class SearchView(APIView):
    """
    GET /search/ — run a vector similarity search and return ranked chunks.

    Query parameters:
        q  (str, required)       — search query text.
        k  (int, optional, 1–20) — max results to return (defaults to TOP_K).

    Response (JSON array):
        [{"title": str, "source": str, "content": str}, ...]

    This endpoint skips the LLM entirely — useful for debugging retrieval
    quality or building custom frontends that handle the LLM call themselves.
    """

    def get(self, request):
        """Validate params, query the retriever, and return ranked chunks."""
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


class SyncView(APIView):
    """
    POST /sync/         — start a background sync, returns {"job_id": "..."}
    GET  /sync/?job_id= — SSE stream of that job's log lines until done

    Auth: Bearer token in Authorization header (SYNC_SECRET setting).
    """

    def _authenticate(self, request):
        secret = rag_setting("SYNC_SECRET")
        if not secret:
            return Response({"detail": "unauthorized"}, status=401)
        token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
        if not hmac.compare_digest(token, secret):
            return Response({"detail": "unauthorized"}, status=401)
        return None

    def post(self, request):
        from django.core.management import call_command

        err = self._authenticate(request)
        if err:
            return err

        rss_url = rag_setting("RSS_URL")
        if not rss_url:
            return Response({"detail": "RSS_URL not configured"}, status=503)

        job_id = str(uuid.uuid4())
        log_queue: queue.Queue = queue.Queue()
        _sync_jobs[job_id] = log_queue

        class _Writer(io.StringIO):
            def write(self, s):
                if s.strip():
                    log_queue.put(s.rstrip())
                return len(s)

        def _run():
            call_command("sync_from_rss", rss_url, stdout=_Writer())
            log_queue.put(None)  # sentinel — job done

        threading.Thread(target=_run, daemon=True).start()
        return Response({"status": "sync started", "job_id": job_id}, status=202)

    def get(self, request):
        err = self._authenticate(request)
        if err:
            return err

        job_id = request.query_params.get("job_id")
        if not job_id or job_id not in _sync_jobs:
            return Response({"detail": "job not found"}, status=404)

        log_queue = _sync_jobs[job_id]

        def _stream():
            try:
                while True:
                    try:
                        line = log_queue.get(timeout=30)
                    except queue.Empty:
                        yield ": keepalive\n\n"
                        continue
                    if line is None:
                        yield "data: [done]\n\n"
                        break
                    yield f"data: {line}\n\n"
            finally:
                _sync_jobs.pop(job_id, None)

        return StreamingHttpResponse(_stream(), content_type="text/event-stream")
