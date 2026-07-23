"""Agents for codebase analysis."""

from pathlib import Path

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from src.conversation import ChatMessage
from src.graph.agent_graph import run_analysis_graph
from src.indexer import DEFAULT_INDEX_PATH
from src.prompts import REACT_SYSTEM_PROMPT
from src.repo import DEFAULT_REPO_PATH
from src.openai_context import ProgressCallback, use_openai_api_key
from src.tools.factory import create_agent_tools

load_dotenv()


def _history_to_messages(history: list[ChatMessage]) -> list:
    messages = []
    for message in history:
        if message["role"] == "user":
            messages.append(HumanMessage(content=message["content"]))
        else:
            messages.append(AIMessage(content=message["content"]))
    return messages


def create_react_analysis_agent(
    repo_path: str | Path = DEFAULT_REPO_PATH,
    index_path: str | Path = DEFAULT_INDEX_PATH,
    k: int = 4,
    model: str = "gpt-4o-mini",
):
    """Create a flexible ReAct agent with all tools."""
    tools = create_agent_tools(
        repo_path=repo_path,
        index_path=index_path,
        k=k,
    )
    llm = ChatOpenAI(model=model, temperature=0)

    return create_react_agent(
        model=llm,
        tools=tools,
        prompt=REACT_SYSTEM_PROMPT,
    )


def ask_question(
    question: str,
    repo_path: str | Path = DEFAULT_REPO_PATH,
    index_path: str | Path = DEFAULT_INDEX_PATH,
    k: int = 4,
    model: str = "gpt-4o-mini",
    mode: str = "graph",
    progress_callback: ProgressCallback | None = None,
    openai_api_key: str | None = None,
    history: list[ChatMessage] | None = None,
) -> str:
    """Ask the agent a question and return the answer as text."""
    prior_messages = history or []

    if mode == "graph":
        return run_analysis_graph(
            question=question,
            repo_path=repo_path,
            index_path=index_path,
            k=k,
            model=model,
            progress_callback=progress_callback,
            openai_api_key=openai_api_key,
            history=prior_messages,
        )

    if mode == "react":
        with use_openai_api_key(openai_api_key):
            agent = create_react_analysis_agent(
                repo_path=repo_path,
                index_path=index_path,
                k=k,
                model=model,
            )
            messages = _history_to_messages(prior_messages)
            messages.append(HumanMessage(content=question))
            result = agent.invoke({"messages": messages})
        last_message = result["messages"][-1]

        if isinstance(last_message, AIMessage):
            return last_message.content

        return str(last_message.content)

    raise ValueError(f"Unknown mode: {mode}. Use 'graph' or 'react'.")
