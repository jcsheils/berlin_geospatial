#!/usr/bin/env python3
"""Build complete-year monthly summaries and fixed-scale watering atlas maps."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from berlin_heat.watering_temporal import build_watering_temporal_atlas  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--processed-dir", type=Path)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args(argv)

    artifacts = build_watering_temporal_atlas(
        args.root,
        processed_dir=args.processed_dir,
        output_dir=args.output_dir,
    )
    print(f"Calendar-month LOR table: {artifacts.calendar_lor_path}")
    print(f"Berlin monthly timeline: {artifacts.city_month_path}")
    print(f"Berlin calendar-month summary: {artifacts.city_calendar_path}")
    print(f"Berlin seasonal summary: {artifacts.season_summary_path}")
    print(f"Berlin annual exposure summary: {artifacts.year_summary_path}")
    print(f"Metadata: {artifacts.metadata_path}")
    print(f"Timing figure: {artifacts.timing_figure_path}")
    print(f"Calendar-month atlas: {artifacts.calendar_atlas_path}")
    print(f"Active-season atlas: {artifacts.active_season_atlas_path}")
    for path in artifacts.yearly_atlas_paths:
        print(f"Full-year monthly atlas: {path}")
    print(
        f"Rows: {artifacts.calendar_lor_rows:,} calendar LOR cells and "
        f"{artifacts.city_month_rows:,} Berlin months; shared positive breaks: "
        + ", ".join(f"{value:.3f}" for value in artifacts.map_breaks)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
