"""Pydantic-modeller för API:et."""

from typing import Literal

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, examples=["Var hanteras autentisering?"])
    repo_path: str | None = None
    index_path: str | None = None
    k: int = Field(default=4, ge=1, le=20)
    model: str = "gpt-4o-mini"
    mode: Literal["graph", "react"] = "graph"


class AskResponse(BaseModel):
    question: str
    answer: str
    mode: str


class IndexRequest(BaseModel):
    repo_path: str | None = None
    index_path: str | None = None


class IndexResponse(BaseModel):
    repo_path: str
    index_path: str
    files_indexed: int
    chunks_created: int


class HealthResponse(BaseModel):
    status: str
    index_exists: bool
    repo_exists: bool
