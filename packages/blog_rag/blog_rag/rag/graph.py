"""
LangGraph ReAct agent that powers the /chat/ endpoint.

The agent is built once at import time (module-level singleton) using
create_react_agent from langgraph.prebuilt. It receives a single tool —
search_blog — and decides on its own whether to call it based on the
conversation so far.

Conversation memory is stored in _memory (a MemorySaver). Each request passes
a thread_id via the LangGraph config, so separate sessions get separate
history. Note: MemorySaver is in-process only — history is lost on restart and
not shared across multiple workers. Switch to PostgresSaver for multi-process
deployments.
"""

from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from ..conf import get as rag_setting
from .prompts import SYSTEM_PROMPT
from .retriever import get_retriever


@tool
def search_blog(query: str) -> str:
    """Search blog posts and devlogs for information relevant to the query."""
    docs = get_retriever().invoke(query)
    return "\n\n".join(
        f"[{doc.metadata.get('title', '?')}]({doc.metadata.get('source', '')})\n{doc.page_content}"
        for doc in docs
    )


# MemorySaver is in-process only — history is lost on restart and not shared
# across multiple workers. For multi-process deployments use PostgresSaver.
_memory = MemorySaver()

rag_agent = create_react_agent(
    model=ChatOpenAI(
        model=rag_setting("CHAT_MODEL"),
        api_key=rag_setting("OPENROUTER_API_KEY"),
        base_url=rag_setting("OPENROUTER_BASE_URL"),
    ),
    tools=[search_blog],
    checkpointer=_memory,
    prompt=SYSTEM_PROMPT,
)
