"""Gemensamma hjälpfunktioner för att arbeta med en lokal kodbas."""

from __future__ import annotations

import re
from pathlib import Path

from src.loader import SKIP_DIRS, SUPPORTED_EXTENSIONS

DEFAULT_REPO_PATH = Path("repo")


def resolve_repo_path(repo_path: str | Path) -> Path:
    """Returnerar absolut sökväg till kodbasen."""
    path = Path(repo_path).resolve()
    if not path.is_dir():
        raise FileNotFoundError(f"Kodbasen finns inte: {path}")
    return path


def safe_repo_file(repo_root: Path, relative_path: str) -> Path:
    """Säkerställer att en fil ligger inom kodbasen."""
    normalized = relative_path.replace("\\", "/").strip().lstrip("/")
    candidate = (repo_root / normalized).resolve()

    if not str(candidate).startswith(str(repo_root)):
        raise ValueError(f"Åtkomst nekad utanför kodbasen: {relative_path}")

    if not candidate.is_file():
        raise FileNotFoundError(f"Filen hittades inte: {relative_path}")

    return candidate


def should_skip_path(path: Path) -> bool:
    """Avgör om en sökväg ska ignoreras."""
    return any(part in SKIP_DIRS for part in path.parts)


def list_repo_files(
    repo_path: str | Path,
    directory: str = ".",
    max_files: int = 100,
) -> str:
    """Listar filer i kodbasen som en läsbar trädstruktur."""
    root = resolve_repo_path(repo_path)
    target = (root / directory).resolve()

    if not str(target).startswith(str(root)):
        raise ValueError(f"Åtkomst nekad utanför kodbasen: {directory}")

    if not target.is_dir():
        raise FileNotFoundError(f"Katalogen hittades inte: {directory}")

    lines: list[str] = [f"Filer under {target.relative_to(root)}:"]
    count = 0

    for file_path in sorted(target.rglob("*")):
        if not file_path.is_file():
            continue
        if should_skip_path(file_path.relative_to(root)):
            continue
        if file_path.suffix not in SUPPORTED_EXTENSIONS:
            continue

        relative = file_path.relative_to(root)
        lines.append(f"- {relative.as_posix()}")
        count += 1

        if count >= max_files:
            lines.append(f"... (visar max {max_files} filer)")
            break

    if count == 0:
        return f"Inga kodfiler hittades under {directory}"

    return "\n".join(lines)


def read_repo_file(repo_path: str | Path, file_path: str) -> str:
    """Läser en hel fil från kodbasen."""
    root = resolve_repo_path(repo_path)
    target = safe_repo_file(root, file_path)
    content = target.read_text(encoding="utf-8")
    relative = target.relative_to(root).as_posix()
    return f"Fil: {relative}\n\n{content}"


def grep_repo_code(
    repo_path: str | Path,
    pattern: str,
    file_extension: str = ".py",
    max_results: int = 20,
) -> str:
    """Söker efter ett mönster i kodbasen med regex."""
    root = resolve_repo_path(repo_path)

    try:
        regex = re.compile(pattern, re.IGNORECASE)
    except re.error as error:
        return f"Ogiltigt regex-mönster: {error}"

    matches: list[str] = []

    for file_path in sorted(root.rglob(f"*{file_extension}")):
        if not file_path.is_file():
            continue
        if should_skip_path(file_path.relative_to(root)):
            continue

        relative = file_path.relative_to(root).as_posix()
        for line_number, line in enumerate(
            file_path.read_text(encoding="utf-8").splitlines(),
            start=1,
        ):
            if regex.search(line):
                matches.append(f"{relative}:{line_number}: {line.strip()}")
                if len(matches) >= max_results:
                    return _format_grep_results(pattern, matches)

    return _format_grep_results(pattern, matches)


def _format_grep_results(pattern: str, matches: list[str]) -> str:
    if not matches:
        return f"Inga träffar för mönstret: {pattern}"

    header = f"Träffar för '{pattern}' ({len(matches)}):"
    return "\n".join([header, *matches])


def extract_sources_from_search_results(search_results: str) -> list[str]:
    """Plockar ut filnamn från formaterade FAISS-sökresultat."""
    sources: list[str] = []

    for line in search_results.splitlines():
        if not line.startswith("--- Resultat"):
            continue

        parts = [part.strip() for part in line.split("|")]
        if len(parts) >= 2:
            sources.append(parts[1].replace("\\", "/"))

    return list(dict.fromkeys(sources))
