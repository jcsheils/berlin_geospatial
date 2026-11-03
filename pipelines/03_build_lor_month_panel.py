#!/usr/bin/env python3
"""Build the canonical LOR-month recorded-watering foundation panel."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from berlin_heat.lor_month_panel import build_lor_month_panel  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args(argv)

    artifacts = build_lor_month_panel(
        args.root,
        output_dir=args.output_dir,
    )
    print(f"Panel: {artifacts.panel_path}")
    print(f"Recorded-tree crosswalk: {artifacts.crosswalk_path}")
    print(f"Metadata: {artifacts.metadata_path}")
    print(
        f"Rows: {artifacts.rows:,}; matched events: "
        f"{artifacts.matched_events:,}; matched litres: "
        f"{artifacts.matched_litres:,.0f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
