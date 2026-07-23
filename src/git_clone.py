"""Clone Git repositories as input for the codebase."""

from __future__ import annotations

import os
import re
import shutil
import stat
import subprocess
import uuid
from pathlib import Path

from src.repo import DEFAULT_REPO_PATH

ALLOWED_GIT_PREFIXES = (
    "https://",
    "http://",
    "git@",
    "ssh://",
)


class GitCloneError(RuntimeError):
    """Raised when cloning a repository fails."""


def validate_git_url(git_url: str) -> str:
    """Validate that the URL looks like a safe Git remote."""
    url = git_url.strip()

    if not url:
        raise ValueError("git_url must not be empty")

    if url.startswith("file://"):
        raise ValueError("file:// URLs are not supported")

    if not url.startswith(ALLOWED_GIT_PREFIXES):
        raise ValueError(
            "Invalid git_url. Use https://, http://, git@, or ssh://"
        )

    return url


def repo_name_from_url(git_url: str) -> str:
    """Extract repository name from a Git URL."""
    cleaned = git_url.rstrip("/").removesuffix(".git")
    name = cleaned.split("/")[-1]
    if name.endswith(":"):
        name = cleaned.split(":")[-1]
    return re.sub(r"[^\w\-.]", "_", name) or "repository"


def _remove_readonly(func, path, _exc_info) -> None:
    """Allow removing read-only files on Windows."""
    os.chmod(path, stat.S_IWRITE)
    func(path)


def _safe_rmtree(path: Path) -> None:
    """Remove a directory tree, including read-only files on Windows."""
    if path.exists():
        shutil.rmtree(path, onexc=_remove_readonly)


def _move_aside(path: Path) -> Path | None:
    """Rename an existing directory out of the way instead of deleting in place."""
    if not path.exists():
        return None

    backup = path.parent / f".{path.name}_old_{uuid.uuid4().hex[:8]}"
    path.rename(backup)
    return backup


def clone_git_repository(
    git_url: str,
    target_dir: str | Path = DEFAULT_REPO_PATH,
    branch: str | None = None,
    depth: int = 1,
) -> Path:
    """Clone a Git repo to a local folder."""
    validated_url = validate_git_url(git_url)
    target = Path(target_dir).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)

    temp_target = target.parent / f".{target.name}_clone_{uuid.uuid4().hex[:8]}"
    backup: Path | None = None

    command = ["git", "clone", "--depth", str(depth)]
    if branch:
        command.extend(["--branch", branch])
    command.extend([validated_url, str(temp_target)])

    try:
        completed = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as error:
        raise GitCloneError(
            "git is not installed. Install Git and try again."
        ) from error
    except subprocess.CalledProcessError as error:
        _safe_rmtree(temp_target)
        details = (error.stderr or error.stdout or "").strip()
        message = f"Git clone failed: {details or validated_url}"
        raise GitCloneError(message) from error

    try:
        backup = _move_aside(target)
        temp_target.rename(target)
    except OSError as error:
        _safe_rmtree(temp_target)
        if backup and backup.exists() and not target.exists():
            backup.rename(target)
        raise GitCloneError(
            "Could not replace the target repository folder. "
            "Close any programs using the repo directory and try again."
        ) from error

    if backup and backup.exists():
        try:
            _safe_rmtree(backup)
        except OSError:
            print(f"Warning: could not remove old repo backup: {backup}")

    if completed.stdout.strip():
        print(completed.stdout.strip())

    print(f"Cloned {validated_url} to {target}")
    return target
