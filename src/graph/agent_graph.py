"""LangGraph med tydliga steg: planera → sök → läs → svara."""

from __future__ import annotations

from pathlib import Path
from typing import TypedDict

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph

from src.indexer import DEFAULT_INDEX_PATH
from src.repo import (
    DEFAULT_REPO_PATH,
    extract_sources_from_search_results,
    read_repo_file,
)
from src.tools.search_tool import create_search_codebase_tool

load_dotenv()

PLAN_PROMPT = """Du planerar hur en kodbas ska analyseras.

Gör en kort plan med:
1. Vad användaren vill veta
2. Vilken semantisk sökfråga som ska användas (hela frågan)
3. Vilka filtyper eller områden som troligen är relevanta

Håll planen kort och konkret."""


ANSWER_PROMPT = """Du svarar på frågor om en indexerad kodbas.

Använd planen, sökresultaten och filinnehållet nedan.
Basera svaret på faktisk kod och nämn alltid källfiler.
Svara på svenska om inte användaren skriver på annat språk.
Om informationen inte räcker, säg det tydligt."""


class AnalysisState(TypedDict):
    question: str
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


def plan_step(state: AnalysisState) -> dict:
    """Steg 1: planera hur frågan ska besvaras."""
    llm = _get_llm(state["model"])
    response = llm.invoke(
        [
            SystemMessage(content=PLAN_PROMPT),
            HumanMessage(content=state["question"]),
        ]
    )
    return {"plan": response.content}


def search_step(state: AnalysisState) -> dict:
    """Steg 2: semantisk sökning i FAISS-index."""
    search_tool = create_search_codebase_tool(
        index_path=state["index_path"],
        k=state["k"],
    )
    results = search_tool.invoke({"query": state["question"]})
    return {"search_results": results}


def read_step(state: AnalysisState) -> dict:
    """Steg 3: läs hela filer som hittades i sökningen."""
    sources = extract_sources_from_search_results(state["search_results"])
    chunks: list[str] = []

    for source in sources[:3]:
        try:
            chunks.append(read_repo_file(state["repo_path"], source))
        except (FileNotFoundError, ValueError) as error:
            chunks.append(f"Fil: {source}\n\nKunde inte läsas: {error}")

    if not chunks:
        return {"file_contents": "Inga filer kunde läsas från sökresultaten."}

    return {"file_contents": "\n\n".join(chunks)}


def answer_step(state: AnalysisState) -> dict:
    """Steg 4: syntetisera ett slutgiltigt svar."""
    llm = _get_llm(state["model"])
    context = f"""Fråga:
{state["question"]}

Plan:
{state["plan"]}

Sökresultat:
{state["search_results"]}

Innehåll från filer:
{state["file_contents"]}"""

    response = llm.invoke(
        [
            SystemMessage(content=ANSWER_PROMPT),
            HumanMessage(content=context),
        ]
    )
    return {"answer": response.content}


def build_analysis_graph():
    """Bygger grafen plan → search → read → answer."""
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
) -> str:
    """Kör hela analysgrafen och returnerar svaret."""
    graph = build_analysis_graph()
    result = graph.invoke(
        {
            "question": question,
            "repo_path": str(repo_path),
            "index_path": str(index_path),
            "k": k,
            "model": model,
            "plan": "",
            "search_results": "",
            "file_contents": "",
            "answer": "",
        }
    )
    return result["answer"]
