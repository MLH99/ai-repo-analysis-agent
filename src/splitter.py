"""Delar upp kod med LangChains språkspecifika text splitters."""

from langchain_core.documents import Document
from langchain_text_splitters import (
    Language,
    RecursiveCharacterTextSplitter,
)

LANGUAGE_MAP: dict[str, Language] = {
    "python": Language.PYTHON,
    "javascript": Language.JS,
    "typescript": Language.TS,
    "java": Language.JAVA,
    "go": Language.GO,
    "rust": Language.RUST,
    "markdown": Language.MARKDOWN,
}


def split_code_documents(
    documents: list[Document],
    chunk_size: int = 800,
    chunk_overlap: int = 100,
) -> list[Document]:
    """Delar upp dokument med språkspecifik splitter där det går."""
    chunks: list[Document] = []

    for doc in documents:
        language_name = doc.metadata.get("language", "python")
        language = LANGUAGE_MAP.get(language_name)

        if language:
            splitter = RecursiveCharacterTextSplitter.from_language(
                language=language,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
        else:
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )

        chunks.extend(splitter.split_documents([doc]))

    return chunks
