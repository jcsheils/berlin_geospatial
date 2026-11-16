# Spatial data

## LOR Planungsräume 2021

- **File:** `lor_planungsraeume_2021.gpkg`, layer `a_lor_plr_2021`
- **Features:** 542 Planungsräume; EPSG:25833; reference date 1 January 2021
- **Provider:** Amt für Statistik Berlin-Brandenburg
- **Source:** https://daten.berlin.de/datensaetze/lebensweltlich-orientierte-raume-lor-01-01-2021-wfs-34c86848
- **WFS:** https://gdi.berlin.de/services/wfs/lor_2021 (feature type `lor_2021:a_lor_plr_2021`)
- **Licence:** CC BY 3.0 DE. Attribution: Amt für Statistik Berlin-Brandenburg / Lebensweltlich orientierte Räume (LOR) (01.01.2021)
- **Downloaded:** 12 June 2026

## LOR equity and environmental-justice indicators

- **File:** `lor_equity_environment_2024.gpkg`, layers `mss2025_indizes_542`, `mss2025_indexind_542` and `environmental_justice_2023_2024`
- **Features:** 542 Planungsräume per layer; EPSG:25833
- **Reference periods:** MSS 31 December 2024; environmental justice 2023/24
- **Sources:** [MSS 2025](https://daten.berlin.de/datensaetze/monitoring-soziale-stadtentwicklung-mss-2025-wfs-67692212) and [Umweltgerechtigkeit 2023/2024](https://daten.berlin.de/datensaetze/umweltgerechtigkeit-2023-2024-umweltatlas-wfs-2d02ba21)
- **WFS:** https://gdi.berlin.de/services/wfs/mss_2025 and https://gdi.berlin.de/services/wfs/ua_umweltgerechtigkeit2023
- **Licence:** Datenlizenz Deutschland – Zero – Version 2.0
- **Downloaded:** 12 June 2026

The environmental-justice layer shares the 2021 LOR layer's 542 `plr_id` values and names, but some polygon areas differ by up to about 4.6%. The analysis joins its attributes by `plr_id` and keeps the 2021 geometry.

Rebuild with `python analysis/download_equity_data.py`. That fetches the current service state, so skip it when reproducing the frozen release.

## ALKIS Ortsteile

- **File:** `alkis_ortsteile_2026_09_29.geojson`
- **Features:** 97 named Ortsteile; EPSG:25833
- **Retrieved:** 29 September 2026
- **Catalogue:** https://daten.berlin.de/datensaetze/alkis-berlin-ortsteile-wfs-61bd3084
- **WFS:** https://gdi.berlin.de/services/wfs/alkis_ortsteile (feature type `alkis_ortsteile:ortsteile`)
- **Licence:** Datenlizenz Deutschland – Zero – Version 2.0

The provisional Ortsteil analysis uses this current-boundary extract to assign tree IDs and compute polygon areas from projected geometry (not the source `gdf` attribute). Nobody has confirmed that these are the boundaries behind the supplied LST file. The district documents [Schlachtensee's creation](https://www.berlin.de/ba-steglitz-zehlendorf/aktuelles/pressemitteilungen/2020/pressemitteilung.1024262.php) from Nikolassee and Zehlendorf. `output/watering_response/ortsteil/metadata.json` stores the WFS query and input hash.
