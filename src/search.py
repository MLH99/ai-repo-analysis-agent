"""Söker i ett sparat FAISS-index."""

from pathlib import Path

from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

from src.indexer import DEFAULT_INDEX_PATH

load_dotenv()

DEFAULT_SCORE_THRESHOLD = 1.3


def load_faiss_index(index_path: str | Path = DEFAULT_INDEX_PATH) -> FAISS:
    """Laddar ett sparat FAISS-index."""
    index_path = Path(index_path)
    if not index_path.exists():
        raise FileNotFoundError(
            f"FAISS-index saknas: {index_path}. Kör build_index.py först."
        )

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    return FAISS.load_local(
        str(index_path),
        embeddings,
        allow_dangerous_deserialization=True,
    )


def search_code_with_scores(
    query: str,
    index_path: str | Path = DEFAULT_INDEX_PATH,
    k: int = 4,
    score_threshold: float | None = DEFAULT_SCORE_THRESHOLD,
) -> list[tuple[Document, float]]:
    """Söker kodblock och returnerar relevanspoäng (lägre = bättre träff)."""
    vectorstore = load_faiss_index(index_path)
    results = vectorstore.similarity_search_with_score(query, k=k)

    if score_threshold is not None:
        results = [
            (document, score)
            for document, score in results
            if score <= score_threshold
        ]

    return results


def search_code(
    query: str,
    index_path: str | Path = DEFAULT_INDEX_PATH,
    k: int = 4,
    score_threshold: float | None = DEFAULT_SCORE_THRESHOLD,
) -> list[Document]:
    """Söker relevanta kodblock baserat på en naturlig språkfråga."""
    return [
        document
        for document, _ in search_code_with_scores(
            query=query,
            index_path=index_path,
            k=k,
            score_threshold=score_threshold,
        )
    ]


def format_search_results(
    query: str,
    results: list[Document] | list[tuple[Document, float]],
    include_scores: bool = False,
) -> str:
    """Formaterar sökresultat som läsbar text för agent eller CLI."""
    if not results:
        return f"Inga relevanta kodblock hittades för frågan: {query}"

    lines = [f"Sökfråga: {query}", ""]

    for index, item in enumerate(results, start=1):
        if include_scores and isinstance(item, tuple):
            document, score = item
            source = document.metadata.get("source", "okänd fil")
            lines.append(f"--- Resultat {index} | {source} | score: {score:.4f} ---")
            lines.append(document.page_content.strip())
            lines.append("")
        elif isinstance(item, tuple):
            document, _ = item
            source = document.metadata.get("source", "okänd fil")
            lines.append(f"--- Resultat {index} | {source} ---")
            lines.append(document.page_content.strip())
            lines.append("")
        else:
            source = item.metadata.get("source", "okänd fil")
            lines.append(f"--- Resultat {index} | {source} ---")
            lines.append(item.page_content.strip())
            lines.append("")

    return "\n".join(lines).strip()


def print_search_results(query: str, results: list[Document]) -> None:
    """Skriver ut sökresultat på ett läsbart sätt."""
    print(f"\nFråga: {query}\n")
    print("=" * 60)
    print(format_search_results(query, results))
    print()
