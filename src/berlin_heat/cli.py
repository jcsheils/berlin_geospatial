"""Command-line status and validation interface."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .contracts import validate_repository
from .manifest import ManifestError, RepositoryManifest, load_manifest
from .paths import ProjectRootNotFoundError, resolve_project_path


def _path_available(manifest: RepositoryManifest, dataset_id: str) -> bool:
    spec = manifest.datasets[dataset_id]
    if spec.availability == "planned" or not spec.path:
        return False
    try:
        return resolve_project_path(manifest.root, spec.path).is_file()
    except ValueError:
        return False


def _is_deferred(spec: object) -> bool:
    """Return whether a dataset is registered only as a future extension."""
    return getattr(spec, "metadata", {}).get("scope") == (
        "future-extension-not-current-thesis-core"
    )


def _print_status(manifest: RepositoryManifest) -> int:
    print(manifest.project["title"])
    print(f"Repository: {manifest.root}")
    print()
    print("Workstream readiness")
    for pillar_id in sorted(manifest.pillars):
        pillar = manifest.pillars[pillar_id]
        present = sum(
            _path_available(manifest, dataset_id)
            for dataset_id in pillar.datasets
        )
        planned = sum(
            manifest.datasets[dataset_id].availability == "planned"
            for dataset_id in pillar.datasets
        )
        print(
            f"{pillar_id:>2}  {pillar.status:<16}  {pillar.label} "
            f"[{present}/{len(pillar.datasets)} paths present; {planned} planned]"
        )
        print(f"    {pillar.reason}")

    current = sum(
        spec.availability != "planned"
        and bool(spec.path)
        and _path_available(manifest, dataset_id)
        for dataset_id, spec in manifest.datasets.items()
    )
    planned = sum(
        spec.availability == "planned" and not _is_deferred(spec)
        for spec in manifest.datasets.values()
    )
    deferred = sum(_is_deferred(spec) for spec in manifest.datasets.values())
    missing_required = sum(
        spec.required
        and spec.availability != "planned"
        and not _path_available(manifest, dataset_id)
        for dataset_id, spec in manifest.datasets.items()
    )
    print()
    print(
        f"Dataset inventory: {current} available, {planned} core planned, "
        f"{deferred} deferred extensions, {missing_required} required missing."
    )
    return 0


def _print_validation(
    manifest: RepositoryManifest, strict: bool = False
) -> int:
    issues = validate_repository(manifest)
    for issue in issues:
        print(
            f"{issue.severity:<7} {issue.dataset_id}: "
            f"{issue.code} - {issue.message}"
        )

    errors = sum(issue.severity == "ERROR" for issue in issues)
    warnings = sum(issue.severity == "WARNING" for issue in issues)
    infos = sum(issue.severity == "INFO" for issue in issues)
    print()
    print(
        f"Validation summary: {errors} errors, {warnings} warnings, "
        f"{infos} informational checks."
    )
    if errors or (strict and warnings):
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="berlin-heat",
        description="Inspect the Berlin heat thesis repository without changing it.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        help="Repository root; normally discovered automatically.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser(
        "status", help="Show declared thesis-workstream and dataset readiness."
    )
    validate = commands.add_parser(
        "validate", help="Validate current dataset paths and contracts."
    )
    validate.add_argument(
        "--strict",
        action="store_true",
        help="Return a failure status for warnings as well as errors.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        manifest = load_manifest(args.root)
        if args.command == "status":
            return _print_status(manifest)
        if args.command == "validate":
            return _print_validation(manifest, strict=args.strict)
    except (ManifestError, ProjectRootNotFoundError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    parser.error(f"Unsupported command: {args.command}")
    return 2
