"""Build the agreed exploratory monthly watering report and tables."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from berlin_heat.watering_response import build_response_tables


if __name__ == "__main__":
    result = build_response_tables(ROOT, ROOT / "output/watering_response")
    print(result["metadata"]["audit"])
    print(result["tables"]["berlin_june_september_comparison"].to_string(index=False))
    print(result["tables"]["monthly_adjusted_associations"].drop(columns=["interpretation", "month_controls", "year_controls"]).to_string(index=False))
