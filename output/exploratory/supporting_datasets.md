# Supporting Dataset Inventory

Reviewed on 12 June 2026. These datasets have not yet been downloaded into the
workspace. The order below reflects analytical value for the thesis rather than
portal prominence.

## Priority 1: Build the neighbourhood panel

| Dataset | Resolution and coverage | Main use | Important limitation |
|---|---|---|---|
| [Berlin LOR boundaries](https://daten.berlin.de/datensaetze/lebensweltlich-orientierte-raume-lor-01-01-2021-wfs-34c86848) | 542 Planungsräume, 143 Bezirksregionen, 58 Prognoseräume | Stable neighbourhood units for tree, watering, heat, and vulnerability aggregation | Boundaries changed from the pre-2021 LOR system |
| [MSS 2025](https://daten.berlin.de/datensaetze/monitoring-soziale-stadtentwicklung-mss-2025-wfs-67692212) | LOR Planungsräume; indicators through 2024 | Unemployment, transfer receipt, child poverty, social status and change | Measures social disadvantage, not civic participation directly |
| [Environmental Justice Atlas 2023/24](https://daten.berlin.de/datensaetze/umweltgerechtigkeit-2023-2024-umweltatlas-wfs-2d02ba21) | Small-area Berlin indicators | Thermal burden, green-space provision, air/noise burden, and social disadvantage | Cross-sectional and partly model-derived |
| [LOR population by single year of age, 2024](https://daten.berlin.de/datensaetze/einwohnerinnen-und-einwohner-in-berlin-in-lor-planungsraumen-am-31-12-2024) | Planungsraum CSV | Elderly population, population denominators, and age-specific vulnerability | One annual snapshot |
| [Health and Social Structure Atlas 2022](https://daten.berlin.de/datensaetze/gesundheits-und-sozialstrukturatlas-berlin-2022-indexwerte-auf-ebene-der-planungsraeume-1191176) | Planungsraum CSV; 20 indicators | Broader health and social vulnerability index | Index construction may overlap with MSS variables |

## Priority 2: Temperature, drought, and watering need

| Dataset | Resolution and coverage | Main use | Important limitation |
|---|---|---|---|
| [DWD Climate Data Center daily climate data](https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/daily/kl/) | Daily station observations; long time series | Daily maximum/minimum temperature, precipitation, humidity, wind, antecedent rainfall, heatwave definitions | Berlin stations are sparse; select stations by coordinates, not by a name substring |
| [Berlin Climate Analysis Maps 2022](https://daten.berlin.de/datensaetze/klimaanalysekarten-2022-umweltatlas-wfs-255aead2) | City climate model; vector WFS and [raster products](https://daten.berlin.de/datensaetze/klimaanalysekarten-2022-umweltatlas-b76870e3) | Near-ground air and surface temperature, night cooling, PET/UTCI, wind and cold-air flows | Represents a modelled reference summer situation, not daily variation |
| [Berlin Water Balance 2022](https://daten.berlin.de/datensaetze/wasserhaushalt-2022-umweltatlas-wfs-f3878ec6) | Block and sub-block scale | Static infiltration, evaporation, runoff, and hydrological context around trees | Long-term/modelled conditions, not daily soil moisture |
| [Berlin Sealing 2021](https://daten.berlin.de/datensaetze/versiegelung-2021-umweltatlas-wfs-46d7bcf5) | Block/sub-block data in 10% classes | Imperviousness around trees and grid cells | Single reference year |
| [Building heights](https://daten.berlin.de/datensaetze/gebaudehohen-umweltatlas-wfs-d918088d) and [ALKIS buildings](https://daten.berlin.de/datensaetze/alkis-berlin-gebaude-wfs-728b368a) | Individual buildings | Urban morphology, shade potential, built density, street-canyon controls | Large files and substantial preprocessing |

## Priority 3: Remote-sensing outcomes

| Dataset | Resolution and coverage | Main use | Important limitation |
|---|---|---|---|
| [Landsat 8 Collection 2 Level 2](https://developers.google.com/earth-engine/datasets/catalog/LANDSAT_LC08_C02_T1_L2) plus Landsat 9 | Surface temperature product and reflectance; 2013-present | Consistent multi-year summer LST panel and heat-event composites | Thermal information is natively much coarser than an individual tree and acquired in daytime |
| [Sentinel-2 Level-2A harmonized](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR_HARMONIZED) | 10-20 m reflectance; 5-day revisit | NDVI/EVI, canopy condition, vegetation stress, pre/post watering response | No thermal band; cloud masking and seasonal phenology matter |
| [ECOSTRESS LST Version 3](https://www.earthdata.nasa.gov/data/catalog/lpcloud-eco-l2g-lste-003) | 70 m instantaneous LST; variable acquisition times | Event-matched and occasional nighttime thermal observations | Irregular coverage and a short, sparse time series |
| [Copernicus Tree Cover Density 2021](https://land.copernicus.eu/en/products/high-resolution-layer-forests-and-tree-cover/tree-cover-density-2021-raster-10-m-100-m-europe-yearly) | 10 m and 100 m; annual products available from 2018 | Independent canopy-density measure and canopy change | Does not identify individual planting events |
| [Copernicus Imperviousness Density 2021](https://land.copernicus.eu/en/products/high-resolution-layer-imperviousness/imperviousness-density-2021) | 10 m and 100 m | Harmonized sealing layer and external validation | Berlin's own sealing product is likely more locally detailed |

## Health and economic extensions

- The [RKI heat-mortality estimates](https://edoc.rki.de/bitstream/handle/176904/12682/EB-19-2025_10-25646-13135.pdf)
  provide national and federal-state estimates, not neighbourhood outcomes.
- No public daily mortality dataset at Berlin district or LOR resolution was
  identified in this first search. A mortality chapter would require a formal
  data request and a clear data-protection plan.
- Municipal tanker routes, watering volumes, staff time, and costs do not appear
  to be published as a reusable citywide dataset. Request these from the Senate
  and district green-space offices before promising a municipal-versus-citizen
  cost-benefit comparison.

## Recommended acquisition order

1. LOR boundaries, MSS 2025, Environmental Justice 2023/24, and LOR age data.
2. DWD daily observations for all stations inside a Berlin-area bounding box.
3. Berlin Climate Analysis 2022, Sealing 2021, and Water Balance 2022.
4. A pilot Earth Engine extraction for summer 2022 Landsat LST and Sentinel-2 vegetation indices.
5. ECOSTRESS Version 3 coverage audit for Berlin watering-event dates.
6. ALKIS/building-height variables only after the grid or LOR analysis unit is fixed.
7. Submit municipal irrigation and mortality data requests early because response times are uncertain.

## Design implication

The most defensible panel is likely `LOR-month` or `250 m grid-week`, with:

- watering events, litres, and fraction of eligible trees watered;
- antecedent precipitation and heat from DWD;
- canopy, sealing, tree age/species composition, and urban morphology;
- LST or vegetation stress as outcomes;
- social and health vulnerability attached at LOR level.

Tree-level records should feed exposure variables, but satellite LST should not
be treated as an independent tree-level outcome.
