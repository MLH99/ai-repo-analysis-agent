"""FastAPI application for the codebase analysis agent."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from queue import Queue
from threading import Thread

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from src.agent import ask_question
from src.api.schemas import (
    AskRequest,
    AskResponse,
    HealthResponse,
    IndexRequest,
    IndexResponse,
)
from src.git_clone import GitCloneError
from src.indexer import DEFAULT_INDEX_PATH, build_faiss_index
from src.repo import DEFAULT_REPO_PATH, resolve_repo_path

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
STATIC_DIR = ROOT_DIR / "static"

app = FastAPI(
    title="AI Repository Analysis Agent",
    description="API for indexing and querying a codebase.",
    version="0.2.0",
)

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


def _resolve_index_path(index_path: str | None) -> Path:
    return Path(index_path) if index_path else DEFAULT_INDEX_PATH


def _progress_event(step: str, message: str, status: str) -> str:
    return f"data: {json.dumps({'step': step, 'message': message, 'status': status})}\n\n"


def _run_streaming_task(queue: Queue, task) -> None:
    try:
        result = task()
        queue.put({"type": "complete", "result": result})
    except Exception as error:  # noqa: BLE001 - surface task errors to client stream
        queue.put({"type": "error", "message": str(error)})
    finally:
        queue.put(None)


async def _stream_from_queue(queue: Queue):
    while True:
        item = await asyncio.to_thread(queue.get)
        if item is None:
            break
        if item.get("type") == "complete":
            yield f"data: {json.dumps(item)}\n\n"
        elif item.get("type") == "error":
            yield f"data: {json.dumps(item)}\n\n"
        else:
            yield _progress_event(item["step"], item["message"], item["status"])


@app.get("/")
def ui_home() -> FileResponse:
    """Serve the web UI."""
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="UI not found")
    return FileResponse(index_file)


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Check that the API is running and whether index/repo exist."""
    return HealthResponse(
        status="ok",
        index_exists=DEFAULT_INDEX_PATH.exists(),
        repo_exists=DEFAULT_REPO_PATH.exists(),
    )


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest) -> AskResponse:
    """Ask the agent a question about the codebase."""
    repo_path = Path(request.repo_path) if request.repo_path else DEFAULT_REPO_PATH
    index_path = _resolve_index_path(request.index_path)

    if not index_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"FAISS index not found: {index_path}. Run POST /index first.",
        )

    try:
        resolve_repo_path(repo_path)
        answer = ask_question(
            question=request.question,
            repo_path=repo_path,
            index_path=index_path,
            k=request.k,
            model=request.model,
            mode=request.mode,
            openai_api_key=request.openai_api_key,
            history=[message.model_dump() for message in request.history],
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


@app.post("/ask/stream")
async def ask_stream(request: AskRequest) -> StreamingResponse:
    """Stream agent progress while answering a question."""
    repo_path = Path(request.repo_path) if request.repo_path else DEFAULT_REPO_PATH
    index_path = _resolve_index_path(request.index_path)

    if not index_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"FAISS index not found: {index_path}. Index the repository first.",
        )

    queue: Queue = Queue()

    def task() -> dict:
        resolve_repo_path(repo_path)

        def progress(step: str, message: str, status: str) -> None:
            queue.put({"step": step, "message": message, "status": status})

        answer = ask_question(
            question=request.question,
            repo_path=repo_path,
            index_path=index_path,
            k=request.k,
            model=request.model,
            mode=request.mode,
            progress_callback=progress,
            openai_api_key=request.openai_api_key,
            history=[message.model_dump() for message in request.history],
        )
        return {"question": request.question, "answer": answer, "mode": request.mode}

    Thread(target=_run_streaming_task, args=(queue, task), daemon=True).start()
    return StreamingResponse(_stream_from_queue(queue), media_type="text/event-stream")


@app.post("/index", response_model=IndexResponse)
def index_repository(request: IndexRequest) -> IndexResponse:
    """Index a codebase and save a new FAISS index."""
    repo_path = Path(request.repo_path) if request.repo_path else DEFAULT_REPO_PATH
    index_path = _resolve_index_path(request.index_path)

    try:
        if not request.git_url:
            resolve_repo_path(repo_path)

        result = build_faiss_index(
            repo_path=repo_path,
            index_path=index_path,
            git_url=request.git_url,
            branch=request.branch,
            openai_api_key=request.openai_api_key,
        )
    except GitCloneError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return IndexResponse(**result)


@app.post("/index/stream")
async def index_stream(request: IndexRequest) -> StreamingResponse:
    """Stream indexing progress via Server-Sent Events."""
    repo_path = Path(request.repo_path) if request.repo_path else DEFAULT_REPO_PATH
    index_path = _resolve_index_path(request.index_path)
    queue: Queue = Queue()

    def task() -> dict:
        if not request.git_url:
            resolve_repo_path(repo_path)

        def progress(step: str, message: str, status: str) -> None:
            queue.put({"step": step, "message": message, "status": status})

        return build_faiss_index(
            repo_path=repo_path,
            index_path=index_path,
            git_url=request.git_url,
            branch=request.branch,
            progress_callback=progress,
            openai_api_key=request.openai_api_key,
        )

    Thread(target=_run_streaming_task, args=(queue, task), daemon=True).start()
    return StreamingResponse(_stream_from_queue(queue), media_type="text/event-stream")
