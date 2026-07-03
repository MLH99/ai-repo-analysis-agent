"""Laddar källkodsfiler från en lokal mapp eller klonad repo."""

from pathlib import Path

from langchain_community.document_loaders import TextLoader
from langchain_core.documents import Document

SKIP_DIRS = {
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "node_modules",
    ".mypy_cache",
    ".pytest_cache",
    "data",
}

SUPPORTED_EXTENSIONS = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".jsx": "javascript",
    ".java": "java",
    ".go": "go",
    ".rs": "rust",
    ".md": "markdown",
}


def load_code_documents(repo_path: str | Path) -> list[Document]:
    """Läser in alla kodfiler från en lokal mapp."""
    root = Path(repo_path).resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"Katalogen finns inte: {root}")

    documents: list[Document] = []

    for file_path in root.rglob("*"):
        if not file_path.is_file():
            continue
        if any(part in SKIP_DIRS for part in file_path.parts):
            continue
        if file_path.suffix not in SUPPORTED_EXTENSIONS:
            continue

        loader = TextLoader(str(file_path), encoding="utf-8", autodetect_encoding=True)
        docs = loader.load()
        for doc in docs:
            doc.metadata["source"] = str(file_path.relative_to(root))
            doc.metadata["language"] = SUPPORTED_EXTENSIONS[file_path.suffix]
        documents.extend(docs)

    if not documents:
        raise ValueError(f"Inga kodfiler hittades i {root}")

    return documents
