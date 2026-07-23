"""Verktyg för exakt textsökning i kodbasen."""

from pathlib import Path

from langchain_core.tools import StructuredTool

from src.repo import grep_repo_code


def create_grep_code_tool(repo_path: str | Path) -> StructuredTool:
    """Skapar ett verktyg för regex-sökning i kod."""

    def grep_code(pattern: str, file_extension: str = ".py") -> str:
        return grep_repo_code(
            repo_path=repo_path,
            pattern=pattern,
            file_extension=file_extension,
        )

    return StructuredTool.from_function(
        func=grep_code,
        name="grep_code",
        description=(
            "Search for exact text or regex in the codebase. "
            "Good for function names, classes, or strings, "
            "e.g. pattern='authenticate_user'."
        ),
    )
