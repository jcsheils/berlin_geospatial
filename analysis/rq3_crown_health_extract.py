"""Tree-circle greenness from Berlin's aerial images for the RQ3 crown-health test.

See docs/rq3_crown_health_protocol.md. Each flight is read through Berlin's map service
(WMS) as lossless PNG on the native 20 cm grid, one window around a cluster of trees at a
time. Before its windows, every shard reads the same 200 sampled windows to set the
flight's thresholds: vegetation is NDVI at or above the Otsu split of the sample, shadow
is brightness below half the sample's median. For circles of 1, 2 and 3 m around each
tree and a background ring of 3-5 m, only pixel counts and summaries are kept (mean
index, canopy fraction, greenness of sunlit vegetation, shadow share); for each window,
the SHA-256 of the response and the median values of its stable surfaces (sunlit pixels
without vegetation). No image is stored. The extraction holds no watering data.

Commands:
  plan        count trees and windows (no network access, no freeze needed)
  run         extract one shard of one flight
  crosscheck  compare the colour-infrared and colour layers of one flight in 50 windows
  chips       save 2025 colour chips of 200 young trees for the eye check
  combine     join the shard tables of one flight

Every command except plan refuses to start unless the plan matches its recorded hash.
"""
from __future__ import annotations

import argparse
import hashlib
import http.client
import io
import json
import time
import tomllib
import types
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/project.toml"
PROTOCOL = ROOT / "docs/rq3_crown_health_protocol.md"
INVENTORY_2025 = ROOT / "data/raw/tree_inventory/trees_2025_gbif.csv.gz"

