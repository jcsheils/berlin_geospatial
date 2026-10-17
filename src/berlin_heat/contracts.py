"""Standard-library validation for declared repository datasets."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
import sqlite3

from .manifest import DatasetSpec, RepositoryManifest
from .paths import resolve_project_path


@dataclass(frozen=True)
class ValidationIssue:
    severity: str
    dataset_id: str
    code: str
    message: str


def _issue(
    severity: str, spec: DatasetSpec, code: str, message: str
) -> ValidationIssue:
    return ValidationIssue(severity, spec.dataset_id, code, message)


def _validate_csv(path: Path, spec: DatasetSpec) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.reader(handle, delimiter=spec.delimiter)
            header = next(reader, None)
            if header is None:
                return [_issue("ERROR", spec, "empty_csv", "CSV file is empty.")]
            missing = sorted(set(spec.required_columns) - set(header))
            if missing:
                issues.append(
                    _issue(
                        "ERROR",
                        spec,
                        "missing_columns",
                        "Missing CSV columns: " + ", ".join(missing),
                    )
                )
            row_count = sum(1 for _ in reader)
    except (OSError, csv.Error, UnicodeError) as exc:
        return [_issue("ERROR", spec, "csv_read_failed", str(exc))]

    if spec.expected_rows is not None and row_count != spec.expected_rows:
        issues.append(
            _issue(
                "ERROR",
                spec,
                "unexpected_rows",
                f"Expected {spec.expected_rows:,} rows; found {row_count:,}.",
            )
        )
    return issues


def _quoted_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def _validate_gpkg(path: Path, spec: DatasetSpec) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    uri = path.resolve().as_uri() + "?mode=ro"
    try:
        connection = sqlite3.connect(uri, uri=True)
        contents = {
            row[0]: row[1]
            for row in connection.execute(
                "SELECT table_name, srs_id FROM gpkg_contents"
            )
        }
        missing_layers = sorted(set(spec.required_layers) - set(contents))
        if missing_layers:
            issues.append(
                _issue(
                    "ERROR",
                    spec,
                    "missing_layers",
                    "Missing GeoPackage layers: " + ", ".join(missing_layers),
                )
            )

        layer = spec.expected_layer
        if layer and layer in contents:
            table = _quoted_identifier(layer)
            row_count = connection.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]
            if spec.expected_rows is not None and row_count != spec.expected_rows:
                issues.append(
                    _issue(
                        "ERROR",
                        spec,
                        "unexpected_rows",
                        f"Expected {spec.expected_rows:,} rows in {layer}; "
                        f"found {row_count:,}.",
                    )
                )

            actual_srs = contents[layer]
            if (
                spec.expected_srs_id is not None
                and actual_srs != spec.expected_srs_id
            ):
                issues.append(
                    _issue(
                        "ERROR",
                        spec,
                        "unexpected_crs",
                        f"Expected SRS {spec.expected_srs_id}; found {actual_srs}.",
                    )
                )

            columns = {
                row[1]
                for row in connection.execute(f"PRAGMA table_info({table})")
            }
            missing_columns = sorted(set(spec.required_columns) - columns)
            if missing_columns:
                issues.append(
                    _issue(
                        "ERROR",
                        spec,
                        "missing_columns",
                        "Missing GeoPackage columns: "
                        + ", ".join(missing_columns),
                    )
                )
        connection.close()
    except (OSError, sqlite3.DatabaseError) as exc:
        issues.append(_issue("ERROR", spec, "gpkg_read_failed", str(exc)))
    return issues


def validate_dataset(
    manifest: RepositoryManifest, spec: DatasetSpec
) -> list[ValidationIssue]:
    """Validate one current dataset without changing it."""

    if spec.availability == "planned":
        if spec.metadata.get("scope") == (
            "future-extension-not-current-thesis-core"
        ):
            return [
                _issue(
                    "INFO",
                    spec,
                    "deferred",
                    "Dataset is registered as a future extension, not a "
                    "current thesis dependency.",
                )
            ]
        return [
            _issue(
                "INFO",
                spec,
                "planned",
                "Dataset is declared as planned and has no current path.",
            )
        ]

    try:
        path = resolve_project_path(manifest.root, spec.path or "")
    except ValueError as exc:
        return [_issue("ERROR", spec, "unsafe_path", str(exc))]

    if not path.is_file():
        severity = "ERROR" if spec.required else "WARNING"
        return [
            _issue(
                severity,
                spec,
                "missing_file",
                f"Declared file is not available: {spec.path}",
            )
        ]

    if spec.format == "csv":
        issues = _validate_csv(path, spec)
    elif spec.format == "gpkg":
        issues = _validate_gpkg(path, spec)
    else:
        issues = []

    if spec.known_warning:
        issues.append(
            _issue("WARNING", spec, "known_limitation", spec.known_warning)
        )
    if not any(issue.severity == "ERROR" for issue in issues):
        issues.append(
            _issue(
                "INFO",
                spec,
                "validated",
                f"Validated {spec.path}.",
            )
        )
    return issues


def validate_repository(
    manifest: RepositoryManifest,
) -> list[ValidationIssue]:
    """Validate manifest paths and all declared datasets."""

    issues: list[ValidationIssue] = []
    for dataset_id in sorted(manifest.datasets):
        issues.extend(validate_dataset(manifest, manifest.datasets[dataset_id]))
    return issues
