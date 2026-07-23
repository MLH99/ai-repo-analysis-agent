"""Klona ett Git-repo till repo/."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.venv_bootstrap import reexec_with_project_venv

reexec_with_project_venv()

from src.git_clone import GitCloneError, clone_git_repository


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Klona ett Git-repo till repo/ utan att indexera."
    )
    parser.add_argument("git_url", help="Git-URL att klona")
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path("repo"),
        help="Målmapp för klonen (standard: repo)",
    )
    parser.add_argument(
        "--branch",
        help="Branch att klona (valfritt)",
    )
    args = parser.parse_args()

    try:
        target = clone_git_repository(
            git_url=args.git_url,
            target_dir=args.repo,
            branch=args.branch,
        )
    except (GitCloneError, ValueError) as error:
        print(f"Fel: {error}", file=sys.stderr)
        raise SystemExit(1) from error

    print(f"Klart. Repository finns i: {target}")


if __name__ == "__main__":
    main()
