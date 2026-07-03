"""Ställ frågor till kodbas-agenten."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.venv_bootstrap import ensure_langchain_dependencies, reexec_with_project_venv

reexec_with_project_venv()
ensure_langchain_dependencies("ask.py")

from src.agent import ask_question


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ställ en fråga om kodbasen till AI-agenten."
    )
    parser.add_argument(
        "question",
        nargs="?",
        default="Var hanteras autentisering?",
        help="Fråga om kodbasen (standard: 'Var hanteras autentisering?')",
    )
    parser.add_argument(
        "--index",
        type=Path,
        default=Path("data/faiss_index"),
        help="Sökväg till FAISS-index (standard: data/faiss_index)",
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path("repo"),
        help="Sökväg till kodbasen (standard: repo)",
    )
    parser.add_argument(
        "-k",
        type=int,
        default=4,
        help="Antal kodblock att hämta per sökning (standard: 4)",
    )
    parser.add_argument(
        "--model",
        default="gpt-4o-mini",
        help="OpenAI-modell för agenten (standard: gpt-4o-mini)",
    )
    parser.add_argument(
        "--mode",
        choices=["graph", "react"],
        default="graph",
        help="Agentläge: graph (plan→sök→läs→svara) eller react (fria verktyg)",
    )
    args = parser.parse_args()

    print(f"Fråga: {args.question}\n")
    print("=" * 60)

    answer = ask_question(
        question=args.question,
        repo_path=args.repo,
        index_path=args.index,
        k=args.k,
        model=args.model,
        mode=args.mode,
    )

    print(answer)
    print()


if __name__ == "__main__":
    main()
