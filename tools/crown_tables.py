"""Keep the RQ3 crown-health tables beyond the 90-day artifact limit, using only the standard library.

The ten extracted tables (about 122 MB) are too large for git. They are kept as assets of one
GitHub release, and each must match the SHA-256 that output/rq3_crown_health/outcome.json records.

    python tools/crown_tables.py fetch               download the tables into data/processed/rq3_crown_health/
    python tools/crown_tables.py verify DIR [--sums] check DIR's tables; --sums also writes DIR/SHA256SUMS
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
TAG = "rq3-crown-health-tables-2026-11"
RELEASE_URL = f"https://github.com/jcsheils/berlin_geospatial/releases/download/{TAG}"
OUTCOME = Path("output/rq3_crown_health/outcome.json")
TABLES = Path("data/processed/rq3_crown_health")
SUMS = "SHA256SUMS"


def digest(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def recorded(root: Path = ROOT) -> dict[str, str]:
    """The table names and SHA-256 values the outcome stage read."""
    return json.loads((root / OUTCOME).read_text())["inputs_sha256"]


def verify(folder: Path, root: Path = ROOT) -> dict[str, str]:
    expected = recorded(root)
    problems = []
    for name, sha in sorted(expected.items()):
        path = folder / name
        if not path.is_file():
            problems.append(f"missing {name}")
        elif digest(path) != sha:
            problems.append(f"changed {name}")
    if problems:
        raise ValueError("Tables do not match outcome.json: " + "; ".join(problems))
    return expected


def write_sums(folder: Path) -> Path:
    """Write SHA256SUMS for every file in the folder, in the format `sha256sum -c` reads."""
    names = sorted(p.name for p in folder.iterdir() if p.is_file() and p.name != SUMS)
    target = folder / SUMS
    target.write_text("".join(f"{digest(folder / name)}  {name}\n" for name in names))
    return target


def fetch(root: Path = ROOT, base_url: str = RELEASE_URL) -> list[Path]:
    """Download missing tables and check each one; a table already present must match."""
    target = root / TABLES
    target.mkdir(parents=True, exist_ok=True)
    fetched = []
    for name, sha in sorted(recorded(root).items()):
        path = target / name
        if path.exists():
            if digest(path) != sha:
                raise ValueError(f"{path} differs from outcome.json; move it aside before fetching.")
            continue
        with tempfile.NamedTemporaryFile(dir=target, prefix=f".{name}.", suffix=".part", delete=False) as part:
            partial = Path(part.name)
            try:
                with urllib.request.urlopen(f"{base_url}/{name}", timeout=300) as response:
                    shutil.copyfileobj(response, part)
            except BaseException:
                partial.unlink(missing_ok=True)
                raise
        if digest(partial) != sha:
            partial.unlink()
            raise ValueError(f"Checksum mismatch for downloaded {name}; nothing kept.")
        partial.replace(path)
        fetched.append(path)
    return fetched


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("fetch", help="download and check the ten tables")
    check = commands.add_parser("verify", help="check a folder of tables against outcome.json")
    check.add_argument("folder", type=Path)
    check.add_argument("--sums", action="store_true", help="also write SHA256SUMS for every file in the folder")
    args = parser.parse_args()
    if args.command == "fetch":
        fetched = fetch()
        print(f"Fetched {len(fetched)} tables; all {len(recorded())} match outcome.json.")
    else:
        expected = verify(args.folder)
        print(f"All {len(expected)} tables match outcome.json.")
        if args.sums:
            print(f"Wrote {write_sums(args.folder)}")


if __name__ == "__main__":
    main()
