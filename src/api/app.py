"""FastAPI-applikation för kodbas-agenten."""

from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

from src.agent import ask_question
from src.api.schemas import (
    AskRequest,
    AskResponse,
    HealthResponse,
    IndexRequest,
    IndexResponse,
)
from src.indexer import DEFAULT_INDEX_PATH, build_faiss_index
from src.repo import DEFAULT_REPO_PATH, resolve_repo_path

load_dotenv()

app = FastAPI(
    title="AI Repository Analysis Agent",
    description="API för att indexera och ställa frågor om en kodbas.",
    version="0.1.0",
)


def _resolve_repo_path(repo_path: str | None) -> Path:
    path = Path(repo_path) if repo_path else DEFAULT_REPO_PATH
    return resolve_repo_path(path)


def _resolve_index_path(index_path: str | None) -> Path:
    return Path(index_path) if index_path else DEFAULT_INDEX_PATH


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Kontrollerar att API:et körs och att index/kodbas finns."""
    repo_exists = DEFAULT_REPO_PATH.exists()
    index_exists = DEFAULT_INDEX_PATH.exists()

    return HealthResponse(
        status="ok",
        index_exists=index_exists,
        repo_exists=repo_exists,
    )


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest) -> AskResponse:
    """Ställ en fråga om kodbasen till AI-agenten."""
    repo_path = _resolve_repo_path(request.repo_path)
    index_path = _resolve_index_path(request.index_path)

    if not index_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"FAISS-index saknas: {index_path}. Kör POST /index först.",
        )

    try:
        answer = ask_question(
            question=request.question,
            repo_path=repo_path,
            index_path=index_path,
            k=request.k,
            model=request.model,
            mode=request.mode,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error

    return AskResponse(
        question=request.question,
        answer=answer,
        mode=request.mode,
    )


@app.post("/index", response_model=IndexResponse)
def index_repository(request: IndexRequest) -> IndexResponse:
    """Indexera om en kodbas och spara ett nytt FAISS-index."""
    try:
        repo_path = _resolve_repo_path(request.repo_path)
        index_path = _resolve_index_path(request.index_path)
        result = build_faiss_index(repo_path=repo_path, index_path=index_path)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return IndexResponse(**result)
