"""LangGraph flow: plan → search → read → answer."""

from __future__ import annotations

from pathlib import Path
from typing import TypedDict

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph

from src.conversation import ChatMessage, build_search_query, format_history_for_prompt
from src.indexer import DEFAULT_INDEX_PATH
from src.openai_context import ProgressCallback, emit_progress, use_openai_api_key
from src.prompts import ANSWER_PROMPT, PLAN_PROMPT
from src.repo import (
    DEFAULT_REPO_PATH,
    extract_sources_from_search_results,
    read_repo_file,
)
from src.tools.search_tool import create_search_codebase_tool

load_dotenv()


class AnalysisState(TypedDict):
    question: str
    history: list[ChatMessage]
    repo_path: str
    index_path: str
    k: int
    model: str
    plan: str
    search_results: str
    file_contents: str
    answer: str


def _get_llm(model: str) -> ChatOpenAI:
    return ChatOpenAI(model=model, temperature=0)


def _format_plan_input(state: AnalysisState) -> str:
    history_text = format_history_for_prompt(state["history"])
    if not history_text:
        return state["question"]

    return (
        "Conversation history:\n"
        f"{history_text}\n\n"
        f"Current question: {state['question']}"
    )


def plan_step(state: AnalysisState) -> dict:
    """Step 1: plan how to answer the question."""
    llm = _get_llm(state["model"])
    response = llm.invoke(
        [
            SystemMessage(content=PLAN_PROMPT),
            HumanMessage(content=_format_plan_input(state)),
        ]
    )
    return {"plan": response.content}


def search_step(state: AnalysisState) -> dict:
    """Step 2: semantic search in the FAISS index."""
    search_tool = create_search_codebase_tool(
        index_path=state["index_path"],
        k=state["k"],
    )
    query = build_search_query(state["question"], state["history"])
    results = search_tool.invoke({"query": query})
    return {"search_results": results}


def read_step(state: AnalysisState) -> dict:
    """Step 3: read full files found during search."""
    sources = extract_sources_from_search_results(state["search_results"])
    chunks: list[str] = []

    for source in sources[:3]:
        try:
            chunks.append(read_repo_file(state["repo_path"], source))
        except (FileNotFoundError, ValueError) as error:
            chunks.append(f"File: {source}\n\nCould not read: {error}")

    if not chunks:
        return {"file_contents": "No files could be read from the search results."}

    return {"file_contents": "\n\n".join(chunks)}


def answer_step(state: AnalysisState) -> dict:
    """Step 4: synthesize the final answer."""
    llm = _get_llm(state["model"])
    history_text = format_history_for_prompt(state["history"])
    history_block = (
        f"Conversation history:\n{history_text}\n\n" if history_text else ""
    )
    context = f"""{history_block}Current question:
{state["question"]}

Plan:
{state["plan"]}

Search results:
{state["search_results"]}

File contents:
{state["file_contents"]}"""

    response = llm.invoke(
        [
            SystemMessage(content=ANSWER_PROMPT),
            HumanMessage(content=context),
        ]
    )
    return {"answer": response.content}


def build_analysis_graph():
    """Build the plan → search → read → answer graph."""
    graph = StateGraph(AnalysisState)

    graph.add_node("plan", plan_step)
    graph.add_node("search", search_step)
    graph.add_node("read", read_step)
    graph.add_node("answer", answer_step)

    graph.add_edge(START, "plan")
    graph.add_edge("plan", "search")
    graph.add_edge("search", "read")
    graph.add_edge("read", "answer")
    graph.add_edge("answer", END)

    return graph.compile()


def run_analysis_graph(
    question: str,
    repo_path: str | Path = DEFAULT_REPO_PATH,
    index_path: str | Path = DEFAULT_INDEX_PATH,
    k: int = 4,
    model: str = "gpt-4o-mini",
    progress_callback: ProgressCallback | None = None,
    openai_api_key: str | None = None,
    history: list[ChatMessage] | None = None,
) -> str:
    """Run the full analysis graph and return the answer."""
    with use_openai_api_key(openai_api_key):
        state: AnalysisState = {
            "question": question,
            "history": history or [],
            "repo_path": str(repo_path),
            "index_path": str(index_path),
            "k": k,
            "model": model,
            "plan": "",
            "search_results": "",
            "file_contents": "",
            "answer": "",
        }

        emit_progress(progress_callback, "plan", "Planning analysis", "running")
        state.update(plan_step(state))
        emit_progress(progress_callback, "plan", "Analysis plan ready", "done")

        emit_progress(progress_callback, "search", "Searching codebase", "running")
        state.update(search_step(state))
        emit_progress(progress_callback, "search", "Relevant code found", "done")

        emit_progress(progress_callback, "read", "Reading source files", "running")
        state.update(read_step(state))
        emit_progress(progress_callback, "read", "Files loaded", "done")

        emit_progress(progress_callback, "answer", "Generating answer", "running")
        state.update(answer_step(state))
        emit_progress(progress_callback, "answer", "Answer ready", "done")

        return state["answer"]
