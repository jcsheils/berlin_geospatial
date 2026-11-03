#!/usr/bin/env python3
"""Build canonical positive recorded-watering tree-day temporal products."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from berlin_heat.recorded_tree_day import build_recorded_tree_day  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--processed-dir", type=Path)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args(argv)

    artifacts = build_recorded_tree_day(
        args.root,
        processed_dir=args.processed_dir,
        output_dir=args.output_dir,
    )
    print(f"Tree-day product: {artifacts.tree_day_path}")
    print(f"Age timing summary: {artifacts.age_summary_path}")
    print(f"Genus timing summary: {artifacts.genus_summary_path}")
    print(f"Metadata: {artifacts.metadata_path}")
    print(f"Figure: {artifacts.figure_path}")
    print(f"Human-facing age table: {artifacts.age_table_path}")
    print(f"Human-facing genus table: {artifacts.genus_table_path}")
    print(
        f"Tree-days: {artifacts.tree_day_rows:,}; matched events: "
        f"{artifacts.matched_events:,}; matched litres: "
        f"{artifacts.matched_litres:,.0f}; unique trees: "
        f"{artifacts.unique_trees:,}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
