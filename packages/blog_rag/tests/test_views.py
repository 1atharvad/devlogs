import pytest
from unittest.mock import MagicMock, patch


class TestChatView:
    def _mock_agent_result(self, answer="Test answer.", tool_content=None):
        """
        Build a minimal agent result dict.

        tool_content: if provided, inserts a ToolMessage before the final
        answer message so that _extract_sources has something to parse.
        """
        from langchain_core.messages import ToolMessage
        messages = []
        if tool_content:
            tool_msg = ToolMessage(content=tool_content, tool_call_id="call_1")
            messages.append(tool_msg)
        final_msg = MagicMock()
        final_msg.content = answer
        messages.append(final_msg)
        return {"messages": messages}

    @patch("blog_rag.views.rag_agent")
    def test_returns_answer_and_session_id(self, mock_agent, api_client):
        mock_agent.invoke.return_value = self._mock_agent_result()
        response = api_client.post(
            "/chat/",
            {"message": "what is rate limiting?"},
            format="json",
        )
        assert response.status_code == 200
        assert response.data["answer"] == "Test answer."
        assert "session_id" in response.data
        assert "sources" in response.data

    @patch("blog_rag.views.rag_agent")
    def test_reuses_provided_session_id(self, mock_agent, api_client):
        mock_agent.invoke.return_value = self._mock_agent_result()
        response = api_client.post(
            "/chat/",
            {"message": "follow up", "session_id": "my-session-123"},
            format="json",
        )
        assert response.status_code == 200
        assert response.data["session_id"] == "my-session-123"

    @patch("blog_rag.views.rag_agent")
    def test_generates_session_id_when_absent(self, mock_agent, api_client):
        mock_agent.invoke.return_value = self._mock_agent_result()
        response = api_client.post(
            "/chat/",
            {"message": "hello"},
            format="json",
        )
        assert response.status_code == 200
        assert len(response.data["session_id"]) == 36  # UUID format

    @patch("blog_rag.views.rag_agent")
    def test_link_injected_into_message(self, mock_agent, api_client):
        mock_agent.invoke.return_value = self._mock_agent_result()
        api_client.post(
            "/chat/",
            {"message": "explain this", "link": "https://blog.example.com/post"},
            format="json",
        )
        call_args = mock_agent.invoke.call_args
        human_message = call_args[0][0]["messages"][0]
        assert "https://blog.example.com/post" in human_message.content

    @patch("blog_rag.views.rag_agent")
    def test_sources_extracted_from_tool_messages(self, mock_agent, api_client):
        tool_content = (
            "[Rate Limiting with Nginx](https://blog.example.com/rate-limiting)\n"
            "Some chunk content here.\n\n"
            "[Docker Basics](https://blog.example.com/docker)\n"
            "Another chunk."
        )
        mock_agent.invoke.return_value = self._mock_agent_result(tool_content=tool_content)
        response = api_client.post("/chat/", {"message": "nginx?"}, format="json")
        assert response.status_code == 200
        sources = response.data["sources"]
        assert len(sources) == 2
        assert sources[0] == {"title": "Rate Limiting with Nginx", "source": "https://blog.example.com/rate-limiting"}
        assert sources[1] == {"title": "Docker Basics", "source": "https://blog.example.com/docker"}

    @patch("blog_rag.views.rag_agent")
    def test_sources_deduplicated(self, mock_agent, api_client):
        # Same URL appearing twice (e.g. two chunks from the same post)
        tool_content = (
            "[Same Post](https://blog.example.com/post)\nchunk one.\n\n"
            "[Same Post](https://blog.example.com/post)\nchunk two."
        )
        mock_agent.invoke.return_value = self._mock_agent_result(tool_content=tool_content)
        response = api_client.post("/chat/", {"message": "hello"}, format="json")
        assert len(response.data["sources"]) == 1

    @patch("blog_rag.views.rag_agent")
    def test_sources_empty_when_no_tool_called(self, mock_agent, api_client):
        # Agent answered from history — no ToolMessage in result
        mock_agent.invoke.return_value = self._mock_agent_result()
        response = api_client.post("/chat/", {"message": "follow up"}, format="json")
        assert response.data["sources"] == []

    def test_missing_message_returns_400(self, api_client):
        response = api_client.post("/chat/", {}, format="json")
        assert response.status_code == 400


class TestSearchView:
    @patch("blog_rag.views.get_retriever")
    def test_returns_matching_docs(self, mock_get_retriever, api_client, sample_docs):
        mock_get_retriever.return_value.invoke.return_value = sample_docs
        response = api_client.get("/search/?q=nginx")
        assert response.status_code == 200
        assert len(response.data) == 2
        assert response.data[0]["title"] == "Rate Limiting with Nginx"
        assert "content" in response.data[0]
        assert "source" in response.data[0]

    @patch("blog_rag.views.get_retriever")
    def test_passes_k_to_retriever(self, mock_get_retriever, api_client, sample_docs):
        mock_get_retriever.return_value.invoke.return_value = sample_docs[:1]
        response = api_client.get("/search/?q=nginx&k=1")
        assert response.status_code == 200
        mock_get_retriever.return_value.invoke.assert_called_once_with("nginx", k=1)

    def test_missing_q_returns_400(self, api_client):
        response = api_client.get("/search/")
        assert response.status_code == 400
