from typing import TypedDict

from langchain_core.documents import Document
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph

from ..conf import get as rag_setting
from .prompts import RAG_PROMPT
from .retriever import get_retriever


class RAGState(TypedDict):
    question: str
    documents: list[Document]
    answer: str
    sources: list[dict]


def retrieve_node(state: RAGState) -> dict:
    docs = get_retriever().invoke(state["question"])
    return {"documents": docs}


def generate_node(state: RAGState) -> dict:
    llm = ChatOpenAI(
        model=rag_setting("CHAT_MODEL"),
        api_key=rag_setting("OPENROUTER_API_KEY"),
        base_url=rag_setting("OPENROUTER_BASE_URL"),
    )
    context = "\n\n".join(
        f"[{doc.metadata.get('title') or doc.metadata.get('source', '?')}]\n{doc.page_content}"
        for doc in state["documents"]
    )
    result = (RAG_PROMPT | llm).invoke({
        "context": context,
        "question": state["question"],
    })
    sources = [
        {"source": doc.metadata.get("source", ""), "title": doc.metadata.get("title", "")}
        for doc in state["documents"]
    ]
    return {"answer": result.content, "sources": sources}


def _build_graph():
    g = StateGraph(RAGState)
    g.add_node("retrieve", retrieve_node)
    g.add_node("generate", generate_node)
    g.add_edge(START, "retrieve")
    g.add_edge("retrieve", "generate")
    g.add_edge("generate", END)
    return g.compile()


rag_graph = _build_graph()
