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
            "Sök exakt text eller regex i kodbasen. "
            "Bra för funktionsnamn, klasser eller strängar, "
            "t.ex. pattern='authenticate_user'."
        ),
    )
