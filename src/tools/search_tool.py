"""LangChain-verktyg för semantisk kodsökning."""

from pathlib import Path

from langchain_core.tools import StructuredTool

from src.indexer import DEFAULT_INDEX_PATH
from src.search import format_search_results, search_code_with_scores


def create_search_codebase_tool(
    index_path: str | Path = DEFAULT_INDEX_PATH,
    k: int = 4,
    score_threshold: float | None = None,
) -> StructuredTool:
    """Skapar ett verktyg som agenten kan använda för att söka i kodbasen."""

    def search_codebase(query: str) -> str:
        results = search_code_with_scores(
            query=query,
            index_path=index_path,
            k=k,
            score_threshold=score_threshold,
        )
        return format_search_results(query, results, include_scores=True)

    return StructuredTool.from_function(
        func=search_codebase,
        name="search_codebase",
        description=(
            "Search the indexed codebase using semantic search. "
            "Use this to find where functionality is implemented, "
            "e.g. authentication, database, or API endpoints."
        ),
    )
