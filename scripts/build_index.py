"""Bygger FAISS-index från en lokal kodbas eller Git-URL."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.venv_bootstrap import ensure_langchain_dependencies, reexec_with_project_venv

reexec_with_project_venv()
ensure_langchain_dependencies("build_index.py")

from src.indexer import build_faiss_index


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Indexera en kodbas och spara FAISS-vektorindex."
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path("repo"),
        help="Sökväg till lokal kodbas eller klon-mål (standard: repo)",
    )
    parser.add_argument(
        "--git-url",
        type=str,
        help="Klona ett Git-repo till --repo innan indexering",
    )
    parser.add_argument(
        "--branch",
        type=str,
        help="Branch att klona (valfritt, används med --git-url)",
    )
    parser.add_argument(
        "--index",
        type=Path,
        default=Path("data/faiss_index"),
        help="Var FAISS-index ska sparas (standard: data/faiss_index)",
    )
    args = parser.parse_args()

    build_faiss_index(
        repo_path=args.repo,
        index_path=args.index,
        git_url=args.git_url,
        branch=args.branch,
    )


if __name__ == "__main__":
    main()
