"""Startar FastAPI-servern."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.venv_bootstrap import ensure_langchain_dependencies, reexec_with_project_venv

reexec_with_project_venv()
ensure_langchain_dependencies("run_api.py")

import uvicorn


def main() -> None:
    parser = argparse.ArgumentParser(description="Starta FastAPI-servern.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args()

    uvicorn.run(
        "src.api.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
