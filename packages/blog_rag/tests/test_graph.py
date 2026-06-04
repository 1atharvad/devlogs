import pytest
from unittest.mock import MagicMock, patch


@patch("blog_rag.rag.graph.get_retriever")
def test_search_blog_tool_formats_output(mock_get_retriever, sample_docs):
    from blog_rag.rag.graph import search_blog

    mock_get_retriever.return_value.invoke.return_value = sample_docs
    result = search_blog.invoke("rate limiting")

    assert "Rate Limiting with Nginx" in result
    assert "Rate limiting controls how many requests" in result
    assert "https://blog.example.com/rate-limiting" in result


@patch("blog_rag.rag.graph.get_retriever")
def test_search_blog_tool_empty_results(mock_get_retriever):
    from blog_rag.rag.graph import search_blog

    mock_get_retriever.return_value.invoke.return_value = []
    result = search_blog.invoke("nonexistent topic")

    assert result == ""


@patch("blog_rag.rag.graph.get_retriever")
def test_rag_agent_invokes_with_thread_id(mock_get_retriever, sample_docs):
    from langchain_core.messages import HumanMessage, AIMessage
    from blog_rag.rag.graph import rag_agent

    mock_get_retriever.return_value.invoke.return_value = sample_docs

    with patch.object(rag_agent, "invoke") as mock_invoke:
        ai_msg = MagicMock(spec=AIMessage)
        ai_msg.content = "Rate limiting controls traffic."
        mock_invoke.return_value = {"messages": [ai_msg]}

        config = {"configurable": {"thread_id": "test-session-1"}}
        result = rag_agent.invoke(
            {"messages": [HumanMessage(content="what is rate limiting?")]},
            config=config,
        )

    mock_invoke.assert_called_once()
    call_config = mock_invoke.call_args.kwargs["config"]
    assert call_config["configurable"]["thread_id"] == "test-session-1"
    assert result["messages"][-1].content == "Rate limiting controls traffic."


def test_prompts_system_prompt_contains_rules():
    from blog_rag.rag.prompts import SYSTEM_PROMPT

    assert "search_blog" in SYSTEM_PROMPT
    assert "markdown" in SYSTEM_PROMPT
    assert "don't invent" in SYSTEM_PROMPT
