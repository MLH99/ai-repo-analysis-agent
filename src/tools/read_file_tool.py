"""Verktyg för att läsa hela filer från kodbasen."""

from pathlib import Path

from langchain_core.tools import StructuredTool

from src.repo import read_repo_file


def create_read_file_tool(repo_path: str | Path) -> StructuredTool:
    """Skapar ett verktyg för att läsa en hel fil."""

    def read_file(file_path: str) -> str:
        return read_repo_file(repo_path=repo_path, file_path=file_path)

    return StructuredTool.from_function(
        func=read_file,
        name="read_file",
        description=(
            "Läs en hel fil från kodbasen. "
            "Använd efter search_codebase när du behöver full kontext, "
            "t.ex. file_path='app/auth.py'."
        ),
    )
