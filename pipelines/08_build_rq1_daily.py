"""Build the refined proposal's RQ1 daily exploratory pilot."""
import argparse
from pathlib import Path

from berlin_heat.paths import find_project_root
from berlin_heat.rq1_daily import build_daily_pilot


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=None)
    parser.add_argument("--unavailable-dates", type=Path, default=None,
                        help="Optional CSV with a unique date column for unavailable platform days")
    args = parser.parse_args()
    result = build_daily_pilot(find_project_root(args.root), unavailable_path=args.unavailable_dates)
    print(f"Built {result['area_day_rows']:,} area-days; {result['season_events']:,} seasonal events.")
    print("Report: output/rq1_daily/report.md")


if __name__ == "__main__":
    main()
