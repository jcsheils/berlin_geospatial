# Berlin recorded-care atlas — Earth Engine demo

## Launch

1. Open https://code.earthengine.google.com/ in an Earth Engine enabled account with a configured Cloud project.
2. Create a new script. Copy the **entire contents** of `berlin_atlas_demo.js` into it, then press **Run**.
3. Start with July 2025, monthly events per 1,000 inventory trees. Click a neighbourhood to open its monthly history.
4. Compare July in 2021–2025 using the same fixed colour classes. Switch to pooled reach or social status for static context.
5. Select Landsat monthly surface temperature, then valid scene count to inspect the coverage supporting it.
6. Use the separate RQ1 year selector for citywide daily events and maximum station air temperature.

The generated script embeds aggregated project data and simplified boundaries (~1 MB). No project-data upload or asset-ID configuration is needed. Satellite tiles are computed online. The script has been syntax checked and its source totals verified locally; authenticated Earth Engine execution and UI rendering remain to be checked. It has not been published as an Earth Engine App.

## What is included

- 542 LOR planning areas, May 2020–December 2025, 68 monthly observations per area.
- Canonical linked all-tree monthly totals: 57,786 events and 2,249,502 recorded litres.
- Monthly events, litres and events per 1,000 current inventory trees; pooled distinct-tree reach.
- Static MSS end-2024 social status; thermal burden and green provision in the inspector.
- RQ1 daily citywide April–September observations, with 2020 starting on 18 May. These are a different seasonal sample from the all-month map.
- Live Landsat 8/9 Collection 2 Level 2 monthly clear-sky median surface temperature and valid scene count.

## Interpretation and limitations

This is an exploratory atlas, not an allocation tool. Platform logs do not represent all irrigation. Current inventory is not historical stock; rates include all linked tree types. Zeros assume platform availability. May 2020 is partial. Social/environmental layers use later static reference periods, not contemporaneous monthly vulnerability. Pooled reach does not change with the month selector. No RQ1 neighbourhood slopes, causal cooling effects, validated need rankings, or RQ4 allocations are displayed.

Landsat uses L2SP scenes; QA_PIXEL bits 0–5 (fill, dilated cloud, cirrus, cloud, shadow, snow) and nonzero QA_RADSAT are excluded. ST_B10 is scaled by 0.00341802, offset by 149 K, then converted to Celsius. Values are monthly per-pixel medians of retained scenes, not daily averages. Valid counts are scene counts, not necessarily independent overpass dates. Missing emissivity and clouds cause gaps; clear-sky sampling is selective. LST is distinct from the DWD air temperature in the RQ1 charts. The two-axis daily chart is descriptive and axis scaling can exaggerate apparent agreement.

Display geometry is simplified by 20 m in EPSG:25833 and converted to EPSG:4326. This may affect boundary clicks and produces approximate display edges; analytical assignments and source data are unchanged. The implementation is deliberately compact for a meeting demo. A deployed version should move aggregates and full boundaries to managed EE assets and complete live performance/access checks.

## Rebuild

From repository root:

```sh
.venv/bin/python earth_engine/build_demo.py
```

Edit `atlas_ui.js`, then rebuild. The builder checks unique area-month keys, coverage, matching area IDs and canonical totals. Existing dependencies: pandas and geopandas. Inputs are the equity GeoPackage, canonical monthly panel and RQ1 daily baseline CSV. Do not edit the generated data block by hand.

## Meeting walkthrough

“Here is where citizen watering was recorded. The same scale allows comparison across months. Clicking an area reveals whether activity was persistent or episodic. Social and environmental context help frame inequality questions, while satellite temperature supplies a separate environmental view. The RQ1 chart shows temporal patterns motivating the statistical models; this atlas does not estimate those effects.”

## Attribution and API references

- LOR: Amt für Statistik Berlin-Brandenburg / Lebensweltlich orientierte Räume (01.01.2021), CC BY 3.0 DE; geometry simplified for display. See `data/spatial/README.md` for original source URLs and context metadata.
- Watering: Giess den Kiez project snapshot, linked using repository pipelines. See `data/README.md` for source limitations and licences.
- Satellite: USGS Landsat 8/9, public-domain products.
- https://developers.google.com/earth-engine/datasets/catalog/LANDSAT_LC08_C02_T1_L2
- https://developers.google.com/earth-engine/guides/ui_widgets

Before live acceptance, check startup, all seven map modes, a zero-activity area, outside-boundary clicks, rapid repeated clicks, month changes and both RQ1 year endpoints. Check a low-coverage winter month against the scene-count layer. Share via your Earth Engine account only after checking the intended data audience.
