"""Dated OpenStreetMap status panel for Berlin's street pumps (RQ2 treatment side).

The revised design (docs/revised_research_design_2026_11.md, RQ2 item 1) compares
logged watering near street pumps before and after a repair or failure. This
module builds only the treatment side: a frozen full-history snapshot, a table
of dated status changes, a pump x April-September season panel, an audit, and
design-feasibility counts of catalogued street trees near pumps. It never reads
the watering logs, so the design and its smallest effect of interest can be
registered before any outcome is examined. Rules: docs/pump_status_protocol.md.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile
from typing import Any, Iterable, Mapping
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd

OHSOME_API = "https://api.ohsome.org/v1"
USER_AGENT = "osm-history-client/1.0"
SNAPSHOT_DIR = Path("data/raw/osm_pumps")
PROCESSED_DIR = Path("data/processed/rq2_pumps")
OUTPUT_DIR = Path("output/pump_status")
DISCOVERY_ARCHIVE = "ohsome_discovery_full_history.geojson.gz"
HISTORY_ARCHIVE = "ohsome_node_histories_part{number:02d}.geojson.gz"
HISTORY_CHUNK = 500  # the API rejects an id filter listing all ~2,400 nodes at once
BOUNDARY_FILE = "query_boundary_epsg4326.geojson"
HISTORY_START = "2007-10-08T00:00:00Z"  # first timestamp held by the OSHDB
BOUNDARY_BUFFER_M = 100
BOUNDARY_SIMPLIFY_M = 10
HISTORY_BBOX_MARGIN_DEG = 0.1
TIMEZONE = "Europe/Berlin"
ANALYSIS_CRS = "EPSG:25833"
SEASONS = tuple(range(2019, 2026))
RADII_M = (100, 200)
IN_BERLIN_TOLERANCE_M = 10.0
PLATFORM_NETWORK = "Berliner Straßenbrunnen"
# The platform's harvester (technologiestiftung/giessdenkiez-de-osm-pumpen-harvester)
# selects man_made=water_well + network=Berliner Straßenbrunnen since commit c938dcb
# (10 May 2021) and description=Berliner Straßenbrunnen before it.
NETWORK_SELECTOR_FROM = pd.Timestamp("2021-05-10", tz=TIMEZONE)
# Pump layers the harvester published (out/pumps.geojson), one per selector era; the
# build checks that the snapshot reproduces them at their commit instants.
PLATFORM_LAYER_URL = ("https://raw.githubusercontent.com/technologiestiftung/"
                      "giessdenkiez-de-osm-pumpen-harvester/{commit}/out/pumps.geojson")
PLATFORM_LAYERS = (
    {"commit": "9eb7bee524d3c15f1f2ca79878637554df960cd0", "committed_utc": "2021-05-02T04:07:01Z",
     "archive": "platform_pumps_2021-05-02_9eb7bee.geojson.gz"},
    {"commit": "b7471fcd15aaeb40c0c32d17d9c21f1dbb6b5754", "committed_utc": "2023-04-02T04:05:56Z",
     "archive": "platform_pumps_2023-04-02_b7471fc.geojson.gz"},
)
CHECK_DATE_WINDOW_DAYS = 365
CHECK_DATE_EDIT_TOLERANCE = pd.Timedelta(days=1)
SUCCESSOR_RADIUS_M = 15.0
SUCCESSOR_WINDOW = pd.Timedelta(days=31)
REVERT_WINDOW_DAYS = 14
DUPLICATE_RADIUS_M = 5.0
REPORTED_2022 = {
    "pumps": 2079,
    "working": 1614,
    "status_year": 2022,
    "source": "Berliner Mieterverein, 'Berliner Wasserpumpen: Trinkwasser per Muskelkraft' (04/2024), "
              "reporting 2,079 street pumps of which 1,614 worked (status 2022)",
}

DISCOVERY_FILTER = (
    "type:node and (man_made=water_well or network=\"Berliner Straßenbrunnen\" "
    "or description=\"Berliner Straßenbrunnen\" or name=\"Berliner Straßenbrunnen\" "
    "or removed:man_made=water_well or razed:man_made=water_well "
    "or demolished:man_made=water_well or destroyed:man_made=water_well "
    "or was:man_made=water_well or disused:man_made=water_well "
    "or abandoned:man_made=water_well or pump:status=* or removed:pump:status=*)"
)

# Status vocabulary. usable: 1 water can be drawn, 0 it cannot, missing unknown.
USABLE = {"working": 1, "broken": 0, "locked": 0, "pump_absent": 0, "disused": 0, "removed": 0}
LIFECYCLE_PREFIXES = (
    ("removed", "removed"), ("razed", "removed"), ("demolished", "removed"),
    ("destroyed", "removed"), ("was", "removed"), ("disused", "disused"), ("abandoned", "disused"),
)
STATUS_KEYS = ("pump:status", "pump_status", "pump.status", "operational_status",
               "operational:status", "status")
STATUS_CODES = {
    "ok": "working", "functional": "working", "working": "working",
    "broken": "broken", "missing_beam": "broken", "out_of_order": "broken",
    "non_functional": "broken", "damaged": "broken", "defekt": "broken",
    "locked": "locked", "blocked": "locked",
    "missing": "removed",
}
# Every free-text pump:status value in the frozen snapshot whose meaning is clear, read
# and classified once. "?", "off" and an "unbekannt, ..." note are left unrecognised;
# values not listed here become "unrecognised" (usable unknown) and are reported.
FREE_TEXT_STATUS = {
    "funktioniert (<30x pumpen), allerdings geringe Hubwirkung, von Pflanzen zugewachsen": "working",
    "Wird regelmäßig für die Straßenbaumbewässerung genutzt (queerfish | giessdenkiez.de)": "working",
    "queerfish nutzt diese Pumpe für Straßenbaumbewässerung (giessdenkiez.de)": "working",
    "regelmäßig in Gebrauch für adoptierte Straßenbäume (giessdenkiez.de)": "working",
    "es kommt Wasser, aber die Pumpe blockiert manchmal": "working",
    "funktioniert, aber geringe Hubleistung": "working",
    "Die Pumpe liefert nach einmaligem pumpen Wasser": "working",
    "<10x pumpen": "working",
    "Pumpen ist trotz Handschwengel nicht möglich. (Kein Gegendruck)": "broken",
    "Der Bolzen vom Handschwengel fehlt.": "broken",
    "Abgebaut": "removed",
    "nicht vorhanden": "removed",
    "Nicht mehr vorhanden": "removed",
    "Die Pumpe ist nicht vorhanden": "removed",
    "Die Pumpe wurde entfernt. Hier gibt es keine Pumpe mehr. Stand: 2022": "removed",
    "Diese Pumpe existiert nicht mehr. Vermutlich wurde sie für einen Fußgängerübergang demontiert.": "removed",
}
# The harvester's display mapping of pump:status; other values are shown unchanged.
PLATFORM_LABELS = {
    "ok": "funktionsfähig", "broken": "defekt", "missing_beam": "defekt", "out_of_order": "defekt",
    "locked": "verriegelt", "blocked": "verriegelt",
}
CHANGE_TYPES = ("repair", "failure", "status_reported", "status_withdrawn", "reclassified",
                "exit", "reentry")


@dataclass(frozen=True)
class StatusReading:
    status: str
    source: str
    raw_value: str | None = None

    @property
    def usable(self) -> int | None:
        return USABLE.get(self.status)


@dataclass(frozen=True)
class CheckDate:
    value: date
    precision: str  # day, month or year; value is the first day of the stated period


def _code(value: str) -> str:
    return re.sub(r"[\s.]+", "", value.strip().lower())


def map_status_value(value: str) -> str | None:
    """Map one status tag value to a category, or None when it is not understood."""
    text = str(value).strip()
    if text in FREE_TEXT_STATUS:
        return FREE_TEXT_STATUS[text]
    return STATUS_CODES.get(_code(text))


def parse_status(tags: Mapping[str, Any]) -> StatusReading:
    """Harmonised status of one OSM version (rules in docs/pump_status_protocol.md)."""
    man_made = str(tags.get("man_made") or "")
    if man_made != "water_well":
        for prefix, status in LIFECYCLE_PREFIXES:
            if tags.get(f"{prefix}:man_made") == "water_well" or man_made == f"{prefix}:water_well":
                return StatusReading(status, f"{prefix}:man_made")
        return StatusReading("not_a_pump", f"man_made={man_made}" if man_made else "no_man_made")
    unrecognised: tuple[str, str] | None = None
    for key in STATUS_KEYS:
        value = tags.get(key)
        if value is None or not str(value).strip():
            continue
        mapped = map_status_value(str(value))
        if mapped:
            return StatusReading(mapped, key, str(value))
        unrecognised = unrecognised or (key, str(value))
    for key, status in (("disused", "disused"), ("abandoned", "disused"), ("locked", "locked")):
        if str(tags.get(key, "")).strip().lower() == "yes":
            return StatusReading(status, f"{key}=yes")
    if str(tags.get("pump", "")).strip().lower() == "no":
        return StatusReading("pump_absent", "pump=no")
    if "removed:pump" in tags:
        return StatusReading("pump_absent", "removed:pump")
    if unrecognised:
        return StatusReading("unrecognised", unrecognised[0], unrecognised[1])
    return StatusReading("unknown", "none")


def platform_label(tags: Mapping[str, Any]) -> str:
    """The label the platform's harvester derives from pump:status."""
    value = tags.get("pump:status")
    if value is None:
        return "unbekannt"
    return PLATFORM_LABELS.get(str(value), str(value))


