"""Project-root and manifest-path helpers."""

from __future__ import annotations

import os
from pathlib import Path


class ProjectRootNotFoundError(FileNotFoundError):
    """Raised when the repository root cannot be located."""


def find_project_root(start: str | Path | None = None) -> Path:
    """Find a repository root without depending on any large local dataset."""

    configured = os.environ.get("BERLIN_HEAT_ROOT")
    origin = Path(configured) if configured else Path(start or Path.cwd())
    origin = origin.expanduser().resolve()
    if origin.is_file():
        origin = origin.parent

    for candidate in (origin, *origin.parents):
        if (
            (candidate / "pyproject.toml").is_file()
            and (candidate / "config/project.toml").is_file()
            and (candidate / "config/datasets.toml").is_file()
        ):
            return candidate

    raise ProjectRootNotFoundError(
        f"Could not locate the Berlin heat repository from {origin}."
    )


def resolve_project_path(root: Path, relative_path: str) -> Path:
    """Resolve a manifest path and reject absolute paths or traversal."""

    declared = Path(relative_path)
    if declared.is_absolute():
        raise ValueError(f"Manifest paths must be relative: {relative_path}")

    resolved_root = root.resolve()
    resolved = (resolved_root / declared).resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError(
            f"Manifest path escapes the project root: {relative_path}"
        ) from exc
    return resolved
