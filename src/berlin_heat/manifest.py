"""Parse the project and dataset TOML manifests."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import tomllib

from .paths import find_project_root


VALID_STATUSES = {
    "partial-ready",
    "preliminary-only",
    "blocked-planned",
    "ready",
}
VALID_AVAILABILITY = {
    "current",
    "current-worktree",
    "optional-local",
    "planned",
}


class ManifestError(ValueError):
    """Raised when a repository manifest is malformed."""


@dataclass(frozen=True)
class DatasetSpec:
    dataset_id: str
    label: str
    path: str | None
    format: str
    availability: str
    required: bool
    grain: str
    delimiter: str = ","
    expected_rows: int | None = None
    expected_layer: str | None = None
    required_layers: tuple[str, ...] = ()
    expected_srs_id: int | None = None
    analysis_srs_id: int | None = None
    required_columns: tuple[str, ...] = ()
    known_warning: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(
        cls, dataset_id: str, values: dict[str, Any]
    ) -> "DatasetSpec":
        required_fields = ("label", "format", "availability", "required", "grain")
        missing = [key for key in required_fields if key not in values]
        if missing:
            raise ManifestError(
                f"Dataset {dataset_id} is missing: {', '.join(missing)}"
            )

        availability = str(values["availability"])
        if availability not in VALID_AVAILABILITY:
            raise ManifestError(
                f"Dataset {dataset_id} has invalid availability {availability!r}."
            )

        path = values.get("path")
        if availability != "planned" and not path:
            raise ManifestError(
                f"Dataset {dataset_id} must declare a path unless it is planned."
            )

        known_keys = {
            "label",
            "path",
            "format",
            "availability",
            "required",
            "grain",
            "delimiter",
            "expected_rows",
            "expected_layer",
            "required_layers",
            "expected_srs_id",
            "analysis_srs_id",
            "required_columns",
            "known_warning",
        }
        metadata = {
            key: value for key, value in values.items() if key not in known_keys
        }
        return cls(
            dataset_id=dataset_id,
            label=str(values["label"]),
            path=str(path) if path else None,
            format=str(values["format"]),
            availability=availability,
            required=bool(values["required"]),
            grain=str(values["grain"]),
            delimiter=str(values.get("delimiter", ",")),
            expected_rows=values.get("expected_rows"),
            expected_layer=values.get("expected_layer"),
            required_layers=tuple(values.get("required_layers", ())),
            expected_srs_id=values.get("expected_srs_id"),
            analysis_srs_id=values.get("analysis_srs_id"),
            required_columns=tuple(values.get("required_columns", ())),
            known_warning=values.get("known_warning"),
            metadata=metadata,
        )


@dataclass(frozen=True)
class PillarSpec:
    pillar_id: str
    label: str
    status: str
    reason: str
    datasets: tuple[str, ...]

    @classmethod
    def from_mapping(
        cls, pillar_id: str, values: dict[str, Any]
    ) -> "PillarSpec":
        required_fields = ("label", "status", "reason", "datasets")
        missing = [key for key in required_fields if key not in values]
        if missing:
            raise ManifestError(
                f"Pillar {pillar_id} is missing: {', '.join(missing)}"
            )
        status = str(values["status"])
        if status not in VALID_STATUSES:
            raise ManifestError(
                f"Pillar {pillar_id} has invalid status {status!r}."
            )
        return cls(
            pillar_id=pillar_id,
            label=str(values["label"]),
            status=status,
            reason=str(values["reason"]),
            datasets=tuple(str(item) for item in values["datasets"]),
        )


@dataclass(frozen=True)
class RepositoryManifest:
    root: Path
    project: dict[str, Any]
    pillars: dict[str, PillarSpec]
    datasets: dict[str, DatasetSpec]
    dataset_manifest: dict[str, Any]


def _read_toml(path: Path) -> dict[str, Any]:
    try:
        with path.open("rb") as handle:
            return tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise ManifestError(f"Could not read {path}: {exc}") from exc


def load_manifest(root: str | Path | None = None) -> RepositoryManifest:
    """Load and cross-check both repository manifests."""

    project_root = find_project_root(root)
    project_doc = _read_toml(project_root / "config/project.toml")
    dataset_doc = _read_toml(project_root / "config/datasets.toml")

    project_values = project_doc.get("project")
    pillar_values = project_doc.get("pillars")
    dataset_values = dataset_doc.get("datasets")
    dataset_manifest = dataset_doc.get("manifest")
    if not isinstance(project_values, dict):
        raise ManifestError("config/project.toml is missing [project].")
    if not isinstance(pillar_values, dict):
        raise ManifestError("config/project.toml is missing [pillars].")
    if not isinstance(dataset_values, dict):
        raise ManifestError("config/datasets.toml is missing [datasets].")
    if not isinstance(dataset_manifest, dict):
        raise ManifestError("config/datasets.toml is missing [manifest].")

    datasets = {
        dataset_id: DatasetSpec.from_mapping(dataset_id, values)
        for dataset_id, values in dataset_values.items()
    }
    pillars = {
        pillar_id: PillarSpec.from_mapping(pillar_id, values)
        for pillar_id, values in pillar_values.items()
    }

    unknown_dependencies = {
        dataset_id
        for pillar in pillars.values()
        for dataset_id in pillar.datasets
        if dataset_id not in datasets
    }
    if unknown_dependencies:
        raise ManifestError(
            "Pillars refer to unknown datasets: "
            + ", ".join(sorted(unknown_dependencies))
        )

    return RepositoryManifest(
        root=project_root,
        project=project_values,
        pillars=pillars,
        datasets=datasets,
        dataset_manifest=dataset_manifest,
    )
