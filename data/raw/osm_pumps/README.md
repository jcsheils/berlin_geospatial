# Frozen OpenStreetMap street-pump history

This folder holds the full OpenStreetMap edit history of Berlin's street pumps (*Berliner Straßenbrunnen*). It was retrieved through the [ohsome API](https://api.ohsome.org/v1) on 15 November 2026, with data up to the API's latest replicated state, 27 July 2026 09:00 UTC. It is the only source of the RQ2 pump status panel built by `pipelines/09_build_pump_status_panel.py`. The status and dating rules are in the [protocol](../../../docs/pump_status_protocol.md).

| File | Content |
| --- | --- |
| `ohsome_discovery_full_history.geojson.gz` | Request 1, within the Berlin query polygon: every version of nodes matching the discovery filter (water wells, water wells under a lifecycle prefix, the platform selector tags, pump status tags). 2,331 nodes, 15,449 versions. |
| `ohsome_node_histories_part01–05.geojson.gz` | Request 2: every version of the same 2,331 nodes, requested by id in chunks of 500. This includes versions that no longer match the tag filter (tags removed, feature retagged). 15,602 versions. |
| `query_boundary_epsg4326.geojson` | Query polygon: the union of the 542 LOR 2021 planning areas, buffered by 100 m and simplified to 10 m in EPSG:25833, then converted to EPSG:4326. |
| `platform_pumps_2021-05-02_9eb7bee.geojson.gz`, `platform_pumps_2023-04-02_b7471fc.geojson.gz` | Pump layers published by the platform's harvester, one per selector era, used only for validation. |
| `snapshot.json` | Request parameters, API version, data end, and the sizes and SHA-256 of every archive before and after decompression. |

Each archive holds the exact response bytes, compressed with gzip level 9, mtime 0 and no file name. `load_snapshot` verifies every checksum, and checks that each history part was requested for the matching slice of the discovery node list.

## Platform selection

- **Source code.** The selection comes from [technologiestiftung/giessdenkiez-de-osm-pumpen-harvester](https://github.com/technologiestiftung/giessdenkiez-de-osm-pumpen-harvester) (`harvester/fetch.py` and `harvester/utils.py`). This builds the platform's pump layer weekly from the Overpass API.
- **Selector.** The harvester queries `node["man_made"="water_well"]["network"="Berliner Straßenbrunnen"]` inside `ISO3166-2=DE-BE`. That has applied since commit `c938dcb` (10 May 2021). Before it, the harvester matched `description="Berliner Straßenbrunnen"`.
- **Status shown.** The platform shows `pump:status` as follows:
  - `ok` becomes *funktionsfähig*;
  - `broken`, `missing_beam` and `out_of_order` become *defekt*;
  - `locked` and `blocked` become *verriegelt*;
  - a missing tag becomes *unbekannt*;
  - any other value is shown unchanged.
  `check_date` is shown as recorded.
- **Validation.** At each layer's commit instant, the snapshot reproduces both frozen platform layers exactly, with the same pumps, status labels and check dates. That is 1,862 pumps on 2 May 2021 (`description` era) and 1,940 on 2 April 2023 (`network` era, the harvester's last published layer).

## Licence and attribution

© OpenStreetMap contributors. The data are available under the [Open Database License 1.0](https://opendatacommons.org/licenses/odbl/1-0/). The derived tables in `data/processed/rq2_pumps/` are derived databases under the same licence. The ohsome API is provided by HeiGIT. The harvester's pump layers are derived from OpenStreetMap.

## Limitations

- **Mapping, not maintenance.** Pumps appear in the data when someone maps them. On 1 April, 1,109 pumps were mapped as water wells in 2019 and 1,946 in 2025.
- **Edit dates.** A status edit dates the report, not the breakdown or repair. Edits may follow use: platform users also edit pump status, and three free-text values cite the platform.
- **History start.** The OSHDB starts on 8 October 2007. OpenStreetMap's 2012 licence redaction removed some early versions.
- **Deletions.** A node deleted in OpenStreetMap is absent from the response. Its history shows a gap and then ends, or resumes when the node is restored.

## Rebuild or reacquire

Rebuild from these files; do not refresh them to reproduce results.

```bash
python pipelines/09_build_pump_status_panel.py
```

A new acquisition gives different outputs, because OpenStreetMap keeps changing. Move this folder aside first, since `--download` refuses to replace an existing `snapshot.json`:

```bash
python pipelines/09_build_pump_status_panel.py --download
```