PIXEL_M = 0.2
RADII_M = (1.0, 2.0, 3.0)
RING_M = (3.0, 5.0)  # background ring: beyond the widest circle, inside the neighbouring crowns
PAD_M = RING_M[1]
REGIONS = tuple(f"{r:g}m" for r in RADII_M) + ("ring",)
CALIBRATION_WINDOWS = 200
OTSU_BINS = 200  # NDVI histogram over [-1, 1]
SHADOW_SHARE_OF_MEDIAN = 0.5
EDGE_M2 = 1e-6  # a pixel centre on the circle counts as inside, whatever the rounding
CELL_M = 50.0
PLANTED = (1980, 2019)  # ages 1-40 in 2020: young cohort, placebo and older trees
YOUNG_PLANTED = (2005, 2019)
SEED = 42
CROSSCHECK_WINDOWS = 50
CROSSCHECK_MAX_DIFF = 2.0
EYE_CHECK_TREES = 200
CHIP_HALF_M = 5.0
CHIP_ZOOM = 4
SHARDS = 6
MAX_REQUESTS_PER_S = 3.0
ATTEMPTS = 6
WMS = "https://gdi.berlin.de/services/wms/"
USER_AGENT = "berlin-street-tree-crown-study/1.0"
FLIGHTS = {
    "2015": {"service": "dop_2015", "layer": "dop_2015_cir", "rgb": "dop_2015_rgb", "index": "ndvi"},
    "2020": {"service": "truedop_2020_sommer", "layer": "truedop_2020_sommer_cir", "rgb": "truedop_2020_sommer_rgb", "index": "ndvi"},
    "2020rgb": {"service": "truedop_2020_sommer", "layer": "truedop_2020_sommer_rgb", "rgb": "truedop_2020_sommer_rgb", "index": "gcc"},  # baseline for S7
    "2023": {"service": "truedop_2023_sommer", "layer": "truedop_2023_senweb", "rgb": "truedop_2023_senweb", "index": "gcc"},
    "2025": {"service": "truedop_2025_sommer", "layer": "truedop_2025_sommer_cir", "rgb": "truedop_2025_sommer_rgb", "index": "ndvi"},
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def frozen(config_text: str, protocol: bytes) -> bool:
    """True when the plan's SHA-256 matches the hash recorded in the config."""
    plan = tomllib.loads(config_text)["project"]["rq3_crown_health"]
    return plan.get("protocol_sha256") == sha256(protocol)


def require_freeze() -> None:
    if not frozen(CONFIG.read_text(), PROTOCOL.read_bytes()):
        raise SystemExit("The crown-health plan is not frozen: its SHA-256 does not match "
                         "config/project.toml. No image is read.")


def cohort(path: Path = INVENTORY_2025) -> pd.DataFrame:
    """Street trees planted 1980-2019 with planting year and position; no watering data."""
    trees = pd.read_csv(path, dtype={"tree_id": str}, usecols=["tree_id", "planting_year", "x_25833", "y_25833"])
    keep = trees["tree_id"].str.startswith("strassenbaeume.") & trees["planting_year"].between(*PLANTED)
    out = trees.loc[keep].rename(columns={"x_25833": "x", "y_25833": "y"}).drop_duplicates("tree_id")
    return out.sort_values("tree_id").reset_index(drop=True)


def windows(trees: pd.DataFrame, cell: float = CELL_M, pad: float = PAD_M) -> tuple[pd.DataFrame, pd.Series]:
    """One request window per occupied cell, and the window of each tree.

    Edges are integer pixel indices (coordinate = index * PIXEL_M), snapped outward so
    that the window holds every tree's background ring.
    """
    key = (np.floor(trees["x"] / cell).astype(np.int64).astype(str) + "_"
           + np.floor(trees["y"] / cell).astype(np.int64).astype(str))
    grouped = trees.assign(window=key).groupby("window")
    frame = pd.DataFrame({
        "ix0": np.floor((grouped["x"].min() - pad) / PIXEL_M).astype(np.int64),
        "ix1": np.ceil((grouped["x"].max() + pad) / PIXEL_M).astype(np.int64),
        "iy0": np.floor((grouped["y"].min() - pad) / PIXEL_M).astype(np.int64),
        "iy1": np.ceil((grouped["y"].max() + pad) / PIXEL_M).astype(np.int64),
    })
    frame["width"] = frame["ix1"] - frame["ix0"]
    frame["height"] = frame["iy1"] - frame["iy0"]
    frame["trees"] = grouped.size()
    return frame.sort_index(), pd.Series(key.to_numpy(), index=trees.index, name="window")


def getmap_url(service: str, layer: str, window) -> str:
    bbox = (window.ix0, window.iy0, window.ix1, window.iy1)
    params = {
        "SERVICE": "WMS", "VERSION": "1.1.1", "REQUEST": "GetMap", "LAYERS": layer, "STYLES": "",
        "SRS": "EPSG:25833", "BBOX": ",".join(f"{v * PIXEL_M:.1f}" for v in bbox),
        "WIDTH": str(int(window.width)), "HEIGHT": str(int(window.height)),
        "FORMAT": "image/png", "TRANSPARENT": "FALSE", "BGCOLOR": "0x000000",
    }
    return WMS + service + "?" + urllib.parse.urlencode(params)


class Client:
    """GET with a request-rate ceiling and retries with exponential back-off."""

    def __init__(self, rate: float = MAX_REQUESTS_PER_S, attempts: int = ATTEMPTS):
        self.interval = 1.0 / rate
        self.attempts = attempts
        self.last = 0.0

    def get(self, url: str) -> bytes:
        error: Exception | None = None
        for attempt in range(self.attempts):
            wait = self.last + self.interval - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            self.last = time.monotonic()
            try:
                request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
                with urllib.request.urlopen(request, timeout=60) as response:
                    body, kind = response.read(), response.headers.get("Content-Type", "")
                if kind.startswith("image/png"):
                    return body
                raise ValueError(f"not a PNG ({kind}): {body[:200]!r}")
            except (OSError, http.client.HTTPException, ValueError) as caught:
                error = caught
                time.sleep(min(60, 2 ** attempt))
        raise RuntimeError(f"{url}: {error}")


def decode(body: bytes, width: int, height: int) -> np.ndarray:
    """The three bands of a served PNG as a (height, width, 3) uint8 array, rows north to south."""
    image = Image.open(io.BytesIO(body))
    if image.format != "PNG" or image.mode not in ("RGB", "RGBA"):
        raise ValueError(f"expected a full-colour PNG, got {image.format} {image.mode}")
    if image.size != (width, height):
        raise ValueError(f"expected {width}x{height} pixels, got {image.size[0]}x{image.size[1]}")
    pixels = np.asarray(image)
    bands = pixels[:, :, :3].copy()
    if image.mode == "RGBA":
        bands[pixels[:, :, 3] == 0] = 0
    return bands


def index_values(bands: np.ndarray, index: str) -> np.ndarray:
    """NDVI from colour-infrared bands (near-infrared, red, green) or green share from colour bands."""
    b = bands.astype(np.float64)
    with np.errstate(invalid="ignore", divide="ignore"):
        if index == "ndvi":
            total = b[:, :, 0] + b[:, :, 1]
            return np.where(total > 0, (b[:, :, 0] - b[:, :, 1]) / total, np.nan)
        if index == "gcc":
            total = b.sum(axis=2)
            return np.where(total > 0, b[:, :, 1] / total, np.nan)
    raise ValueError(index)


def brightness(bands: np.ndarray) -> np.ndarray:
    """Mean of the three served bands, 0-255."""
    return bands.astype(np.float64).mean(axis=2)


def otsu(histogram: np.ndarray, edges: np.ndarray) -> float:
    """The split of a histogram that maximises the variance between the two classes (Otsu, 1979)."""
    centres = (edges[:-1] + edges[1:]) / 2
    weight = histogram.astype(np.float64)
    w0 = np.cumsum(weight)
    w1 = w0[-1] - w0
    m0 = np.cumsum(weight * centres)
    with np.errstate(invalid="ignore", divide="ignore"):
        between = w0 * w1 * (m0 / w0 - (m0[-1] - m0) / w1) ** 2
    between[~np.isfinite(between)] = -1
    return float(edges[int(np.argmax(between)) + 1])


def histogram_median(histogram: np.ndarray, edges: np.ndarray) -> float:
    cumulative = np.cumsum(histogram)
    return float(edges[int(np.searchsorted(cumulative, cumulative[-1] / 2)) + 1])


def calibrate(spec: dict, frame: pd.DataFrame, client) -> dict:
    """Thresholds of one flight from a fixed sample of windows, before any tree is summarised.

    Every shard draws the same sample (seed 42 over all windows), so all shards of a
    flight use the same thresholds; combine confirms it.
    """
    sample = frame.sample(n=min(CALIBRATION_WINDOWS, len(frame)), random_state=SEED)
    ndvi_edges = np.linspace(-1.0, 1.0, OTSU_BINS + 1)
    light_edges = np.arange(0.0, 257.0, 1.0)
    ndvi_hist = np.zeros(OTSU_BINS, dtype=np.int64)
    light_hist = np.zeros(len(light_edges) - 1, dtype=np.int64)
    for window in sample.itertuples():
        bands = decode(client.get(getmap_url(spec["service"], spec["layer"], window)), window.width, window.height)
        inside = bands.any(axis=2)
        light_hist += np.histogram(brightness(bands)[inside], bins=light_edges)[0]
        if spec["index"] == "ndvi":
            values = index_values(bands, "ndvi")[inside]
            ndvi_hist += np.histogram(values[~np.isnan(values)], bins=ndvi_edges)[0]
    result = {"windows": int(len(sample)), "pixels": int(light_hist.sum()), "seed": SEED,
              "shadow": SHADOW_SHARE_OF_MEDIAN * histogram_median(light_hist, light_edges)}
    result["vegetation"] = otsu(ndvi_hist, ndvi_edges) if spec["index"] == "ndvi" else None
    return result


def stable_surfaces(bands: np.ndarray, index: str, thresholds: dict) -> dict:
    """Median values of the window's sunlit pixels without vegetation (roofs, paving)."""
    empty = {"stable_pixels": 0, "stable_nir": np.nan, "stable_red": np.nan, "stable_ndvi": np.nan}
    if index != "ndvi":
        return empty
    values = index_values(bands, "ndvi")
    stable = bands.any(axis=2) & ~np.isnan(values) & (values < thresholds["vegetation"]) & (brightness(bands) >= thresholds["shadow"])
    if not stable.any():
        return empty
    return {"stable_pixels": int(stable.sum()), "stable_nir": float(np.median(bands[:, :, 0][stable])),
            "stable_red": float(np.median(bands[:, :, 1][stable])), "stable_ndvi": float(np.median(values[stable]))}


def region_columns(index: str) -> list[str]:
    kinds = ["pixels", "in_image", index, "shadow_frac"] + (["veg_frac", "veg_ndvi"] if index == "ndvi" else [])
    return [f"{kind}_{region}" for region in REGIONS for kind in kinds]


def circle_stats(bands: np.ndarray, window, trees: pd.DataFrame, index: str, thresholds: dict | None = None) -> pd.DataFrame:
    """Pixel counts and summaries within each circle and the background ring of each tree.

    Pixel (row r, column c) has its centre at x = (ix0 + c + 0.5) * PIXEL_M and
    y = (iy1 - r - 0.5) * PIXEL_M. A pixel with all three bands at zero lies outside
    the image. With thresholds, each region also gets its shadow share and, for NDVI,
    its canopy fraction (share of pixels at or above the vegetation threshold) and the
    mean NDVI of its sunlit vegetation pixels.
    """
    height, width = bands.shape[:2]
    values = index_values(bands, index)
    inside = bands.any(axis=2)
    light = brightness(bands)
    reach = int(np.ceil(PAD_M / PIXEL_M)) + 1
    regions = {f"{r:g}m": (None, r) for r in RADII_M} | {"ring": RING_M}
    records = []
    for tree in trees.itertuples():
        col = tree.x / PIXEL_M - window.ix0 - 0.5
        row = window.iy1 - tree.y / PIXEL_M - 0.5
        cols = np.arange(int(np.floor(col)) - reach, int(np.ceil(col)) + reach + 1)
        rows = np.arange(int(np.floor(row)) - reach, int(np.ceil(row)) + reach + 1)
        cc, rr = np.meshgrid(cols, rows)
        distance2 = ((cc - col) ** 2 + (rr - row) ** 2) * PIXEL_M ** 2
        in_array = (rr >= 0) & (rr < height) & (cc >= 0) & (cc < width)
        rr_c, cc_c = np.clip(rr, 0, height - 1), np.clip(cc, 0, width - 1)
        present = inside[rr_c, cc_c] & in_array
        local = values[rr_c, cc_c]
        dark = light[rr_c, cc_c] < thresholds["shadow"] if thresholds else None
        record = {"tree_id": tree.tree_id}
        for label, (inner, outer) in regions.items():
            within = distance2 <= outer ** 2 + EDGE_M2
            if inner is not None:
                within &= distance2 > inner ** 2 + EDGE_M2
            usable = within & present & ~np.isnan(local)
            record[f"pixels_{label}"] = int(within.sum())
            record[f"in_image_{label}"] = int((within & present).sum())
            record[f"{index}_{label}"] = float(local[usable].mean()) if usable.any() else np.nan
            if thresholds is None:
                continue
            seen = within & present
            record[f"shadow_frac_{label}"] = float((dark & seen).sum() / seen.sum()) if seen.any() else np.nan
            if index == "ndvi":
                vegetated = usable & (local >= thresholds["vegetation"])
                sunlit = vegetated & ~dark
                record[f"veg_frac_{label}"] = float(vegetated.sum() / usable.sum()) if usable.any() else np.nan
                record[f"veg_ndvi_{label}"] = float(local[sunlit].mean()) if sunlit.any() else np.nan
        records.append(record)
    return pd.DataFrame(records)


WINDOW_COLUMNS = ["window", "sha256", "bytes", "error", "stable_pixels", "stable_nir", "stable_red", "stable_ndvi"]


def code_hash() -> str:
    return sha256(Path(__file__).read_bytes())


def run(flight: str, shard: int, shards: int, out: Path, client: Client | None = None,
        trees: pd.DataFrame | None = None) -> dict:
    """Extract the circles of one shard of windows for one flight."""
    require_freeze()
    spec = FLIGHTS[flight]
    trees = cohort() if trees is None else trees
    frame, membership = windows(trees)
    by_window = trees.assign(window=membership).groupby("window")
    part = frame.iloc[shard::shards]
    client = client or Client()
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    thresholds = calibrate(spec, frame, client)
    tables, log = [], []
    for window in part.itertuples():
        try:
            body = client.get(getmap_url(spec["service"], spec["layer"], window))
            bands = decode(body, window.width, window.height)
        except (RuntimeError, ValueError) as error:
            log.append({"window": window.Index, "sha256": "", "bytes": 0, "error": str(error)[:300]})
            continue
        log.append({"window": window.Index, "sha256": sha256(body), "bytes": len(body), "error": "",
                    **stable_surfaces(bands, spec["index"], thresholds)})
        tables.append(circle_stats(bands, window, by_window.get_group(window.Index), spec["index"], thresholds).assign(window=window.Index))
    out.mkdir(parents=True, exist_ok=True)
    stem = f"{flight}_shard{shard}"
    columns = ["tree_id", "window"] + region_columns(spec["index"])
    table = pd.concat(tables, ignore_index=True)[columns] if tables else pd.DataFrame(columns=columns)
    table.to_csv(out / f"{stem}_trees.csv.gz", index=False)
    pd.DataFrame(log, columns=WINDOW_COLUMNS).to_csv(out / f"{stem}_windows.csv.gz", index=False)
    summary = {
        "flight": flight, "service": spec["service"], "layer": spec["layer"], "shard": shard, "shards": shards,
        "thresholds": thresholds,
        "windows": int(len(part)), "failed_windows": int(sum(bool(entry["error"]) for entry in log)),
        "trees": int(len(table)), "started_utc": started,
        "finished_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "protocol_sha256": sha256(PROTOCOL.read_bytes()), "code_sha256": code_hash(),
        "inventory_sha256": sha256(INVENTORY_2025.read_bytes()),
    }
    (out / f"{stem}.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def crosscheck(flight: str, out: Path, client: Client | None = None, trees: pd.DataFrame | None = None) -> dict:
    """Compare the red and green bands of the colour-infrared and colour layers in sampled windows."""
    require_freeze()
    spec = FLIGHTS[flight]
    if spec["index"] != "ndvi":
        raise SystemExit(f"{flight} has no colour-infrared layer to cross-check.")
    frame, _ = windows(cohort() if trees is None else trees)
    sample = frame.sample(n=min(CROSSCHECK_WINDOWS, len(frame)), random_state=SEED)
    client = client or Client()
    red, green, rows = [], [], []
    for window in sample.itertuples():
        cir = decode(client.get(getmap_url(spec["service"], spec["layer"], window)), window.width, window.height)
        rgb = decode(client.get(getmap_url(spec["service"], spec["rgb"], window)), window.width, window.height)
        both = cir.any(axis=2) & rgb.any(axis=2)
        red.append(np.abs(cir[:, :, 1][both].astype(int) - rgb[:, :, 0][both]))
        green.append(np.abs(cir[:, :, 2][both].astype(int) - rgb[:, :, 1][both]))
        rows.append({"window": window.Index, "pixels": int(both.sum())})
    red_diff = float(np.median(np.concatenate(red))) if red else float("nan")
    green_diff = float(np.median(np.concatenate(green))) if green else float("nan")
    result = {
        "flight": flight, "windows": rows, "seed": SEED,
        "red_median_abs_diff": red_diff, "green_median_abs_diff": green_diff,
        "passes": bool(red_diff <= CROSSCHECK_MAX_DIFF and green_diff <= CROSSCHECK_MAX_DIFF),
        "protocol_sha256": sha256(PROTOCOL.read_bytes()), "code_sha256": code_hash(),
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{flight}_crosscheck.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def chips(out: Path, client: Client | None = None, trees: pd.DataFrame | None = None) -> pd.DataFrame:
    """Colour chips of 200 young trees from the 2025 flight with the 2 m circle drawn, for the eye check."""
    require_freeze()
    trees = cohort() if trees is None else trees
    young = trees[trees["planting_year"].between(*YOUNG_PLANTED)]
    sample = young.sample(n=min(EYE_CHECK_TREES, len(young)), random_state=SEED)
    spec = FLIGHTS["2025"]
    client = client or Client()
    half = int(round(CHIP_HALF_M / PIXEL_M))
    folder = out / "chips"
    folder.mkdir(parents=True, exist_ok=True)
    index = []
    for number, tree in enumerate(sample.itertuples()):
        cx, cy = int(round(tree.x / PIXEL_M)), int(round(tree.y / PIXEL_M))
        window = types.SimpleNamespace(ix0=cx - half, ix1=cx + half, iy0=cy - half, iy1=cy + half,
                                       width=2 * half, height=2 * half)
        bands = decode(client.get(getmap_url(spec["service"], spec["rgb"], window)), window.width, window.height)
        image = Image.fromarray(bands).resize((window.width * CHIP_ZOOM, window.height * CHIP_ZOOM), Image.NEAREST)
        col = (tree.x / PIXEL_M - window.ix0) * CHIP_ZOOM
        row = (window.iy1 - tree.y / PIXEL_M) * CHIP_ZOOM
        radius = 2.0 / PIXEL_M * CHIP_ZOOM
        ImageDraw.Draw(image).ellipse([col - radius, row - radius, col + radius, row + radius], outline=(255, 0, 255), width=2)
        name = f"{number:03d}.png"
        image.save(folder / name)
        index.append({"chip": name, "tree_id": tree.tree_id, "on_tree": ""})
    table = pd.DataFrame(index)
    table.to_csv(out / "eye_check.csv", index=False)
    return table


def combine(flight: str, folder: Path, out: Path) -> dict:
    """Join the shard tables of one flight and confirm that every window was requested once."""
    require_freeze()
    summaries = [json.loads(p.read_text()) for p in sorted(folder.glob(f"{flight}_shard*.json"))]
    shards = {s["shards"] for s in summaries}
    if len(shards) != 1 or sorted(s["shard"] for s in summaries) != list(range(shards.pop())):
        raise SystemExit(f"{flight}: shard summaries are incomplete.")
    if len({json.dumps(s["thresholds"], sort_keys=True) for s in summaries}) != 1:
        raise SystemExit(f"{flight}: shards set different thresholds.")
    trees = pd.concat([pd.read_csv(folder / f"{flight}_shard{s['shard']}_trees.csv.gz", dtype={"tree_id": str, "window": str})
                       for s in summaries], ignore_index=True)
    log = pd.concat([pd.read_csv(folder / f"{flight}_shard{s['shard']}_windows.csv.gz", dtype={"window": str}, keep_default_na=False)
                     for s in summaries], ignore_index=True)
    if log["window"].duplicated().any() or trees["tree_id"].duplicated().any():
        raise SystemExit(f"{flight}: a window or tree appears twice.")
    out.mkdir(parents=True, exist_ok=True)
    trees.to_csv(out / f"crown_circles_{flight}.csv.gz", index=False)
    log.to_csv(out / f"crown_windows_{flight}.csv.gz", index=False)
    summary = {
        "flight": flight, "windows": int(len(log)), "failed_windows": int((log["error"] != "").sum()),
        "trees": int(len(trees)), "thresholds": summaries[0]["thresholds"], "shards": summaries,
    }
    (out / f"crown_circles_{flight}.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def plan() -> dict:
    trees = cohort()
    frame, _ = windows(trees)
    pixels = int((frame["width"] * frame["height"]).sum())
    return {
        "street_trees_planted_1980_2019": int(len(trees)),
        "young_planted_2005_2019": int(trees["planting_year"].between(*YOUNG_PLANTED).sum()),
        "windows": int(len(frame)),
        "calibration_windows_per_shard": CALIBRATION_WINDOWS,
        "pixels_per_flight": pixels,
        "raw_gb_per_flight": round(pixels * 3 / 1e9, 2),
        "shards": SHARDS,
        "hours_per_shard_at_rate_ceiling": round((len(frame) / SHARDS + CALIBRATION_WINDOWS) / MAX_REQUESTS_PER_S / 3600, 1),
        "plan_frozen": frozen(CONFIG.read_text(), PROTOCOL.read_bytes()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("plan")
    for name in ("run", "crosscheck", "combine"):
        command = commands.add_parser(name)
        command.add_argument("--flight", required=True, choices=sorted(FLIGHTS))
        command.add_argument("--out", type=Path, required=True)
    commands.choices["run"].add_argument("--shard", type=int, required=True)
    commands.choices["run"].add_argument("--shards", type=int, default=SHARDS)
    commands.choices["combine"].add_argument("--folder", type=Path, required=True)
    commands.add_parser("chips").add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "plan":
        result = plan()
    elif args.command == "run":
        result = run(args.flight, args.shard, args.shards, args.out)
    elif args.command == "crosscheck":
        result = crosscheck(args.flight, args.out)
    elif args.command == "chips":
        result = {"chips": len(chips(args.out))}
    else:
        result = combine(args.flight, args.folder, args.out)
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
