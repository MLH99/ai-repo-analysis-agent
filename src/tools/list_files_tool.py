"""Verktyg för att lista filer i kodbasen."""

from pathlib import Path

from langchain_core.tools import StructuredTool

from src.repo import list_repo_files


def create_list_files_tool(repo_path: str | Path) -> StructuredTool:
    """Skapar ett verktyg för att lista projektets filer."""

    def list_files(directory: str = ".") -> str:
        return list_repo_files(repo_path=repo_path, directory=directory)

    return StructuredTool.from_function(
        func=list_files,
        name="list_files",
        description=(
            "List files in the codebase. "
            "Use to get an overview before searching or reading files."
        ),
    )
