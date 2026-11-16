"""Extract the 2025 tree inventory from its GBIF archive, using the standard library only.

The archive is a Darwin Core export of the Berlin tree cadastre as published in
2025. Each tree has one observation row and, where the planting year is known, a
second ".planted" row. The extract keeps one row per tree with the fields the
identifier comparison needs. Only `occurrence.tsv` is read; nothing is unpacked.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
from pathlib import Path
import tempfile
from urllib.request import urlopen
import zipfile

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "data/raw/tree_inventory"
OUTPUT = FOLDER / "trees_2025_gbif.csv.gz"
SNAPSHOT = FOLDER / "snapshot_2025.json"
ARCHIVE_URL = "https://hosted-datasets.gbif.org/datasets/berlin-trees.zip"
ARCHIVE_SHA256 = "42042faaec9b091edc9ec5e4269c4f8f82d0447d2392bbe7892263dcd187c9f6"
MEMBER = "berlin-trees/occurrence.tsv"
COLUMNS = ["tree_id", "district", "genus", "planting_year", "x_25833", "y_25833"]


def sha256(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def tree_rows(lines) -> list[list[str]]:
    """One row per tree from the archive's tab-separated occurrence table."""
    rows = []
    for record in csv.DictReader(lines, delimiter="\t", quoting=csv.QUOTE_NONE):
        if record["occurrenceID"].endswith(".planted"):
            continue
        # The archive writes missing values as Python's None, which is not valid JSON.
        properties = json.loads(record["dynamicProperties"].replace(":None", ":null") or "{}")
        year = properties.get("planting year")
        rows.append([
            record["occurrenceID"], record["municipality"], record["genus"], "" if year is None else str(int(year)),
            f"{float(record['verbatimLongitude']):.2f}", f"{float(record['verbatimLatitude']):.2f}",
        ])
    return sorted(rows)


def extract(archive: Path) -> dict:
    digest = sha256(archive)
    if digest != ARCHIVE_SHA256:
        raise ValueError(f"{archive} is not the recorded archive (SHA-256 {digest})")
    with zipfile.ZipFile(archive) as bundle, bundle.open(MEMBER) as member:
        rows = tree_rows(io.TextIOWrapper(member, encoding="utf-8", newline=""))
    text = io.StringIO()
    writer = csv.writer(text, lineterminator="\n")
    writer.writerow(COLUMNS)
    writer.writerows(rows)
    payload = text.getvalue().encode("utf-8")
    with OUTPUT.open("wb") as raw, gzip.GzipFile(filename="", mode="wb", fileobj=raw, compresslevel=6, mtime=0) as handle:
        handle.write(payload)
    return {
        "extracted_date": "2026-11-16",
        "file": str(OUTPUT.relative_to(ROOT)),
        "file_bytes": OUTPUT.stat().st_size,
        "file_sha256": sha256(OUTPUT),
        "rows": len(rows),
        "street_trees": sum(row[0].startswith("strassenbaeume.") for row in rows),
        "green_space_trees": sum(row[0].startswith("anlagenbaeume.") for row in rows),
        "columns": COLUMNS,
        "source": "https://doi.org/10.15468/75ssj5",
        "source_archive": ARCHIVE_URL,
        "source_archive_sha256": ARCHIVE_SHA256,
        "source_archive_bytes": archive.stat().st_size,
        "source_published": "2025-12-19",
        "source_license": "CC0 1.0 (originally Datenlizenz Deutschland - Zero - Version 2.0)",
        "coordinate_crs": "EPSG:25833",
        "provenance_limit": ("Third-party export of the official cadastre, not an official release. It holds about 39,500 fewer "
                             "trees than the platform's 2025 import. Coordinates are rounded to 0.01 m."),
        "compression": "gzip level 6, no embedded filename, mtime 0",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--archive", type=Path, help="local copy of berlin-trees.zip; downloaded when omitted")
    args = parser.parse_args()
    if args.archive:
        snapshot = extract(args.archive)
    else:
        with tempfile.TemporaryDirectory() as folder:
            archive = Path(folder) / "berlin-trees.zip"
            with urlopen(ARCHIVE_URL, timeout=300) as response, archive.open("wb") as handle:
                while chunk := response.read(1 << 20):
                    handle.write(chunk)
            snapshot = extract(archive)
    SNAPSHOT.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {snapshot['file']}: {snapshot['rows']:,} trees")


if __name__ == "__main__":
    main()
