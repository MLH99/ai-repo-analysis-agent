"""Samlar alla agentverktyg."""

from pathlib import Path

from langchain_core.tools import StructuredTool

from src.indexer import DEFAULT_INDEX_PATH
from src.repo import DEFAULT_REPO_PATH
from src.tools.grep_tool import create_grep_code_tool
from src.tools.list_files_tool import create_list_files_tool
from src.tools.read_file_tool import create_read_file_tool
from src.tools.search_tool import create_search_codebase_tool


def create_agent_tools(
    repo_path: str | Path = DEFAULT_REPO_PATH,
    index_path: str | Path = DEFAULT_INDEX_PATH,
    k: int = 4,
) -> list[StructuredTool]:
    """Skapar alla verktyg som agenten kan använda."""
    return [
        create_search_codebase_tool(index_path=index_path, k=k),
        create_read_file_tool(repo_path=repo_path),
        create_grep_code_tool(repo_path=repo_path),
        create_list_files_tool(repo_path=repo_path),
    ]
