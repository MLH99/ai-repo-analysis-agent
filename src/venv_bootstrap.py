"""Hjälper CLI-skript att köra med projektets virtuella miljö."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def venv_python_path(root: Path | None = None) -> Path:
    root = root or project_root()
    if sys.platform == "win32":
        return root / ".venv" / "Scripts" / "python.exe"
    return root / ".venv" / "bin" / "python"


def reexec_with_project_venv() -> None:
    """Starta om skriptet med .venv-Python om det finns och inte redan används."""
    root = project_root()
    venv_python = venv_python_path(root)

    if not venv_python.exists():
        return

    if Path(sys.executable).resolve() == venv_python.resolve():
        return

    completed = subprocess.run([str(venv_python), *sys.argv], check=False)
    raise SystemExit(completed.returncode)


def ensure_langchain_dependencies(script_name: str) -> None:
    """Ge ett tydligt fel om beroenden saknas i aktiv Python."""
    try:
        import langchain_community  # noqa: F401
    except ModuleNotFoundError:
        root = project_root()
        venv_python = venv_python_path(root)

        if venv_python.exists():
            message = (
                "Beroenden finns i .venv men du kör fel Python.\n\n"
                f"Kör i stället:\n"
                f"  {venv_python} scripts/{script_name}\n\n"
                "Eller aktivera miljön först:\n"
                f"  cd {root}\n"
                "  .venv\\Scripts\\activate\n"
                f"  python scripts/{script_name}"
            )
        else:
            message = (
                "Saknade Python-paket. Skapa och använd projektets virtuella miljö:\n\n"
                f"  cd {root}\n"
                "  python -m venv .venv\n"
                "  .venv\\Scripts\\activate\n"
                "  pip install -r requirements.txt\n"
                f"  python scripts/{script_name}"
            )

        print(message, file=sys.stderr)
        raise SystemExit(1)
