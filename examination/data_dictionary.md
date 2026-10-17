# Data definitions and analytical units

The [schema inventory](data_schema.json) lists every field in the included CSV and GeoPackage tables. The [file inventory](data_inventory.csv) records hashes, sizes, row counts, and access status. This guide defines the main analytical quantities; consult each builder for less common diagnostics.

| Field or quantity | Definition and unit | Caution |
| --- | --- | --- |
| `id`, `tree_id`, `pitid` | Tree/planting-location identifiers used to link logs to the inventory | Not volunteer IDs; read as text |
| `plr_id`, `bzr_id` | LOR Planungsraum and Bezirksregion identifiers | Preserve leading zeros; fixed 2021 geography |
| `timestamp` | Source event timestamp, parsed as UTC | Convert to Europe/Berlin for local dates; midnight rounding affects 2024–2025 |
| `local_date` | Berlin local calendar date | A logged date is not necessarily a measured irrigation time |
| `month`, `month_date` | Calendar month key | May 2020 is partial; January–April 2020 are unavailable |
| `recorded_watering_events` | Count of deduplicated linked platform event rows | Repeat events on a tree remain events |
| `recorded_litres` | Sum of reported positive watering volumes, litres | Self-reported; not measured soil uptake |
| `recorded_watered_trees` | Distinct linked tree IDs within the stated area and period | Monthly distinct counts cannot be summed to obtain annual distinct trees |
| `current_inventory_trees` | Distinct currently inventoried tree IDs assigned to an area | Not a historical eligible-tree denominator |
| `watering_reach_pct` | 100 × distinct recorded-watered trees / current inventory trees | Applies to the plate's entire stated window |
| Events per 1,000 current inventory trees | 1,000 × event count / current inventory count | Repeated events mean this is an intensity, not coverage |
| Litres per inventory tree | Total logged litres / current inventory count | Zero logs do not establish zero total watering |
| `plr_area_ha` | Polygon area in hectares using EPSG:25833 | Geometry support may differ from source indicator geometry |
| `age_at_watering` | Local event year minus planting year | Missing or implausible ages are unknown, not zero |
| MSS status | Four-class end-2024 social status from MSS 2025 | Area context, not the circumstances of individual volunteers or a historical annual series |
| Burden count | Environmental Justice Atlas environmental and social burden count | Composite context, not a direct physiological need measure |
| `air_temperature_mean_c`, `air_temperature_max_c` | DWD Berlin-Tempelhof air temperature, degrees Celsius | Shared station context, not neighbourhood or surface temperature |
| `rainfall_mm` | DWD daily/monthly precipitation, millimetres | -999 source sentinel becomes missing; monthly summaries require complete daily coverage |
| `LST_C_mean`, `lst_c` | Supplied monthly Ortsteil mean surface temperature, degrees Celsius | Processing and boundary metadata unverified |
| `LST_C_count` | Source count accompanying monthly LST | Meaning unknown; do not label as image/scene count |
| `comparison_eligible` | Area is retained in the provisional LST comparison | Does not establish validated geography |
| Moran's I / local cluster | Spatial dependence under row-standardised queen contiguity | 999 permutations; local p < .05 is unadjusted and exploratory |

CSV empty cells and `NaN` represent unavailable values unless a source documents otherwise. Recorded zeros in balanced panels represent no linked platform event during an observed period. They do not represent unobserved months, missing temperatures, or absence of all irrigation.
