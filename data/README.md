# Data available for examination

The package includes all existing analysis input datasets and saved tabular/geospatial products, with the large tree inventory stored as a lossless compressed snapshot. It does **not** claim to include inputs that the October proposal only plans to obtain. The [file inventory](../examination/data_inventory.csv) provides paths, sizes, hashes, row counts, and provenance classifications; [schemas](../examination/data_schema.json) and the [dictionary](../examination/data_dictionary.md) describe the tables.

| Input | Coverage and purpose | Provenance and reuse |
| --- | --- | --- |
| `giessdenkiez_bewässerungsdaten (1).csv` | 58,847 raw records, May 2020–April 2026; analyses generally stop at December 2025 | CityLAB / Technologiestiftung Berlin, [Gieß den Kiez Nutzungsdaten](https://daten.berlin.de/datensaetze/gdk-nutzungsdaten); CC0 as recorded in project manifest |
| `raw/tree_inventory/Berlin_trees.gpkg.gz` | Exact 962,545-row inventory input; restore with the supplied command | [Source, licence, hashes, and CRS correction](raw/tree_inventory/README.md); original acquisition procedure unknown |
| `spatial/lor_planungsraeume_2021.gpkg` | 542 planning-area polygons, fixed 2021 geography | Amt für Statistik Berlin-Brandenburg; CC BY 3.0 DE; [attribution and service](spatial/README.md) |
| `spatial/lor_equity_environment_2024.gpkg` | MSS 2025 and Environmental Justice Atlas 2023/24, three layers | Berlin official spatial services; DL-DE Zero 2.0; [source details](spatial/README.md) |
| `spatial/alkis_ortsteile_2026_09_29.geojson` | 97 current Ortsteile for the provisional LST extension | Official Berlin ALKIS WFS; DL-DE Zero 2.0; [boundary caveats](spatial/README.md) |
| `raw/dwd/*.zip` | Frozen Berlin-Tempelhof station archive; extracted daily weather for 2020–2025 | Deutscher Wetterdienst CDC; CC BY 4.0; [source and quality notes](raw/dwd/README.md) |
| `raw/supervisor/*.csv` | Monthly Ortsteil LST/rainfall, 2018–2025; 9,312 source rows | Supervisor-supplied; extraction metadata and explicit redistribution licence were not supplied; [audit](raw/supervisor/README.md) |
| `Berlin_heat_population_data.csv` and `Berlin_heat_population_death_Birth_data.csv` | Legacy district heat/population/mortality aggregates used in initial exploration | Original assembly method and complete source/licence chain unverified; retain as preliminary legacy inputs, not a validated daily climate or health dataset |

## Analysis products

- `processed/foundation/`: balanced 542-area × 68-month panel and recorded-tree/LOR crosswalk.
- `processed/temporal/`: 50,259 positive tree-days plus monthly, annual, seasonal, age and genus summaries.
- `../output/exploratory/`: original source audits and district/tree summaries.
- `../output/spatial/`: LOR metrics, spatial-join audit, Moran results and enriched polygons.
- `../output/equity/`: social/environmental joins, associations, screening candidates and enriched polygons.
- `../output/03_spatial_equity_vulnerability/`: descriptive temporal atlas and duplicate presentation tables; the folder name reflects the August design.
- `../output/watering_response/`: monthly station-weather associations and the separately qualified Ortsteil-LST extension.

Derived files inherit source-specific attribution and any unresolved source restrictions. No blanket open-data licence is assigned to all contents. Source licence statements above are metadata, not a legal assessment; the supplied and legacy data require provenance clarification before downstream redistribution under an open licence.

## Planned inputs are not included

The valid-overpass Landsat/Sentinel panel, vegetation-height fractions, built-form controls, temporal drought series, area-level age composition, turnout crosswalk, heat-warning/calendar controls, and historical young-tree risk set remain to be assembled. Optional user IDs and district watering schedules have not been supplied. The positive tree-day table is not the complete daily behavioural panel proposed for Part II.
