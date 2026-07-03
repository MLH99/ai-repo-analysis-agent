"""Agenter för kodbasanalys."""

from pathlib import Path

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from src.graph.agent_graph import run_analysis_graph
from src.indexer import DEFAULT_INDEX_PATH
from src.repo import DEFAULT_REPO_PATH
from src.tools.factory import create_agent_tools

load_dotenv()

REACT_SYSTEM_PROMPT = """Du är en AI-assistent som analyserar mjukvaruprojekt.

Du har tillgång till dessa verktyg:
- search_codebase: semantisk sökning i indexerad kod
- read_file: läs en hel fil
- grep_code: exakt regex-sökning
- list_files: lista filer i projektet

Arbetsflöde:
1. Börja med search_codebase eller list_files för överblick
2. Använd read_file för att läsa relevanta filer i full längd
3. Använd grep_code för exakta funktions- eller klassnamn

Regler:
- Skicka användarens fullständiga fråga till search_codebase
- Basera svaret på faktisk kod
- Nämn alltid källfiler
- Svara på svenska om inte användaren skriver på annat språk"""


def create_react_analysis_agent(
    repo_path: str | Path = DEFAULT_REPO_PATH,
    index_path: str | Path = DEFAULT_INDEX_PATH,
    k: int = 4,
    model: str = "gpt-4o-mini",
):
    """Skapar en flexibel ReAct-agent med alla verktyg."""
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
) -> str:
    """Ställer en fråga till agenten och returnerar svaret som text."""
    if mode == "graph":
        return run_analysis_graph(
            question=question,
            repo_path=repo_path,
            index_path=index_path,
            k=k,
            model=model,
        )

    if mode == "react":
        agent = create_react_analysis_agent(
            repo_path=repo_path,
            index_path=index_path,
            k=k,
            model=model,
        )
        result = agent.invoke({"messages": [HumanMessage(content=question)]})
        last_message = result["messages"][-1]

        if isinstance(last_message, AIMessage):
            return last_message.content

        return str(last_message.content)

    raise ValueError(f"Okänt läge: {mode}. Använd 'graph' eller 'react'.")
