"""Bygger och sparar FAISS-index från en kodbas."""

from pathlib import Path
from typing import TypedDict

from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

from src.loader import load_code_documents
from src.openai_context import ProgressCallback, emit_progress, use_openai_api_key
from src.splitter import split_code_documents

load_dotenv()

DEFAULT_INDEX_PATH = Path("data/faiss_index")


class IndexResult(TypedDict):
    repo_path: str
    index_path: str
    files_indexed: int
    chunks_created: int
    git_url: str | None
    branch: str | None


def build_faiss_index(
    repo_path: str | Path,
    index_path: str | Path = DEFAULT_INDEX_PATH,
    chunk_size: int = 800,
    chunk_overlap: int = 100,
    git_url: str | None = None,
    branch: str | None = None,
    progress_callback: ProgressCallback | None = None,
    openai_api_key: str | None = None,
) -> IndexResult:
    """Indexerar en kodbas och sparar FAISS-index lokalt."""
    from src.git_clone import clone_git_repository

    repo_path = Path(repo_path)
    index_path = Path(index_path)
    cloned_from: str | None = None

    with use_openai_api_key(openai_api_key):
        if git_url:
            emit_progress(
                progress_callback,
                "clone",
                f"Cloning repository: {git_url}",
                "running",
            )
            repo_path = clone_git_repository(
                git_url=git_url,
                target_dir=repo_path,
                branch=branch,
            )
            cloned_from = git_url
            emit_progress(
                progress_callback,
                "clone",
                "Repository cloned successfully",
                "done",
            )

        repo_path = repo_path.resolve()

        emit_progress(
            progress_callback,
            "load",
            f"Loading source files from {repo_path.name}",
            "running",
        )
        documents = load_code_documents(repo_path)
        emit_progress(
            progress_callback,
            "load",
            f"Loaded {len(documents)} files",
            "done",
        )

        emit_progress(
            progress_callback,
            "chunk",
            "Splitting code into chunks",
            "running",
        )
        chunks = split_code_documents(
            documents,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        emit_progress(
            progress_callback,
            "chunk",
            f"Created {len(chunks)} code chunks",
            "done",
        )

        emit_progress(
            progress_callback,
            "embed",
            "Creating embeddings with OpenAI",
            "running",
        )
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        vectorstore = FAISS.from_documents(chunks, embeddings)
        emit_progress(
            progress_callback,
            "embed",
            "Embeddings created",
            "done",
        )

        emit_progress(
            progress_callback,
            "faiss",
            "Building FAISS vector index",
            "running",
        )
        index_path.parent.mkdir(parents=True, exist_ok=True)
        vectorstore.save_local(str(index_path))
        emit_progress(
            progress_callback,
            "faiss",
            "FAISS index built",
            "done",
        )

        emit_progress(
            progress_callback,
            "save",
            f"Index saved to {index_path}",
            "done",
        )

    return {
        "repo_path": str(repo_path),
        "index_path": str(index_path.resolve()),
        "files_indexed": len(documents),
        "chunks_created": len(chunks),
        "git_url": cloned_from,
        "branch": branch,
    }
