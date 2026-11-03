import json
import os
from pathlib import Path
import tempfile
from urllib.parse import urlencode
from urllib.request import urlopen

import geopandas as gpd


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data/spatial/lor_equity_environment_2024.gpkg"
TARGET_CRS = "EPSG:25833"

SOURCES = {
    "mss2025_indizes_542": (
        "https://gdi.berlin.de/services/wfs/mss_2025",
        "mss_2025:mss2025_indizes_542",
    ),
    "mss2025_indexind_542": (
        "https://gdi.berlin.de/services/wfs/mss_2025",
        "mss_2025:mss2025_indexind_542",
    ),
    "environmental_justice_2023_2024": (
        "https://gdi.berlin.de/services/wfs/ua_umweltgerechtigkeit2023",
        "ua_umweltgerechtigkeit2023:z_gesamt_umwelt2023",
    ),
}


def download_layer(endpoint, feature_type):
    query = urlencode(
        {
            "service": "WFS",
            "version": "2.0.0",
            "request": "GetFeature",
            "typeNames": feature_type,
            "outputFormat": "application/json",
            "srsName": TARGET_CRS,
        }
    )
    with urlopen(f"{endpoint}?{query}", timeout=120) as response:
        payload = json.load(response)

    features = payload.get("features", [])
    frame = gpd.GeoDataFrame.from_features(features, crs=TARGET_CRS)

    expected = int(payload.get("numberMatched", payload.get("totalFeatures", len(frame))))
    assert len(frame) == expected == 542, (
        f"{feature_type}: expected 542 Planungsraeume, received {len(frame)}."
    )
    assert frame["plr_id"].is_unique, f"{feature_type}: plr_id is not unique."
    assert frame.geometry.notna().all(), f"{feature_type}: missing geometries."
    return frame


def main():
    # Fetch and validate every source before touching the current artifact.
    layers = []
    for layer_name, (endpoint, feature_type) in SOURCES.items():
        frame = download_layer(endpoint, feature_type)
        layers.append((layer_name, frame))
        print(f"Fetched {layer_name}: {len(frame):,} features")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{OUTPUT.stem}-",
        suffix=OUTPUT.suffix,
        dir=OUTPUT.parent,
    )
    os.close(descriptor)
    temporary_output = Path(temporary_name)
    temporary_output.unlink()

    try:
        for layer_name, frame in layers:
            frame.to_file(temporary_output, layer=layer_name, driver="GPKG")
            print(f"Staged {layer_name}: {len(frame):,} features")
        os.replace(temporary_output, OUTPUT)
    finally:
        temporary_output.unlink(missing_ok=True)

    print(f"Created {OUTPUT}")


if __name__ == "__main__":
    main()