def parse_check_date(value: Any) -> CheckDate | None:
    """Parse check_date as a day, month or year; return None when unparseable."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    text = str(value).strip()
    patterns = ((r"(\d{4})-(\d{1,2})-(\d{1,2})", "ymd", "day"),
                (r"(\d{1,2})\.(\d{1,2})\.(\d{4})", "dmy", "day"),
                (r"(\d{4})-(\d{1,2})", "ym", "month"),
                (r"(\d{4})", "y", "year"))
    for pattern, order, precision in patterns:
        match = re.fullmatch(pattern, text)
        if not match:
            continue
        parts = [int(part) for part in match.groups()]
        try:
            if order == "ymd":
                parsed = date(parts[0], parts[1], parts[2])
            elif order == "dmy":
                parsed = date(parts[2], parts[1], parts[0])
            elif order == "ym":
                parsed = date(parts[0], parts[1], 1)
            else:
                parsed = date(parts[0], 1, 1)
        except ValueError:
            return None
        return CheckDate(parsed, precision) if 1990 <= parsed.year <= 2100 else None
    return None


def classify_change(from_status: str, to_status: str) -> str:
    """Type of a transition between two harmonised statuses."""
    if to_status in ("deleted", "not_a_pump"):
        return "exit"
    if from_status in ("deleted", "not_a_pump"):
        return "reentry"
    before, after = USABLE.get(from_status), USABLE.get(to_status)
    if before == 0 and after == 1:
        return "repair"
    if before == 1 and after == 0:
        return "failure"
    if before is None and after is not None:
        return "status_reported"
    if before is not None and after is None:
        return "status_withdrawn"
    return "reclassified"


def season_bounds(season: int) -> tuple[pd.Timestamp, pd.Timestamp]:
    """1 April 00:00 to 1 October 00:00 Europe/Berlin, as UTC instants."""
    start = pd.Timestamp(f"{season}-04-01", tz=TIMEZONE).tz_convert("UTC")
    end = pd.Timestamp(f"{season}-10-01", tz=TIMEZONE).tz_convert("UTC")
    return start, end


def local_date(instant: pd.Timestamp) -> date:
    return instant.tz_convert(TIMEZONE).date()


# ---------------------------------------------------------------------------
# Snapshot acquisition and loading
# ---------------------------------------------------------------------------

def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def freeze_bytes(data: bytes) -> bytes:
    """Deterministic gzip: level 9, mtime 0, no embedded file name."""
    return gzip.compress(data, compresslevel=9, mtime=0)


def _request(endpoint: str, params: Mapping[str, str] | None, timeout: float) -> bytes:
    data = urlencode(params).encode("utf-8") if params is not None else None
    request = Request(f"{OHSOME_API}/{endpoint}", data=data,
                      headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urlopen(request, timeout=timeout) as response:
        if response.status != 200:
            raise RuntimeError(f"ohsome {endpoint} returned HTTP {response.status}")
        return response.read()


def _round_coordinates(value: Any, digits: int = 6) -> Any:
    if isinstance(value, (list, tuple)):
        return [_round_coordinates(item, digits) for item in value]
    return round(float(value), digits)


def _read_lor(root: Path):
    import geopandas as gpd
    lor = gpd.read_file(root / "data/spatial/lor_planungsraeume_2021.gpkg", layer="a_lor_plr_2021",
                        columns=["plr_id", "plr_name", "bzr_id", "bzr_name", "bez"])
    if len(lor) != 542 or not lor["plr_id"].is_unique:
        raise ValueError("The declared LOR layer is not the expected 542-unit vintage.")
    lor = lor.to_crs(ANALYSIS_CRS)
    lor["district"] = lor["bez"].str.replace(r"^\d+\s*-\s*", "", regex=True)
    return lor


def query_boundary(root: Path) -> dict:
    """Berlin query polygon: LOR 2021 union, buffered and simplified, in EPSG:4326."""
    import geopandas as gpd
    import shapely
    from shapely.geometry import mapping

    union = shapely.union_all(_read_lor(root).geometry.values)
    area = union.buffer(BOUNDARY_BUFFER_M).simplify(BOUNDARY_SIMPLIFY_M)
    area = gpd.GeoSeries([area], crs=ANALYSIS_CRS).to_crs("EPSG:4326").iloc[0]
    geometry = mapping(area)
    geometry = {"type": geometry["type"], "coordinates": _round_coordinates(geometry["coordinates"])}
    return {"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": {"id": "berlin_lor_2021_buffer_100m"}, "geometry": geometry}]}


def _node_sort_key(osm_id: str) -> tuple[str, int]:
    kind, _, number = osm_id.partition("/")
    return kind, int(number)


def _by_node(frame: pd.DataFrame, *columns: str) -> pd.DataFrame:
    """Sort by numeric OSM node id (then the given columns), not by the id string."""
    order = frame.assign(_node=frame["osm_id"].str.partition("/")[2].astype("int64"))
    return order.sort_values(["_node", *columns], kind="stable").drop(columns="_node").reset_index(drop=True)


def download_snapshot(root: Path, *, timeout: float = 900, replace: bool = False) -> dict:
    """Acquire and freeze the full-history snapshot (network access; run once).

    Step 1 selects every Berlin node that was ever a water well, carried a
    lifecycle-prefixed water well, a platform selector tag or a pump status.
    Step 2 requests every version of those nodes by id, so versions that no
    longer match the tag filter (retagging, tag removal) are kept as well.
    """
    folder = root / SNAPSHOT_DIR
    if (folder / "snapshot.json").exists() and not replace:
        raise FileExistsError(f"{folder}/snapshot.json exists; the frozen snapshot is not refreshed "
                              "implicitly. Pass replace=True to acquire a new one.")
    metadata = json.loads(_request("metadata", None, timeout))
    data_end = pd.Timestamp(metadata["extractRegion"]["temporalExtent"]["toTimestamp"])
    data_end_text = data_end.tz_convert("UTC").strftime("%Y-%m-%dT%H:%M:%SZ")
    time_range = f"{HISTORY_START},{data_end_text}"
    boundary = query_boundary(root)
    boundary_text = json.dumps(boundary, ensure_ascii=False, separators=(",", ":")) + "\n"
    discovery_params = {"bpolys": boundary_text.strip(), "time": time_range,
                        "filter": DISCOVERY_FILTER, "properties": "tags,metadata"}
    discovery = _request("elementsFullHistory/geometry", discovery_params, timeout)
    discovery_doc = json.loads(discovery)
    ids = sorted({f["properties"]["@osmId"] for f in discovery_doc["features"]}, key=_node_sort_key)
    if not ids or any(not osm_id.startswith("node/") for osm_id in ids):
        raise ValueError("Discovery returned no nodes or non-node elements.")
    from shapely.geometry import shape
    west, south, east, north = shape(boundary["features"][0]["geometry"]).bounds
    margin = HISTORY_BBOX_MARGIN_DEG  # generous box: a moved node must not look deleted
    bbox = ",".join(f"{value:.4f}" for value in (west - margin, south - margin, east + margin, north + margin))
    def describe(raw: bytes, doc: dict, archive: str) -> tuple[dict, bytes]:
        frozen = freeze_bytes(raw)
        return {"archive": archive, "archive_bytes": len(frozen), "archive_sha256": _sha256_bytes(frozen),
                "response_bytes": len(raw), "response_sha256": _sha256_bytes(raw),
                "features": len(doc["features"]),
                "nodes": len({f["properties"]["@osmId"] for f in doc["features"]}),
                "api_version": doc.get("apiVersion")}, frozen

    discovery_info, discovery_frozen = describe(discovery, discovery_doc, DISCOVERY_ARCHIVE)
    parts, frozen_parts, history_ids = [], {}, set()
    for number, chunk in enumerate(history_chunks(ids), start=1):
        history_filter = "id:(" + ",".join(chunk) + ")"
        raw = _request("elementsFullHistory/geometry", {"bboxes": bbox, "time": time_range,
                                                        "filter": history_filter,
                                                        "properties": "tags,metadata"}, timeout)
        doc = json.loads(raw)
        received = {f["properties"]["@osmId"] for f in doc["features"]}
        if received - set(chunk):
            raise ValueError(f"History part {number} returned nodes outside its id filter.")
        history_ids |= received
        info, frozen = describe(raw, doc, HISTORY_ARCHIVE.format(number=number))
        info.update(first_id=chunk[0], last_id=chunk[-1], requested_ids=len(chunk),
                    filter_sha256=_sha256_bytes(history_filter.encode("utf-8")))
        parts.append(info)
        frozen_parts[info["archive"]] = frozen
    if set(ids) - history_ids:
        raise ValueError(f"{len(set(ids) - history_ids)} discovered nodes are missing from the histories.")
    snapshot = {
        "packaged_date": datetime.now(timezone.utc).date().isoformat(),
        "retrieved_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "ohsome API (HeiGIT) over the OpenStreetMap full-history database (OSHDB)",
        "api_url": OHSOME_API,
        "api_version": metadata.get("apiVersion"),
        "history_start_utc": HISTORY_START,
        "data_end_utc": data_end_text,
        "replication_sequence_number": metadata["extractRegion"].get("replicationSequenceNumber"),
        "licence": "Open Database License 1.0 (ODbL); © OpenStreetMap contributors",
        "attribution": metadata.get("attribution", {}).get("text"),
        "boundary": {"file": BOUNDARY_FILE, "sha256": _sha256_bytes(boundary_text.encode("utf-8")),
                     "derivation": f"Union of the 542 LOR 2021 planning areas, buffered {BOUNDARY_BUFFER_M} m "
                                   f"and simplified {BOUNDARY_SIMPLIFY_M} m in {ANALYSIS_CRS}, then EPSG:4326 "
                                   "rounded to 6 decimals"},
        "requests": {
            "discovery": {"endpoint": "elementsFullHistory/geometry", "spatial": f"bpolys={BOUNDARY_FILE}",
                          "time": time_range, "filter": DISCOVERY_FILTER, "properties": "tags,metadata",
                          **discovery_info},
            "histories": {"endpoint": "elementsFullHistory/geometry", "spatial": f"bboxes={bbox}",
                          "time": time_range, "properties": "tags,metadata", "chunk_size": HISTORY_CHUNK,
                          "filter": "id:(<consecutive chunk of the discovery node ids, ascending, "
                                    "comma-separated>)",
                          "nodes": len(history_ids), "features": sum(part["features"] for part in parts),
                          "parts": parts},
        },
        "compression": "gzip level 9, mtime 0, no embedded file name; archives hold the exact response bytes",
    }
    folder.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".osm_pumps-", dir=folder.parent))
    try:
        (staging / DISCOVERY_ARCHIVE).write_bytes(discovery_frozen)
        for name, frozen in frozen_parts.items():
            (staging / name).write_bytes(frozen)
        (staging / BOUNDARY_FILE).write_text(boundary_text, encoding="utf-8")
        (staging / "snapshot.json").write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n",
                                               encoding="utf-8")
        for name in (DISCOVERY_ARCHIVE, *frozen_parts, BOUNDARY_FILE, "snapshot.json"):
            (staging / name).replace(folder / name)
    finally:
        shutil.rmtree(staging, ignore_errors=True)
    return freeze_platform_layers(root, timeout=timeout)


def freeze_platform_layers(root: Path, *, timeout: float = 120, replace: bool = False) -> dict:
    """Freeze the platform's published pump layers and record them in snapshot.json."""
    path = root / SNAPSHOT_DIR / "snapshot.json"
    snapshot = json.loads(path.read_text(encoding="utf-8"))
    if "validation" in snapshot and not replace:
        raise FileExistsError("snapshot.json already records the platform layers.")
    layers = []
    for layer in PLATFORM_LAYERS:
        url = PLATFORM_LAYER_URL.format(commit=layer["commit"])
        with urlopen(Request(url, headers={"User-Agent": USER_AGENT}), timeout=timeout) as response:
            raw = response.read()
        frozen = freeze_bytes(raw)
        (root / SNAPSHOT_DIR / layer["archive"]).write_bytes(frozen)
        layers.append({**layer, "url": url, "features": len(json.loads(raw)["features"]),
                       "archive_bytes": len(frozen), "archive_sha256": _sha256_bytes(frozen),
                       "response_bytes": len(raw), "response_sha256": _sha256_bytes(raw)})
    snapshot["validation"] = {
        "platform_layers": layers,
        "purpose": "Pump layers the platform's harvester published (weekly Overpass query); the build checks "
                   "that the snapshot reproduces their pump ids, labels and check dates at the commit instant.",
        "retrieved_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    path.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return snapshot


def platform_replication(versions: pd.DataFrame, root: Path, snapshot: Mapping[str, Any]) -> list[dict]:
    """Compare the snapshot's platform selection with the frozen published layers."""
    rows = []
    for layer in snapshot.get("validation", {}).get("platform_layers", []):
        published = {f"node/{f['properties']['id']}": f["properties"]
                     for f in read_frozen(root / SNAPSHOT_DIR, layer)["features"]}
        instant = pd.Timestamp(layer["committed_utc"])
        current = versions[(versions["valid_from"] <= instant) & (versions["valid_to"] > instant)]
        selector = "network_selector" if instant >= NETWORK_SELECTOR_FROM else "description_selector"
        replicated = current[current["is_water_well"] & current[selector]].set_index("osm_id")
        common = sorted(set(published) & set(replicated.index))
        check = replicated["check_date_raw"].where(replicated["check_date_raw"].notna(), "unbekannt")
        rows.append({
            "commit": layer["commit"][:7], "committed_utc": layer["committed_utc"],
            "selector": selector.removesuffix("_selector"), "published_pumps": len(published),
            "replicated_pumps": len(replicated), "in_both": len(common),
            "only_published": len(set(published) - set(replicated.index)),
            "only_replicated": len(set(replicated.index) - set(published)),
            "status_label_agreement": sum(published[i].get("pump:status") == replicated.at[i, "platform_label"]
                                          for i in common),
            "check_date_agreement": sum((published[i].get("check_date") or "unbekannt") == check.at[i]
                                        for i in common),
        })
    return rows


def history_chunks(ids: list[str], size: int = HISTORY_CHUNK) -> list[list[str]]:
    return [ids[start:start + size] for start in range(0, len(ids), size)]


def read_frozen(folder: Path, info: Mapping[str, Any]) -> dict:
    """Read one frozen response after verifying both checksums."""
    archive = folder / info["archive"]
    frozen = archive.read_bytes()
    if _sha256_bytes(frozen) != info["archive_sha256"]:
        raise ValueError(f"Archive checksum mismatch: {archive}")
    raw = gzip.decompress(frozen)
    if _sha256_bytes(raw) != info["response_sha256"]:
        raise ValueError(f"Response checksum mismatch after decompression: {archive}")
    return json.loads(raw)


def load_snapshot(root: Path) -> tuple[dict, dict, dict]:
    folder = root / SNAPSHOT_DIR
    if not (folder / "snapshot.json").is_file():
        raise FileNotFoundError(f"No frozen snapshot in {folder}; run the pipeline once with --download.")
    snapshot = json.loads((folder / "snapshot.json").read_text(encoding="utf-8"))
    boundary = folder / snapshot["boundary"]["file"]
    if _sha256_file(boundary) != snapshot["boundary"]["sha256"]:
        raise ValueError("Query boundary checksum mismatch.")
    discovery = read_frozen(folder, snapshot["requests"]["discovery"])
    ids = sorted({f["properties"]["@osmId"] for f in discovery["features"]}, key=_node_sort_key)
    parts = snapshot["requests"]["histories"]["parts"]
    chunks = history_chunks(ids, snapshot["requests"]["histories"]["chunk_size"])
    if len(chunks) != len(parts):
        raise ValueError("The history parts do not cover the discovery node list.")
    features: list[dict] = []
    for chunk, part in zip(chunks, parts):
        expected = "id:(" + ",".join(chunk) + ")"
        if _sha256_bytes(expected.encode("utf-8")) != part["filter_sha256"]:
            raise ValueError(f"{part['archive']} was not requested for the expected discovery nodes.")
        features.extend(read_frozen(folder, part)["features"])
    return snapshot, discovery, {"features": features}


# ---------------------------------------------------------------------------
# Versions, segments and changes
# ---------------------------------------------------------------------------

VERSION_COLUMNS = ["osm_id", "version", "changeset_id", "valid_from", "valid_to", "lon", "lat",
                   "is_water_well", "network_selector", "description_selector", "name_variant",
                   "status", "status_source", "status_raw", "platform_label", "check_date_raw",
                   "check_date", "check_date_precision", "ref", "official_ref"]


def versions_from_features(features: Iterable[Mapping[str, Any]]) -> pd.DataFrame:
    """One row per OSM node version with its harmonised status."""
    rows = []
    for feature in features:
        props = feature["properties"]
        tags = {key: str(value) for key, value in props.items() if not key.startswith("@")}
        coordinates = (feature.get("geometry") or {}).get("coordinates") or [np.nan, np.nan]
        reading = parse_status(tags)
        check = parse_check_date(tags.get("check_date"))
        rows.append({
            "osm_id": props["@osmId"], "version": int(props["@version"]),
            "changeset_id": str(props.get("@changesetId", "")),
            "valid_from": props["@validFrom"], "valid_to": props["@validTo"],
            "lon": float(coordinates[0]), "lat": float(coordinates[1]),
            "is_water_well": tags.get("man_made") == "water_well",
            "network_selector": tags.get("network") == PLATFORM_NETWORK,
            "description_selector": tags.get("description") == PLATFORM_NETWORK,
            "name_variant": tags.get("name") == PLATFORM_NETWORK,
            "status": reading.status, "status_source": reading.source, "status_raw": reading.raw_value,
            "platform_label": platform_label(tags),
            "check_date_raw": tags.get("check_date"),
            "check_date": check.value if check else None,
            "check_date_precision": check.precision if check else None,
            "ref": tags.get("ref"), "official_ref": tags.get("official_ref"),
        })
    frame = pd.DataFrame(rows, columns=VERSION_COLUMNS)
    frame["valid_from"] = pd.to_datetime(frame["valid_from"], utc=True)
    frame["valid_to"] = pd.to_datetime(frame["valid_to"], utc=True)
    frame["usable"] = frame["status"].map(USABLE).astype("Int64")
    frame = frame.sort_values(["osm_id", "valid_from", "version"], kind="stable").reset_index(drop=True)
    if frame.duplicated(["osm_id", "valid_from"]).any():
        raise ValueError("Two versions of one node start at the same instant.")
    if (frame["valid_to"] <= frame["valid_from"]).any():
        raise ValueError("A version ends before it starts.")
    return frame


def status_segments(versions: pd.DataFrame, snapshot_end: pd.Timestamp) -> pd.DataFrame:
    """Contiguous status segments per node; validity gaps and early ends become 'deleted'.

    A node's history starts at its first version mapped as a pump or former pump:
    earlier versions (untagged, or another feature later retagged) count as not
    yet mapped. check_date_updated marks versions that add or change check_date
    relative to the node's previous version (the first pump version counts).
    """
    rows: list[dict] = []
    for osm_id, group in versions.groupby("osm_id", sort=True):
        previous_end: pd.Timestamp | None = None
        previous_check: str | None = None
        last = None
        pump_related = group["status"].ne("not_a_pump").to_numpy()
        if not pump_related.any():
            continue
        for record in group.iloc[int(pump_related.argmax()):].itertuples(index=False):
            if previous_end is not None and record.valid_from < previous_end:
                raise ValueError(f"Overlapping versions for {osm_id}.")
            if previous_end is not None and record.valid_from > previous_end:
                rows.append(_deleted(osm_id, previous_end, record.valid_from, last))
            check_raw = record.check_date_raw if isinstance(record.check_date_raw, str) else None
            rows.append({
                "osm_id": osm_id, "segment_start": record.valid_from, "segment_end": record.valid_to,
                "version": record.version, "changeset_id": record.changeset_id,
                "status": record.status, "usable": record.usable, "status_source": record.status_source,
                "status_raw": record.status_raw, "is_water_well": bool(record.is_water_well),
                "network_selector": bool(record.network_selector),
                "description_selector": bool(record.description_selector),
                "check_date_raw": check_raw, "check_date": record.check_date,
                "check_date_precision": record.check_date_precision,
                "check_date_updated": check_raw is not None and check_raw != previous_check,
                "lon": record.lon, "lat": record.lat,
            })
            previous_check = check_raw if check_raw is not None else previous_check
            previous_end, last = record.valid_to, record
        if previous_end is not None and previous_end < snapshot_end:
            rows.append(_deleted(osm_id, previous_end, snapshot_end, last))
    frame = pd.DataFrame(rows)
    frame["usable"] = frame["usable"].astype("Int64")
    frame["version"] = frame["version"].astype("Int64")
    return frame


def _deleted(osm_id: str, start: pd.Timestamp, end: pd.Timestamp, last: Any) -> dict:
    return {"osm_id": osm_id, "segment_start": start, "segment_end": end, "version": pd.NA,
            "changeset_id": None, "status": "deleted", "usable": pd.NA, "status_source": "no_version",
            "status_raw": None, "is_water_well": False, "network_selector": False,
            "description_selector": False, "check_date_raw": None, "check_date": None,
            "check_date_precision": None, "check_date_updated": False,
            "lon": getattr(last, "lon", np.nan), "lat": getattr(last, "lat", np.nan)}


def status_changes(segments: pd.DataFrame, snapshot_end: pd.Timestamp) -> pd.DataFrame:
    """One row per transition between harmonised statuses of a node.

    The first mapping of a node is not a change. A change is check_date-backed
    when a version within one day of the status edit adds or changes check_date
    and that date is no later than one day after, and no more than 365 days
    before, the edit's Europe/Berlin date.
    """
    rows: list[dict] = []
    for osm_id, group in segments.groupby("osm_id", sort=True):
        records = list(group.itertuples(index=False))
        updates = [(r.segment_start, r) for r in records if r.check_date_updated]
        for previous, current in zip(records, records[1:]):
            if current.status == previous.status:
                continue
            edit_time = current.segment_start
            edit_date = local_date(edit_time)
            check = None
            if current.status != "deleted":
                near = [(abs(time - edit_time), time != edit_time, r) for time, r in updates
                        if abs(time - edit_time) <= CHECK_DATE_EDIT_TOLERANCE]
                if near:
                    check = min(near, key=lambda item: (item[0], item[1]))[2]
            check_value = check.check_date if check is not None else None
            lag = (edit_date - check_value).days if check_value is not None else None
            backed = lag is not None and -1 <= lag <= CHECK_DATE_WINDOW_DAYS
            backed_day = backed and check.check_date_precision == "day"
            rows.append({
                "osm_id": osm_id, "change_time_utc": edit_time, "edit_date": edit_date,
                "from_status": previous.status, "to_status": current.status,
                "from_usable": previous.usable, "to_usable": current.usable,
                "change_type": classify_change(previous.status, current.status),
                "version": current.version, "changeset_id": current.changeset_id,
                "status_source": current.status_source, "status_raw": current.status_raw,
                "check_date_raw": check.check_date_raw if check is not None else None,
                "check_date_precision": check.check_date_precision if check is not None else None,
                "check_date_lag_days": lag, "check_date_backed": bool(backed),
                "check_date_backed_day": bool(backed_day),
                "event_date": check_value if backed_day else edit_date,
                "event_date_basis": "check_date" if backed_day else "edit",
            })
    columns = ["osm_id", "change_time_utc", "edit_date", "from_status", "to_status", "from_usable",
               "to_usable", "change_type", "version", "changeset_id", "status_source", "status_raw",
               "check_date_raw", "check_date_precision", "check_date_lag_days", "check_date_backed",
               "check_date_backed_day", "event_date", "event_date_basis"]
    frame = pd.DataFrame(rows, columns=columns)
    if frame.empty:
        return frame.assign(new_status_days=pd.Series(dtype=float), right_censored=pd.Series(dtype=bool),
                            reverted_within_14d=pd.Series(dtype=bool),
                            net_change_if_restored=pd.Series(dtype=object))
    frame = _by_node(frame, "change_time_utc")
    following = frame.groupby("osm_id")["change_time_utc"].shift(-1)
    following_status = frame.groupby("osm_id")["to_status"].shift(-1)
    ends = following.fillna(snapshot_end)
    frame["new_status_days"] = ((ends - frame["change_time_utc"]).dt.total_seconds() / 86400).round(2)
    frame["right_censored"] = following.isna()
    frame["reverted_within_14d"] = (following_status.eq(frame["from_status"])
                                    & frame["new_status_days"].le(REVERT_WINDOW_DAYS)).fillna(False)
    # A deleted or retagged node that is later restored: record the net transition
    # across the gap (e.g. working -> deleted -> removed is a net failure at the exit).
    restored = frame["change_type"].eq("exit") & frame.groupby("osm_id")["change_type"].shift(-1).eq("reentry")
    frame["net_change_if_restored"] = None
    frame.loc[restored, "net_change_if_restored"] = [
        classify_change(before, after) if before != after else "none"
        for before, after in zip(frame.loc[restored, "from_status"], following_status[restored])]
    for column in ("from_usable", "to_usable", "version", "check_date_lag_days"):
        frame[column] = frame[column].astype("Int64")
    return frame


def status_at(segments: pd.DataFrame, instant: pd.Timestamp) -> pd.DataFrame:
    """Segment of every mapped node at an instant, indexed by osm_id."""
    current = segments[(segments["segment_start"] <= instant) & (segments["segment_end"] > instant)].copy()
    if current["osm_id"].duplicated().any():
        raise ValueError("Overlapping status segments.")
    selector = current["network_selector"] if instant >= NETWORK_SELECTOR_FROM else current["description_selector"]
    current["platform_visible"] = current["is_water_well"] & selector
    return current.set_index("osm_id")


# ---------------------------------------------------------------------------
# Pump universe, positions and the season panel
# ---------------------------------------------------------------------------

def pump_register(versions: pd.DataFrame, lor) -> pd.DataFrame:
    """Per-node selection facts and reference positions (last version) in EPSG:25833."""
    import geopandas as gpd
    import shapely

    last = versions.groupby("osm_id").tail(1).set_index("osm_id")
    grouped = versions.groupby("osm_id")
    pump_versions = versions[versions["status"].ne("not_a_pump")]
    register = pd.DataFrame({
        "first_mapped_utc": pump_versions.groupby("osm_id")["valid_from"].min(),
        "last_edit_utc": grouped["valid_from"].max(),
        "n_versions": grouped.size(),
        "ever_network_selector": grouped["network_selector"].any(),
        "ever_description_selector": grouped["description_selector"].any(),
        "ever_name_variant": grouped["name_variant"].any(),
        "ever_water_well": grouped["is_water_well"].any(),
        "ref": grouped["ref"].agg(lambda s: s.dropna().iloc[-1] if s.notna().any() else None),
        "official_ref": grouped["official_ref"].agg(lambda s: s.dropna().iloc[-1] if s.notna().any() else None),
        "lon": last["lon"], "lat": last["lat"],
    })
    selector_rows = versions[versions["network_selector"] | versions["description_selector"]]
    register["selector_first_seen_utc"] = selector_rows.groupby("osm_id")["valid_from"].min()
    points = gpd.GeoSeries(gpd.points_from_xy(register["lon"], register["lat"]), index=register.index,
                           crs="EPSG:4326").to_crs(ANALYSIS_CRS)
    register["x_25833"], register["y_25833"] = points.x.round(2), points.y.round(2)
    all_points = gpd.GeoSeries(gpd.points_from_xy(versions["lon"], versions["lat"]), crs="EPSG:4326").to_crs(ANALYSIS_CRS)
    reference = points.reindex(versions["osm_id"]).reset_index(drop=True)
    register["max_displacement_m"] = pd.Series(all_points.distance(reference).to_numpy(),
                                               index=versions["osm_id"]).groupby(level=0).max().round(1)
    berlin = shapely.union_all(lor.geometry.values).buffer(IN_BERLIN_TOLERANCE_M)
    register["in_berlin"] = shapely.contains_xy(berlin, points.x.to_numpy(), points.y.to_numpy())
    frame = gpd.GeoDataFrame(register[[]], geometry=points, crs=ANALYSIS_CRS)
    joined = gpd.sjoin_nearest(frame, lor[["plr_id", "bzr_id", "district", "geometry"]],
                               how="left", max_distance=IN_BERLIN_TOLERANCE_M)
    joined = joined[~joined.index.duplicated(keep="first")]
    for column in ("plr_id", "bzr_id", "district"):
        register[column] = joined[column].reindex(register.index)
    register["in_universe"] = (register["ever_network_selector"] | register["ever_description_selector"]) \
        & register["in_berlin"]
    register.index.name = "osm_id"
    return register.reset_index()


def attach_successors(changes: pd.DataFrame, segments: pd.DataFrame, register: pd.DataFrame) -> pd.DataFrame:
    """Flag deletions where another pump node takes over within 15 m (remapping, not removal)."""
    from scipy.spatial import cKDTree

    changes = changes.copy()
    changes["successor_osm_id"] = None
    changes["successor_relation"] = None
    changes["successor_distance_m"] = np.nan
    exits = changes.index[changes["to_status"].eq("deleted")]
    if len(exits) == 0 or register.empty:
        return changes
    positions = register.set_index("osm_id")[["x_25833", "y_25833"]]
    tree = cKDTree(positions.to_numpy())
    first_mapped = register.set_index("osm_id")["first_mapped_utc"]
    for index in exits:
        row = changes.loc[index]
        origin = positions.loc[row["osm_id"]].to_numpy()
        candidates = [positions.index[i] for i in tree.query_ball_point(origin, SUCCESSOR_RADIUS_M)
                      if positions.index[i] != row["osm_id"]]
        if not candidates:
            continue
        at_exit = status_at(segments[segments["osm_id"].isin(candidates)], row["change_time_utc"])
        found = []
        for candidate in candidates:
            distance = float(np.hypot(*(positions.loc[candidate].to_numpy() - origin)))
            if candidate in at_exit.index and bool(at_exit.loc[candidate, "is_water_well"]):
                found.append((distance, "concurrent_node", candidate))
            elif abs(first_mapped.loc[candidate] - row["change_time_utc"]) <= SUCCESSOR_WINDOW:
                found.append((distance, "new_node_within_31d", candidate))
        if found:
            distance, relation, candidate = min(found)
            changes.loc[index, ["successor_osm_id", "successor_relation", "successor_distance_m"]] = \
                [candidate, relation, round(distance, 1)]
    return changes


def season_panel(osm_ids: Iterable[str], segments: pd.DataFrame, changes: pd.DataFrame,
                 seasons: Iterable[int] = SEASONS) -> pd.DataFrame:
    """Balanced pump x April-September season panel built from edit times."""
    ids = pd.Index(sorted(osm_ids, key=_node_sort_key), name="osm_id")
    segments = segments[segments["osm_id"].isin(ids)]
    changes = changes[changes["osm_id"].isin(ids)]
    first = segments.sort_values("segment_start").groupby("osm_id").head(1).set_index("osm_id")
    frames = []
    for season in seasons:
        start, end = season_bounds(season)
        at_start = status_at(segments, start).reindex(ids)
        at_end = status_at(segments, end).reindex(ids)
        frame = pd.DataFrame(index=ids)
        frame["season"] = season
        frame["season_start"] = f"{season}-04-01"
        frame["season_end"] = f"{season}-09-30"
        frame["mapped_at_start"] = at_start["status"].notna()
        frame["status_at_start"] = at_start["status"].fillna("not_mapped")
        frame["usable_at_start"] = at_start["usable"].astype("Int64")
        frame["status_source_at_start"] = at_start["status_source"]
        frame["platform_visible_at_start"] = at_start["platform_visible"].astype("boolean").fillna(False).astype(bool)
        frame["check_date_at_start"] = at_start["check_date"]
        frame["check_date_precision_at_start"] = at_start["check_date_precision"]
        frame["days_since_check_at_start"] = at_start["check_date"].map(
            lambda value: (start.tz_convert(TIMEZONE).date() - value).days if isinstance(value, date) else pd.NA
        ).astype("Int64")
        first_start = first["segment_start"].reindex(ids)
        mapped_in_season = (first_start >= start) & (first_start < end)
        frame["mapped_in_season"] = mapped_in_season.fillna(False).astype(bool)
        frame["status_at_end"] = at_end["status"].fillna("not_mapped")
        frame["usable_at_end"] = at_end["usable"].astype("Int64")
        window = changes[(changes["change_time_utc"] >= start) & (changes["change_time_utc"] < end)]
        window = window.sort_values(["osm_id", "change_time_utc"], kind="stable")
        counts = window.groupby(["osm_id", "change_type"]).size().unstack(fill_value=0)
        frame["n_status_changes"] = window.groupby("osm_id").size().reindex(ids).fillna(0).astype(int)
        for change_type in CHANGE_TYPES:
            column = counts[change_type] if change_type in counts else pd.Series(dtype=int)
            frame[f"n_{change_type}"] = column.reindex(ids).fillna(0).astype(int)
        first_change = window.groupby("osm_id").head(1).set_index("osm_id")
        frame["first_change_date"] = first_change["edit_date"].reindex(ids)
        frame["first_change_type"] = first_change["change_type"].reindex(ids)
        for change_type in ("repair", "failure"):
            subset = window[window["change_type"].eq(change_type)]
            frame[f"first_{change_type}_date"] = subset.groupby("osm_id")["edit_date"].min().reindex(ids)
        dated = window[window["change_type"].isin(["repair", "failure"])]
        frame["repair_or_failure"] = frame.index.isin(dated["osm_id"])
        frame["repair_or_failure_check_backed"] = frame.index.isin(dated.loc[dated["check_date_backed"], "osm_id"])
        checks = segments[(segments["segment_start"] >= start) & (segments["segment_start"] < end)
                          & segments["check_date_updated"]]
        frame["n_check_date_updates"] = checks.groupby("osm_id").size().reindex(ids).fillna(0).astype(int)
        steps = pd.concat([
            first.loc[first.index.isin(ids[frame["mapped_in_season"].to_numpy()]), ["segment_start", "status"]]
                 .rename(columns={"segment_start": "time"}).reset_index(),
            window[["osm_id", "change_time_utc", "to_status"]].rename(
                columns={"change_time_utc": "time", "to_status": "status"}),
        ]).sort_values(["osm_id", "time"], kind="stable")
        path = steps.groupby("osm_id")["status"].agg(">".join).reindex(ids)
        frame["status_path"] = np.where(path.notna(), frame["status_at_start"] + ">" + path.fillna(""),
                                        frame["status_at_start"])
        frames.append(frame.reset_index())
    return pd.concat(frames, ignore_index=True)


# ---------------------------------------------------------------------------
# Street trees near pumps (design feasibility only)
# ---------------------------------------------------------------------------

def load_street_trees(root: Path) -> np.ndarray:
    """EPSG:25833 coordinates of catalogued street trees in the frozen inventory."""
    import pyogrio

    path = root / "data/Berlin_trees.gpkg"
    if not path.is_file():
        raise FileNotFoundError("Run `python tools/restore_tree_inventory.py` to restore the inventory.")
    expected = json.loads((root / "data/raw/tree_inventory/snapshot.json").read_text())["uncompressed_sha256"]
    if _sha256_file(path) != expected:
        raise ValueError(f"{path} is not the frozen inventory snapshot.")
    trees = pyogrio.read_dataframe(path, layer="Berlin_trees", columns=["pitid", "source_layer"])
    bounds = trees.total_bounds
    if not (bounds[0] > 300_000 and bounds[1] > 5_000_000):
        raise ValueError("Tree coordinates do not look like the documented EPSG:25833 metres.")
    trees = trees.dropna(subset=["pitid"]).copy()
    trees["layer"] = trees["source_layer"].str.replace("baumbestand:", "", regex=False)
    # One row per tree ID, preferring the street-tree row (as in the November benchmarks).
    trees = trees.sort_values("layer", ascending=False, kind="stable").drop_duplicates("pitid")
    street = trees[trees["layer"].eq("strassenbaeume")]
    return np.column_stack([street.geometry.x.to_numpy(), street.geometry.y.to_numpy()])


def trees_within(points: np.ndarray, tree_xy: np.ndarray, radii: Iterable[int] = RADII_M) -> pd.DataFrame:
    """Number of trees within each radius (inclusive) of every point."""
    from scipy.spatial import cKDTree

    index = cKDTree(tree_xy)
    return pd.DataFrame({f"street_trees_{radius}m": index.query_ball_point(points, radius, return_length=True)
                         for radius in radii})


def _unique_trees(index, points: np.ndarray, radius: int) -> set[int]:
    if len(points) == 0:
        return set()
    hits = index.query_ball_point(points, radius)
    return set(np.concatenate([np.asarray(h, dtype=np.int64) for h in hits])) if len(hits) else set()


def design_feasibility(panel: pd.DataFrame, positions: pd.DataFrame, tree_xy: np.ndarray,
                       radii: Iterable[int] = RADII_M) -> pd.DataFrame:
    """Pumps and distinct street trees near treated and comparison pumps, per season.

    Treated: a repair or failure in the season. Comparison: mapped as a water well
    at season start and end with a known start status and no status change of any
    type in the season. Comparison trees exclude trees near a treated pump.
    """
    from scipy.spatial import cKDTree

    index = cKDTree(tree_xy)
    xy = positions.set_index("osm_id")[["x_25833", "y_25833"]]
    rows = []
    for season, frame in panel.groupby("season", sort=True):
        active_end = ~frame["status_at_end"].isin(["deleted", "not_a_pump", "not_mapped", "removed", "disused"])
        groups = {
            "repair": frame["n_repair"].gt(0),
            "failure": frame["n_failure"].gt(0),
            "repair_or_failure": frame["repair_or_failure"],
            "repair_or_failure_check_backed": frame["repair_or_failure_check_backed"],
            "unchanged_comparison": frame["mapped_at_start"] & frame["usable_at_start"].notna()
                                    & frame["n_status_changes"].eq(0) & active_end,
        }
        treated = {radius: _unique_trees(index, xy.loc[frame.loc[groups["repair_or_failure"], "osm_id"]].to_numpy(),
                                         radius) for radius in radii}
        for group, mask in groups.items():
            ids = frame.loc[mask, "osm_id"]
            row = {"season": season, "group": group, "pumps": int(mask.sum())}
            for radius in radii:
                near = _unique_trees(index, xy.loc[ids].to_numpy(), radius)
                if group == "unchanged_comparison":
                    row[f"trees_within_{radius}m_also_near_treated"] = len(near & treated[radius])
                    near = near - treated[radius]
                row[f"trees_within_{radius}m"] = len(near)
            rows.append(row)
    table = pd.DataFrame(rows)
    for radius in radii:
        column = f"trees_within_{radius}m_also_near_treated"
        table[column] = table[column].astype("Int64")
    order = ["season", "group", "pumps"] + [f"trees_within_{r}m" for r in radii] + \
            [f"trees_within_{r}m_also_near_treated" for r in radii]
    return table[order]


# ---------------------------------------------------------------------------
# Audit tables
# ---------------------------------------------------------------------------

def _duplicate_pairs(points: np.ndarray) -> int:
    from scipy.spatial import cKDTree
    return 0 if len(points) < 2 else len(cKDTree(points).query_pairs(DUPLICATE_RADIUS_M))


def pumps_by_season_start(panel: pd.DataFrame, segments: pd.DataFrame, register: pd.DataFrame) -> pd.DataFrame:
    xy = register.set_index("osm_id")[["x_25833", "y_25833"]]
    rows = []
    for season, frame in panel.groupby("season", sort=True):
        start, _ = season_bounds(season)
        at_start = status_at(segments[segments["osm_id"].isin(frame["osm_id"])], start)
        wells = at_start.index[at_start["is_water_well"].to_numpy(dtype=bool)]
        counts = frame["status_at_start"].value_counts()
        mapped_wells = frame[frame["osm_id"].isin(wells)]
        row = {"season": season, "date": f"{season}-04-01",
               "universe_nodes": len(frame), "mapped": int(frame["mapped_at_start"].sum()),
               "mapped_as_water_well": len(wells),
               "platform_visible": int(frame["platform_visible_at_start"].sum())}
        for status in ("working", "broken", "locked", "pump_absent", "unknown", "unrecognised",
                       "disused", "removed", "not_a_pump", "deleted", "not_mapped"):
            row[status] = int(counts.get(status, 0))
        known = mapped_wells["usable_at_start"].notna()
        row["water_wells_with_known_status_pct"] = round(100 * known.mean(), 1) if len(mapped_wells) else np.nan
        row["working_pct_of_known"] = round(100 * mapped_wells.loc[known, "usable_at_start"].eq(1).mean(), 1) \
            if known.any() else np.nan
        row["water_wells_with_check_date"] = int(mapped_wells["check_date_at_start"].notna().sum())
        row["median_days_since_check"] = float(mapped_wells["days_since_check_at_start"].dropna().median()) \
            if mapped_wells["days_since_check_at_start"].notna().any() else np.nan
        row["mapped_in_season"] = int(frame["mapped_in_season"].sum())
        row["possible_duplicate_pairs_within_5m"] = _duplicate_pairs(xy.loc[wells].to_numpy())
        rows.append(row)
    return pd.DataFrame(rows)


def changes_by_year(changes: pd.DataFrame) -> pd.DataFrame:
    data = changes.assign(year=pd.to_datetime(changes["edit_date"]).dt.year,
                          in_season=pd.to_datetime(changes["edit_date"]).dt.month.between(4, 9))
    rows = []
    for (year, change_type), frame in data.groupby(["year", "change_type"], sort=True):
        rows.append({"year": int(year), "change_type": change_type, "changes": len(frame),
                     "in_april_september": int(frame["in_season"].sum()),
                     "nodes": int(frame["osm_id"].nunique()),
                     "check_date_backed": int(frame["check_date_backed"].sum()),
                     "check_date_backed_day": int(frame["check_date_backed_day"].sum()),
                     "reverted_within_14d": int(frame["reverted_within_14d"].sum())})
    table = pd.DataFrame(rows)
    table["check_date_backed_pct"] = (100 * table["check_date_backed"] / table["changes"]).round(1)
    return table


def comparison_2022(segments: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for label in ("2022-01-01", "2022-04-01", "2022-07-01", "2022-10-01", "2022-12-31"):
        instant = pd.Timestamp(label, tz=TIMEZONE).tz_convert("UTC")
        current = status_at(segments, instant)
        wells = current[current["is_water_well"]]
        known = wells["usable"].notna()
        rows.append({
            "source": "OpenStreetMap (this snapshot)", "date": label,
            "pumps": len(wells), "platform_visible": int(current["platform_visible"].sum()),
            "working": int(wells["status"].eq("working").sum()),
            "not_working": int(wells["usable"].eq(0).sum()),
            "status_unknown": int((~known).sum()),
            "working_pct_of_pumps": round(100 * wells["status"].eq("working").mean(), 1),
            "working_pct_of_known_status": round(100 * wells.loc[known, "status"].eq("working").mean(), 1),
            "lifecycle_removed_or_disused": int(current["status"].isin(["removed", "disused"]).sum()),
        })
    reported = REPORTED_2022
    rows.append({"source": reported["source"], "date": "2022 (status year)", "pumps": reported["pumps"],
                 "platform_visible": pd.NA, "working": reported["working"],
                 "not_working": reported["pumps"] - reported["working"], "status_unknown": pd.NA,
                 "working_pct_of_pumps": round(100 * reported["working"] / reported["pumps"], 1),
                 "working_pct_of_known_status": round(100 * reported["working"] / reported["pumps"], 1),
                 "lifecycle_removed_or_disused": pd.NA})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

def _format(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    for column in out.columns:
        if pd.api.types.is_datetime64_any_dtype(out[column]):
            out[column] = out[column].dt.tz_convert("UTC").dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        elif out[column].dtype == object:
            out[column] = out[column].map(lambda v: v.isoformat() if isinstance(v, date) else v)
    return out


def _write_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    _format(frame).to_csv(temporary, index=False, lineterminator="\n")
    temporary.replace(path)


def _clean(value: Any) -> Any:
    """JSON-safe copy: missing values become null, numpy scalars and dates plain values."""
    if isinstance(value, Mapping):
        return {str(key): _clean(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_clean(item) for item in value]
    if isinstance(value, pd.Timestamp):
        return value.tz_convert("UTC").strftime("%Y-%m-%dT%H:%M:%SZ") if value.tzinfo else value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, np.generic):
        value = value.item()
    if value is None or value is pd.NA or (isinstance(value, float) and np.isnan(value)):
        return None
    return value


def _records(frame: pd.DataFrame) -> list[dict]:
    return [_clean(row) for row in frame.astype(object).to_dict(orient="records")]


def _write_json(document: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(_clean(document), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def build_pump_status(root: Path) -> dict:
    """Build the frozen-snapshot products; returns the audit document."""
    root = Path(root).resolve()
    snapshot, discovery, histories = load_snapshot(root)
    snapshot_end = pd.Timestamp(snapshot["data_end_utc"])
    versions = versions_from_features(histories["features"])
    lor = _read_lor(root)
    nodes = pump_register(versions, lor)
    register = nodes[nodes["in_universe"]].drop(columns="in_universe").reset_index(drop=True)
    universe = set(register["osm_id"])
    segments = status_segments(versions[versions["osm_id"].isin(universe)], snapshot_end)
    changes = attach_successors(status_changes(segments, snapshot_end), segments, register)
    panel = season_panel(register["osm_id"], segments, changes)

    final = status_at(segments, snapshot_end - pd.Timedelta(seconds=1))
    register["status_at_snapshot_end"] = register["osm_id"].map(final["status"]).fillna("never_mapped_as_pump")
    register["deleted_at_snapshot_end"] = register["status_at_snapshot_end"].eq("deleted")
    tallies = changes.groupby(["osm_id", "change_type"]).size().unstack(fill_value=0)
    register["n_status_changes"] = register["osm_id"].map(changes.groupby("osm_id").size()).fillna(0).astype(int)
    for change_type in ("repair", "failure", "exit"):
        values = tallies[change_type] if change_type in tallies else pd.Series(dtype=int)
        register[f"n_{change_type}s"] = register["osm_id"].map(values).fillna(0).astype(int)
    exits = changes[changes["successor_osm_id"].notna()].groupby("osm_id")["successor_osm_id"].last()
    register["successor_osm_id"] = register["osm_id"].map(exits)

    tree_xy = load_street_trees(root)
    counts = trees_within(register[["x_25833", "y_25833"]].to_numpy(), tree_xy)
    register = pd.concat([register, counts], axis=1)
    feasibility = design_feasibility(panel, register, tree_xy)

    by_season = pumps_by_season_start(panel, segments, register)
    by_year = changes_by_year(changes)
    compared = comparison_2022(segments)
    replication = pd.DataFrame(platform_replication(versions, root, snapshot))
    universe_versions = versions[versions["osm_id"].isin(universe)]
    unrecognised = (universe_versions[universe_versions["status"].eq("unrecognised")]
                    .groupby(["status_source", "status_raw"]).agg(versions=("osm_id", "size"),
                                                                  nodes=("osm_id", "nunique")).reset_index())
    bad_checks = universe_versions[universe_versions["check_date_raw"].notna() & universe_versions["check_date"].isna()]

    processed = root / PROCESSED_DIR
    output = root / OUTPUT_DIR
    register_columns = ["osm_id", "ref", "official_ref", "plr_id", "bzr_id", "district", "lon", "lat",
                        "x_25833", "y_25833", "max_displacement_m", "first_mapped_utc", "selector_first_seen_utc",
                        "last_edit_utc", "n_versions", "ever_network_selector", "ever_description_selector",
                        "ever_name_variant", "status_at_snapshot_end", "deleted_at_snapshot_end",
                        "n_status_changes", "n_repairs", "n_failures", "n_exits", "successor_osm_id",
                        "street_trees_100m", "street_trees_200m"]
    register = _by_node(register[register_columns])
    _write_csv(register, processed / "pump_register_osm.csv")
    _write_csv(changes, processed / "pump_status_changes_osm.csv")
    _write_csv(panel, processed / "pump_season_panel_2019_2025.csv")
    _write_csv(by_season, output / "tables/pumps_by_season_start.csv")
    _write_csv(by_year, output / "tables/status_changes_by_year.csv")
    _write_csv(compared, output / "tables/comparison_2022.csv")
    _write_csv(feasibility, output / "tables/design_feasibility_by_season.csv")
    _write_csv(unrecognised, output / "tables/unrecognised_status_values.csv")
    _write_csv(replication, output / "tables/platform_layer_replication.csv")

    dated = changes[changes["change_type"].isin(["repair", "failure"])]
    in_seasons = dated[pd.to_datetime(dated["edit_date"]).dt.year.isin(SEASONS)
                       & pd.to_datetime(dated["edit_date"]).dt.month.between(4, 9)]
    deleted_exits = changes[changes["to_status"].eq("deleted")]
    inputs = {
        "snapshot": {"path": str(SNAPSHOT_DIR / "snapshot.json"),
                     "sha256": _sha256_file(root / SNAPSHOT_DIR / "snapshot.json"),
                     "data_end_utc": snapshot["data_end_utc"], "api_version": snapshot["api_version"]},
        "lor_boundaries": {"path": "data/spatial/lor_planungsraeume_2021.gpkg",
                           "sha256": _sha256_file(root / "data/spatial/lor_planungsraeume_2021.gpkg")},
        "tree_inventory": {"path": "data/Berlin_trees.gpkg",
                           "sha256": json.loads((root / "data/raw/tree_inventory/snapshot.json").read_text())[
                               "uncompressed_sha256"],
                           "crs_override": "Declared EPSG:4326 metadata overridden to EPSG:25833 after "
                                           "coordinate-range validation."},
    }
    audit = {
        "inputs": inputs,
        "selection": {
            "discovery_nodes": snapshot["requests"]["discovery"]["nodes"],
            "history_nodes": int(versions["osm_id"].nunique()),
            "history_versions": int(len(versions)),
            "ever_platform_selector": int((nodes["ever_network_selector"] | nodes["ever_description_selector"]).sum()),
            "ever_platform_selector_outside_berlin": int(((nodes["ever_network_selector"]
                                                           | nodes["ever_description_selector"])
                                                          & ~nodes["in_berlin"]).sum()),
            "universe_pumps": len(register),
            "universe_versions": int(len(universe_versions)),
            "water_wells_never_platform_selector": int((nodes["ever_water_well"] & ~nodes["ever_network_selector"]
                                                        & ~nodes["ever_description_selector"]).sum()),
            "name_variant_only": int((nodes["ever_name_variant"] & ~nodes["ever_network_selector"]
                                      & ~nodes["ever_description_selector"]).sum()),
        },
        "platform_layer_replication": _records(replication),
        "street_trees_in_inventory": int(len(tree_xy)),
        "pumps_by_season_start": _records(by_season),
        "changes": {
            "all": int(len(changes)),
            "by_type": changes["change_type"].value_counts().sort_index().to_dict(),
            "repairs_and_failures": int(len(dated)),
            "repairs_and_failures_check_date_backed_pct": round(100 * dated["check_date_backed"].mean(), 1)
            if len(dated) else None,
            "repairs_and_failures_check_date_backed_day_pct": round(100 * dated["check_date_backed_day"].mean(), 1)
            if len(dated) else None,
            "all_changes_check_date_backed_pct": round(100 * changes["check_date_backed"].mean(), 1),
            "median_check_date_lag_days_when_backed": float(changes.loc[changes["check_date_backed"],
                                                                        "check_date_lag_days"].median()),
            "repairs_and_failures_in_seasons_2019_2025": int(len(in_seasons)),
            "repairs_and_failures_reverted_within_14d": int(dated["reverted_within_14d"].sum()),
            "deletions": int(len(deleted_exits)),
            "deletions_with_successor_node": int(deleted_exits["successor_osm_id"].notna().sum()),
            "exits_later_restored_by_net_change": changes["net_change_if_restored"].value_counts()
            .sort_index().to_dict(),
        },
        "pumps_with_dated_repair_or_failure_by_season": {
            int(season): {"repair": int(frame["n_repair"].gt(0).sum()),
                          "failure": int(frame["n_failure"].gt(0).sum()),
                          "repair_or_failure": int(frame["repair_or_failure"].sum()),
                          "repair_or_failure_check_backed": int(frame["repair_or_failure_check_backed"].sum())}
            for season, frame in panel.groupby("season")},
        "comparison_2022": _records(compared),
        "data_quality": {
            "unrecognised_status_versions": int(unrecognised["versions"].sum()) if len(unrecognised) else 0,
            "unparseable_check_date_versions": int(len(bad_checks)),
            "unparseable_check_date_values": sorted(bad_checks["check_date_raw"].unique().tolist()),
            "pumps_moved_more_than_15m": int(register["max_displacement_m"].gt(15).sum()),
            "check_date_after_edit_changes": int(changes["check_date_lag_days"].lt(-1).sum()),
        },
        "design_feasibility": _records(feasibility),
    }
    metadata = _panel_metadata(snapshot, inputs, register, changes, panel)
    _write_json(metadata, processed / "pump_status_panel.metadata.json")
    _write_json(audit, output / "audit.json")
    (output / "report.md").write_text(render_report(audit, by_season, by_year, compared, feasibility,
                                                    replication), encoding="utf-8")
    return audit


def _panel_metadata(snapshot: dict, inputs: dict, register: pd.DataFrame, changes: pd.DataFrame,
                    panel: pd.DataFrame) -> dict:
    claim = ("Describes what OpenStreetMap recorded about street pumps and when it was edited. An OSM edit "
             "date is when a mapper recorded a status, not necessarily when the pump changed; edits may follow "
             "use. No watering outcome is joined or examined.")
    return {
        "schema_version": 1,
        "dataset_id": "pump_status_panel_osm",
        "protocol": "docs/pump_status_protocol.md",
        "source": {"snapshot_data_end_utc": snapshot["data_end_utc"], "licence": snapshot["licence"]},
        "inputs": inputs,
        "tables": {
            "pump_register_osm.csv": {
                "grain": "osm_node (one row per pump in the platform universe)", "rows": int(len(register)),
                "period": f"{HISTORY_START[:10]} to {snapshot['data_end_utc'][:10]}",
                "universe": "Nodes in Berlin that carried network or description = 'Berliner Straßenbrunnen' in "
                            "at least one version (the platform selector, before and after May 2021).",
                "denominator": "street_trees_* count catalogued street trees in the current frozen inventory "
                               "within the radius (Euclidean, inclusive) of the pump's last mapped position.",
                "zero_semantics": "Zero trees means no catalogued street tree within the radius; trees removed "
                                  "before the inventory snapshot are absent.",
                "claim_limit": claim},
            "pump_status_changes_osm.csv": {
                "grain": "status_transition (consecutive versions of one node with different harmonised status)",
                "rows": int(len(changes)),
                "period": f"edits up to {snapshot['data_end_utc']}",
                "dates": "change_time_utc is the edit instant; edit_date its Europe/Berlin date; event_date is "
                         "check_date when the change is check_date-backed at day precision, else edit_date.",
                "zero_semantics": "A missing row means OSM recorded no change, not that the pump did not change.",
                "denominator": "None; counts of recorded transitions.",
                "claim_limit": claim},
            "pump_season_panel_2019_2025.csv": {
                "grain": "pump x April-September season (balanced over the universe; not-yet-mapped and "
                         "deleted states are explicit statuses)",
                "rows": int(len(panel)), "period": "2019-2025 seasons, 1 April 00:00 to 1 October 00:00 "
                                                   "Europe/Berlin",
                "timing": "Status at start/end and in-season changes use OSM edit instants, so the start status "
                          "and the change counts are mutually consistent; check_date dates are in the changes "
                          "table.",
                "zero_semantics": "n_* = 0 means no recorded change of that type in the season.",
                "denominator": "Pumps in the universe; usable_at_start is missing when the status is unknown, "
                               "not mapped or deleted.",
                "claim_limit": claim},
        },
        "status_vocabulary": {"usable": USABLE, "change_types": list(CHANGE_TYPES),
                              "platform_selector_switch": str(NETWORK_SELECTOR_FROM.date())},
    }


def _markdown_table(frame: pd.DataFrame) -> str:
    frame = _format(frame).astype(object).where(frame.notna(), "")
    header = "| " + " | ".join(str(c) for c in frame.columns) + " |"
    rule = "| " + " | ".join("---" for _ in frame.columns) + " |"
    body = ["| " + " | ".join(str(v) for v in row) + " |" for row in frame.itertuples(index=False)]
    return "\n".join([header, rule, *body])


def render_report(audit: dict, by_season: pd.DataFrame, by_year: pd.DataFrame,
                  compared: pd.DataFrame, feasibility: pd.DataFrame, replication: pd.DataFrame) -> str:
    selection, changes = audit["selection"], audit["changes"]
    restored_net = ", ".join(f"{kind} {count}" for kind, count in
                             changes["exits_later_restored_by_net_change"].items())
    season_view = by_season[["season", "mapped_as_water_well", "platform_visible", "working", "broken", "locked",
                             "pump_absent", "unknown", "removed", "disused", "deleted", "not_mapped",
                             "water_wells_with_known_status_pct", "working_pct_of_known",
                             "median_days_since_check"]]
    dated = by_year[by_year["change_type"].isin(["repair", "failure"])].pivot_table(
        index="year", columns="change_type", values=["changes", "check_date_backed"], aggfunc="sum",
        fill_value=0)
    dated.columns = [f"{kind}_{measure}" for measure, kind in dated.columns]
    dated = dated.reset_index()
    view_2022 = compared[["source", "date", "pumps", "working", "not_working", "status_unknown",
                          "working_pct_of_pumps", "working_pct_of_known_status"]]
    lines = [
        "# Street-pump status panel: audit summary",
        "",
        "Treatment side of the RQ2 pump design only ([protocol](../../docs/pump_status_protocol.md)). "
        "No watering outcome is joined, tabulated or examined here.",
        "",
        f"- **Snapshot.** OpenStreetMap full history via the ohsome API, data to "
        f"{audit['inputs']['snapshot']['data_end_utc']}; {selection['history_nodes']:,} candidate nodes, "
        f"{selection['history_versions']:,} versions.",
        f"- **Universe.** {selection['universe_pumps']:,} Berlin nodes carried the platform selector "
        f"(`network` or, before May 2021, `description` = `Berliner Straßenbrunnen`) in at least one version. "
        f"{selection['water_wells_never_platform_selector']:,} other water wells never did and are excluded.",
        f"- **Changes.** {changes['all']:,} recorded status transitions, of which "
        f"{changes['repairs_and_failures']:,} are repairs or failures; "
        f"{changes['repairs_and_failures_check_date_backed_pct']}% of these are backed by a `check_date` set "
        f"within a day of the edit ({changes['repairs_and_failures_check_date_backed_day_pct']}% at day "
        f"precision). {changes['repairs_and_failures_reverted_within_14d']:,} were reverted within 14 days.",
        f"- **Deletions.** {changes['deletions']:,} pump nodes were deleted; "
        f"{changes['deletions_with_successor_node']:,} have another pump node within 15 m (remapping rather "
        f"than removal). {sum(changes['exits_later_restored_by_net_change'].values()):,} exits were later "
        f"restored on the same node; `net_change_if_restored` gives the net transition across the gap "
        f"({restored_net}).",
        "",
        "## Check against the platform's published pump layer",
        "",
        "The platform's harvester published its pump layer weekly. At each frozen layer's commit instant, the "
        "snapshot's selection reproduces these pumps, labels and check dates:",
        "",
        _markdown_table(replication),
        "",
        "## Pumps at season start (1 April)",
        "",
        _markdown_table(season_view),
        "",
        "Mapping coverage grew quickly before 2021, so early seasons mix real status with missing mapping: "
        "`not_mapped` pumps were added to OSM later, and `unknown` pumps carried no status tag.",
        "",
        "## Repairs and failures by edit year",
        "",
        _markdown_table(dated),
        "",
        "## Comparison with the reported 2022 status",
        "",
        _markdown_table(view_2022),
        "",
        "## Design feasibility (counts only)",
        "",
        "Distinct catalogued street trees within 100 m and 200 m of pumps with a dated repair or failure in the "
        "season, and of comparison pumps whose known status did not change. Comparison trees exclude trees near "
        "a treated pump.",
        "",
        _markdown_table(feasibility),
        "",
        "## Claim limits",
        "",
        "- An edit date records when a mapper reported a status, not when a pump broke or was repaired. Status "
        "edits may follow use, including by platform users; check_date-backed and district repair dates are "
        "preferred for registration.",
        "- `unknown` is missing information, not a working pump. Early seasons have low status coverage.",
        "- Tree counts use the current inventory and straight-line distance; they are feasibility counts, not "
        "exposure measures.",
        "",
    ]
    return "\n".join(lines)
