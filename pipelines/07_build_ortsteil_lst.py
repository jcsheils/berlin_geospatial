"""Run the monthly Ortsteil source audit and provisional descriptive extension."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from berlin_heat.ortsteil_lst import build_ortsteil_extension

if __name__ == "__main__":
    result = build_ortsteil_extension(ROOT)
    print(result["metadata"]["source_audit"])
    print(result["metadata"]["spatial_audit"])
    print(result["tables"]["provisional_pooled_correlations"].query(
        "sample == 'April-September_2021-2025' and screen == 'all_available_LST'"
    ).to_string(index=False))
