"""Restore the frozen inventory using only Python's standard library."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import tempfile


def digest(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def restore(root: Path) -> Path:
    folder = root / "data/raw/tree_inventory"
    metadata = json.loads((folder / "snapshot.json").read_text())
    archive = folder / "Berlin_trees.gpkg.gz"
    target = root / "data/Berlin_trees.gpkg"
    if target.exists():
        if digest(target) != metadata["uncompressed_sha256"]:
            raise ValueError("Existing inventory differs from the frozen snapshot; preserve it before restoring.")
        return target
    if digest(archive) != metadata["archive_sha256"]:
        raise ValueError("Archive checksum mismatch; restore aborted.")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=target.parent, suffix=".gpkg.tmp", delete=False) as out:
            temporary = Path(out.name)
            with gzip.open(archive, "rb") as source:
                shutil.copyfileobj(source, out)
        if temporary.stat().st_size != metadata["uncompressed_bytes"] or digest(temporary) != metadata["uncompressed_sha256"]:
            raise ValueError("Restored inventory checksum or size mismatch.")
        temporary.replace(target)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return target


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    print(f"Verified frozen inventory: {restore(args.root.resolve())}")
