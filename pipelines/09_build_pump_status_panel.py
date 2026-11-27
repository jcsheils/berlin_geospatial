"""Build the OpenStreetMap street-pump status panel (RQ2 treatment side only).

Reads the frozen full-history snapshot in data/raw/osm_pumps/. Pass --download
once to acquire and freeze a snapshot from the ohsome API; an existing snapshot
is never replaced implicitly. The build joins no watering outcome.
"""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from berlin_heat.paths import find_project_root  # noqa: E402
from berlin_heat.pump_status import build_pump_status, download_snapshot  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=None)
    parser.add_argument("--download", action="store_true",
                        help="Acquire and freeze a new ohsome snapshot when none exists")
    args = parser.parse_args()
    root = find_project_root(args.root or ROOT)
    if args.download:
        snapshot = download_snapshot(root)
        print(f"Froze OSM history to {snapshot['data_end_utc']}: "
              f"{snapshot['requests']['histories']['nodes']:,} nodes, "
              f"{snapshot['requests']['histories']['features']:,} versions.")
    audit = build_pump_status(root)
    changes = audit["changes"]
    print(f"Universe: {audit['selection']['universe_pumps']:,} pumps; "
          f"{changes['all']:,} status changes ({changes['repairs_and_failures']:,} repairs or failures, "
          f"{changes['repairs_and_failures_check_date_backed_pct']}% check_date-backed).")
    print("Audit: output/pump_status/report.md")


if __name__ == "__main__":
    main()
