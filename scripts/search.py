"""Söker i FAISS-index med en naturlig språkfråga."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.venv_bootstrap import ensure_langchain_dependencies, reexec_with_project_venv

reexec_with_project_venv()
ensure_langchain_dependencies("search.py")

from src.search import print_search_results, search_code


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sök relevant kod i ett sparat FAISS-index."
    )
    parser.add_argument(
        "query",
        nargs="?",
        default="Var hanteras autentisering?",
        help="Fråga att söka med (standard: 'Var hanteras autentisering?')",
    )
    parser.add_argument(
        "--index",
        type=Path,
        default=Path("data/faiss_index"),
        help="Sökväg till FAISS-index (standard: data/faiss_index)",
    )
    parser.add_argument(
        "-k",
        type=int,
        default=3,
        help="Antal resultat att returnera (standard: 3)",
    )
    args = parser.parse_args()

    results = search_code(query=args.query, index_path=args.index, k=args.k)
    print_search_results(args.query, results)


if __name__ == "__main__":
    main()
