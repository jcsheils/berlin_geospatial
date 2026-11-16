# Earth Engine atlas of recorded watering

## Launch

1. Open https://code.earthengine.google.com/ with an Earth Engine account and a Cloud project.
2. Create a script, paste the **whole** of `berlin_atlas_demo.js` into it and press **Run**.
3. Start with July 2025, monthly events per 1,000 inventory trees. Click a planning area to see its monthly history.
4. Compare July across 2021–2025 on the fixed colour classes, or switch to pooled reach or social status.
5. Select Landsat monthly surface temperature, then valid scene count to see the coverage behind it.
6. Use the RQ1 year selector for citywide daily events against maximum station air temperature.

The script embeds aggregated project data and simplified boundaries (about 1 MB), so you upload nothing and configure no asset IDs. Earth Engine computes satellite tiles online. The script passes a syntax check and its totals match the source locally, but nobody has yet run it in an authenticated session, checked the rendered UI or published it as an Earth Engine App.

## Contents

- 542 LOR planning areas, May 2020–December 2025, 68 months each.
- Canonical linked monthly totals for all tree types: 57,786 events and 2,249,502 litres.
- Monthly events, litres and events per 1,000 current inventory trees; pooled distinct-tree reach.
- MSS end-2024 social status, with thermal burden and green provision in the inspector.
- RQ1 daily citywide April–September series, from 18 May in 2020. This sample differs from the all-month map.
- Live Landsat 8/9 Collection 2 Level 2 monthly clear-sky median surface temperature and valid scene count.

## Limits

The atlas explores the data; it is not an allocation tool.

- **Logs:** platform logs are not all irrigation, and zeros assume the platform was available. May 2020 is partial.
- **Denominators and context:** rates use the current inventory of all linked tree types, not historical stock. Social and environmental layers are static, from later reference periods. Pooled reach ignores the month selector.
- **Not shown:** RQ1 neighbourhood slopes, causal cooling, validated need rankings and RQ4 allocations.

**Landsat processing.** The script uses L2SP scenes and masks QA_PIXEL bits 0–5 (fill, dilated cloud, cirrus, cloud, shadow, snow) and nonzero QA_RADSAT. ST_B10 is scaled by 0.00341802, offset by 149 K and converted to °C. Values are monthly per-pixel medians of retained scenes. Valid counts count scenes, not necessarily independent overpass dates. Missing emissivity and clouds leave gaps, and clear-sky sampling is selective. Surface temperature differs from the DWD air temperature in the RQ1 chart, and the chart's two axes can exaggerate apparent agreement.

**Geometry.** Display boundaries are simplified by 20 m in EPSG:25833 and converted to EPSG:4326, so clicks near edges are approximate. Analytical assignments are unchanged. A deployed version should move aggregates and full boundaries to managed Earth Engine assets and pass performance and access checks.

## Rebuild

```sh
.venv/bin/python earth_engine/build_demo.py
```

Edit `atlas_ui.js`, then rebuild; never edit the generated data block by hand. The builder checks unique area-month keys, coverage, area IDs and canonical totals. It needs pandas and geopandas and reads the equity GeoPackage, the monthly panel and the RQ1 daily baseline CSV.

Before sharing, test startup, all seven map modes, an area with no activity, clicks outside the boundary, rapid repeated clicks, month changes and both RQ1 year endpoints, and compare a low-coverage winter month with the scene-count layer. Share through your Earth Engine account only with the intended audience.

## Attribution

- **LOR:** Amt für Statistik Berlin-Brandenburg / Lebensweltlich orientierte Räume (01.01.2021), CC BY 3.0 DE; geometry simplified for display. Sources in `data/spatial/README.md`.
- **Watering:** Gieß den Kiez snapshot, linked by the repository pipelines. Licences and limits in `data/README.md`.
- **Satellite:** USGS Landsat 8/9, public domain. Catalogue: https://developers.google.com/earth-engine/datasets/catalog/LANDSAT_LC08_C02_T1_L2; UI widgets: https://developers.google.com/earth-engine/guides/ui_widgets
