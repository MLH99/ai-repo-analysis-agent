"""Pydantic models for the API."""

from typing import Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1)


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, examples=["Where is authentication handled?"])
    history: list[ChatMessage] = Field(
        default_factory=list,
        description="Prior conversation turns for follow-up questions.",
    )
    repo_path: str | None = None
    index_path: str | None = None
    k: int = Field(default=4, ge=1, le=20)
    model: str = "gpt-4o-mini"
    mode: Literal["graph", "react"] = "graph"
    openai_api_key: str | None = Field(
        default=None,
        description="Optional OpenAI API key for this request.",
    )


class AskResponse(BaseModel):
    question: str
    answer: str
    mode: str


class IndexRequest(BaseModel):
    repo_path: str | None = None
    index_path: str | None = None
    git_url: str | None = Field(
        default=None,
        examples=["https://github.com/user/repository.git"],
    )
    branch: str | None = Field(
        default=None,
        examples=["main"],
        description="Optional branch to clone when git_url is provided.",
    )
    openai_api_key: str | None = Field(
        default=None,
        description="Optional OpenAI API key for this request.",
    )


class IndexResponse(BaseModel):
    repo_path: str
    index_path: str
    files_indexed: int
    chunks_created: int
    git_url: str | None = None
    branch: str | None = None


class HealthResponse(BaseModel):
    status: str
    index_exists: bool
    repo_exists: bool
