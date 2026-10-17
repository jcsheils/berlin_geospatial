# Spatial data

## Current official Berlin Ortsteile

- File: `alkis_ortsteile_2026_09_29.geojson`
- Features: 97 named Ortsteile; CRS: EPSG:25833
- Retrieved: 29 September 2026
- Catalogue: https://daten.berlin.de/datensaetze/alkis-berlin-ortsteile-wfs-61bd3084
- WFS: https://gdi.berlin.de/services/wfs/alkis_ortsteile
- Feature type: `alkis_ortsteile:ortsteile`
- Licence: Datenlizenz Deutschland – Zero – Version 2.0

This frozen current-boundary extract spatially assigns recorded tree IDs and
supplies polygon areas in the provisional Ortsteil analysis. Area denominators
are computed from projected polygon geometry, not the source `gdf` attribute.
These polygons have not been established as the boundaries used in the
supervisor's LST extraction. Schlachtensee's creation from Nikolassee and
Zehlendorf is documented by the district:
https://www.berlin.de/ba-steglitz-zehlendorf/aktuelles/pressemitteilungen/2020/pressemitteilung.1024262.php

The full WFS query and input hash are saved in
`output/watering_response/ortsteil/metadata.json`.

## Berlin LOR Planungsräume 2021

- File: `lor_planungsraeume_2021.gpkg`
- Layer: `a_lor_plr_2021`
- Features: 542 Planungsräume
- CRS: EPSG:25833
- Reference date: 1 January 2021
- Provider: Amt für Statistik Berlin-Brandenburg
- Source: https://daten.berlin.de/datensaetze/lebensweltlich-orientierte-raume-lor-01-01-2021-wfs-34c86848
- WFS: https://gdi.berlin.de/services/wfs/lor_2021
- License: CC BY 3.0 DE
- Attribution: Amt für Statistik Berlin-Brandenburg / Lebensweltlich
  orientierte Räume (LOR) (01.01.2021)

The file was downloaded from the official WFS on 12 June 2026 using the
`lor_2021:a_lor_plr_2021` feature type and EPSG:25833.

## LOR equity and environmental-justice indicators

- File: `lor_equity_environment_2024.gpkg`
- Layers:
  - `mss2025_indizes_542`
  - `mss2025_indexind_542`
  - `environmental_justice_2023_2024`
- Features: 542 Planungsräume per layer
- CRS: EPSG:25833
- MSS reference date: 31 December 2024
- Environmental-justice reference period: 2023/24
- MSS source: https://daten.berlin.de/datensaetze/monitoring-soziale-stadtentwicklung-mss-2025-wfs-67692212
- Environmental-justice source: https://daten.berlin.de/datensaetze/umweltgerechtigkeit-2023-2024-umweltatlas-wfs-2d02ba21
- WFS:
  - https://gdi.berlin.de/services/wfs/mss_2025
  - https://gdi.berlin.de/services/wfs/ua_umweltgerechtigkeit2023
- License: Datenlizenz Deutschland - Zero - Version 2.0

The file was downloaded from the official WFS services on 12 June 2026.
The Environmental Justice layer uses the same 542 `plr_id` values and names as
the 2021 LOR layer, but localized polygon areas differ by up to about 4.6%.
The analysis therefore joins its attributes by `plr_id` and retains the 2021
watering-analysis geometry.

Rebuild it with:

```bash
python analysis/download_equity_data.py
```
