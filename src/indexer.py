"""Bygger och sparar FAISS-index från en kodbas."""

from pathlib import Path
from typing import TypedDict

from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

from src.loader import load_code_documents
from src.splitter import split_code_documents

load_dotenv()

DEFAULT_INDEX_PATH = Path("data/faiss_index")


class IndexResult(TypedDict):
    repo_path: str
    index_path: str
    files_indexed: int
    chunks_created: int


def build_faiss_index(
    repo_path: str | Path,
    index_path: str | Path = DEFAULT_INDEX_PATH,
    chunk_size: int = 800,
    chunk_overlap: int = 100,
) -> IndexResult:
    """Indexerar en kodbas och sparar FAISS-index lokalt."""
    repo_path = Path(repo_path).resolve()
    index_path = Path(index_path)

    print(f"Läser in kod från: {repo_path}")
    documents = load_code_documents(repo_path)
    print(f"Hittade {len(documents)} filer")

    print("Delar upp kod i chunkar...")
    chunks = split_code_documents(
        documents,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    print(f"Skapade {len(chunks)} kodblock")

    print("Skapar embeddings och FAISS-index...")
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = FAISS.from_documents(chunks, embeddings)

    index_path.parent.mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(str(index_path))
    print(f"Index sparat i: {index_path}")

    return {
        "repo_path": str(repo_path),
        "index_path": str(index_path.resolve()),
        "files_indexed": len(documents),
        "chunks_created": len(chunks),
    }
