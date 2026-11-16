# Data

This folder holds every input the analyses use and the shared processed panels. The large tree inventory ships as a lossless compressed snapshot. Inputs the proposal only plans to obtain are not here. For paths, sizes, hashes and row counts see the [file inventory](../examination/data_inventory.csv); for fields see the [schemas](../examination/data_schema.json) and [dictionary](../examination/data_dictionary.md).

## Inputs

| File | Coverage and use | Provenance and licence |
| --- | --- | --- |
| `giessdenkiez_bewässerungsdaten (1).csv` | 58,847 watering logs, May 2020–April 2026; analyses stop at December 2025 | CityLAB / Technologiestiftung Berlin, [Gieß den Kiez Nutzungsdaten](https://daten.berlin.de/datensaetze/gdk-nutzungsdaten); CC0 per the project manifest |
| `raw/tree_inventory/Berlin_trees.gpkg.gz` | The exact 962,545-row tree inventory; restore with `python tools/restore_tree_inventory.py` | [Source, licence, hashes and CRS fix](raw/tree_inventory/README.md); original acquisition procedure unknown |
| `raw/tree_inventory/trees_2025_gbif.csv.gz` | 927,914 trees from the 2025 inventory, one row each with identifier, district, genus, planting year and position; used only to check which identifiers persist into 2026 | Third-party archive of the official cadastre on GBIF; CC0; [source, hashes and limits](raw/tree_inventory/README.md) |
| `spatial/lor_planungsraeume_2021.gpkg` | 542 planning-area polygons, 2021 geography | Amt für Statistik Berlin-Brandenburg; CC BY 3.0 DE; [details](spatial/README.md) |
| `spatial/lor_equity_environment_2024.gpkg` | MSS 2025 and Environmental Justice Atlas 2023/24, three layers | Berlin spatial services; DL-DE Zero 2.0; [details](spatial/README.md) |
| `spatial/alkis_ortsteile_2026_09_29.geojson` | 97 current Ortsteile for the provisional LST extension | Berlin ALKIS WFS; DL-DE Zero 2.0; [boundary caveats](spatial/README.md) |
| `raw/dwd/*.zip` | Berlin-Tempelhof station archive; daily weather for 2020–2025 | Deutscher Wetterdienst CDC; CC BY 4.0; [notes](raw/dwd/README.md) |
| `raw/supervisor/*.csv` | Monthly Ortsteil LST and rainfall, 2018–2025; 9,312 rows | Supplied to the project without extraction metadata or a redistribution licence; [audit](raw/supervisor/README.md) |
| `Berlin_heat_population_data.csv`, `Berlin_heat_population_death_Birth_data.csv` | Legacy district heat, population and mortality aggregates from the first exploration | Assembly method and licence chain unverified; not a validated climate or health dataset |

## Processed products

- `processed/foundation/`: balanced 542-area × 68-month panel and the tree-to-LOR crosswalk.
- `processed/temporal/`: 50,259 positive tree-days plus monthly, annual, seasonal, age and genus summaries.
- `processed/rq1/`: the April–September planning-area-day panel for the RQ1 pilot.

Analysis outputs live in `../output/`: source audits (`exploratory/`), LOR metrics and Moran results (`spatial/`), social and environmental joins (`equity/`), the temporal atlas (`03_spatial_equity_vulnerability/`, an older folder name), the monthly weather report (`watering_response/`) and the RQ1 pilot (`rq1_daily/`).

## Licences

Derived files inherit the attribution and restrictions of their sources; no blanket licence covers the folder. The licence notes above are metadata, not legal advice. The supplied LST file and legacy aggregates need provenance clarification before anyone redistributes them under an open licence.

## Not yet available

Still to assemble: the valid-overpass Landsat and Sentinel panel, vegetation-height fractions, built-form controls, drought series, area age composition, the turnout crosswalk, heat-warning and holiday calendars, and the historical young-tree risk set. Inventories before 2025 have not been obtained. User IDs and district watering schedules have not been supplied. The positive tree-day table is not the full daily panel.
