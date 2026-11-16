# Monthly watering response protocol, 29 September 2026

Agreed on 29 September 2026, this protocol governs the monthly exploratory deliverable. For this stage it replaces the older plan's definition of RQ2. The earlier satellite cooling design remains a separate feasibility proposal, not a prerequisite for studying response.

## Questions retained provisionally

1. How large is the vegetation–cooling gradient in Berlin, how does drought change it, and how does it relate to thermal exposure and socioeconomic vulnerability?
2. Does logged citizen watering respond to heat and dryness, and does the association differ with neighbourhood vulnerability?
3. Where does predicted citizen care miss independently assessed need, and what municipal priorities follow under explicit allocation assumptions?

Weak, null or opposite associations are valid results. Measurement, coverage and feasibility decide whether a question stays, not statistical significance.

## Deliverable and geography

- Count recorded events, litres and distinct tree IDs per calendar month for Berlin, each Bezirk and each LOR Planungsraum.
- Keep 2020's incomplete platform window visible: never fill January–April 2020 with zeros, and label May as partial (18–31 May).
- Reuse the assigned-tree crosswalk. Recompute distinct trees from IDs for each period instead of summing monthly counts, and reconcile aggregates with the foundation panel.
- Rates use the current inventory, not a historical risk set.
- Describe social-status groups with the MSS 2025 classification (reference 31 December 2024). This is static context, not historical income or the status of individual volunteers.
- Ortsteile are neither LORs nor Bezirke. The supplied Ortsteil file needs schema and metadata checks and a verified spatial mapping before any join.

## Weather, specified before estimating associations

The supplied monthly Landsat and rainfall CSV was at first available only behind SharePoint authentication; a local copy arrived on 29 September 2026, and the extension below covers it. Do not substitute the existing summer snapshots for monthly observations.

Use DWD Berlin-Tempelhof (station 00433) as single-station temporal context if its archive covers the dates. It was chosen for its long continuous Berlin record, not for any correlation with watering. Keep the archive, its metadata, source URL, download date and checksum. TMK is mean air temperature (°C), TXK maximum air temperature (°C) and RSK precipitation (mm). Convert −999 to missing and keep quality codes. Compute monthly means or totals only when every day of the month has a valid value. Never treat missing rain as zero.

The monthly models use the 60 complete months of 2021–2025, including months without activity. Outcomes are log(1 + events), log(1 + litres) and log(1 + distinct trees). For each, fit two OLS models with calendar-month and year indicators:

- same-month mean air temperature and rainfall;
- previous-month mean air temperature and rainfall.

Scale temperature per 5 °C and rainfall per 10 mm. Report slopes in log(1 + outcome) units with approximate 95% Newey–West HAC intervals over three monthly lags. Report raw Spearman correlations with sample sizes and without naive p-values. Refit without 2022 as a sensitivity check, keeping true calendar distances so December 2021 and January 2023 are not adjacent.

This is a small retrospective panel with several outcomes and specifications. Intervals are approximate and unadjusted for multiplicity, so report the full grid. Month and year indicators absorb broad seasonality and yearly levels, but not changes in logging, campaigns or participation. A prior-month association does not prove behavioural motivation, and log(1 + y) slopes are not exact percentage changes.

Station weather is shared context, not 12 independent district measurements. This report describes monthly differences by social status; a formal vulnerability-by-weather interaction needs its own model for repeated areas and shared dates. Station air temperature must not serve as the outcome of a local cooling test.

## Cooling feasibility

Inspect the supplied CSV for area IDs, months, source and units, acquisition dates, clear-sky counts, quality masks, spatial averaging and rainfall provenance. A monthly file can support descriptive same-month and next-month LST associations, but it cannot order events within a month. Estimating cooling needs a separate identification and detectability assessment at a defensible spatial and temporal support.

The report must separate completed descriptive work from unavailable local-temperature, causal-cooling and allocation results.

## Monthly LST extension, 29 September 2026

The file has 9,312 rows for 2018–2025 and 96 distinct Ortsteil names, with two differing Buckow rows per month and no Schlachtensee. Count is zero exactly when LST is missing; large counts and repeated per-area maxima suggest a spatial count, but its meaning is unverified. Acquisition dates, sensor selection, cloud masks, compositing, source polygons and rainfall provenance are absent, so count cannot stand for overpasses or serve as an inferential weight.

Before examining watering–LST correlations:

- Keep the CSV unchanged. Put both Buckow rows in an audit table without averaging or picking one.
- Retrieve the official ALKIS Ortsteil polygons and assign inventory points to them in EPSG:25833. This is a provisional current-boundary alignment, not the source's original polygons.
- Keep all 97 official Ortsteile in the watering panel. Exclude Buckow from the LST join (ambiguous key), and Nikolassee and Zehlendorf because Schlachtensee was carved from them in December 2020 and the source geography is unknown. Schlachtensee has no source LST. The other 93 areas form the provisional sample.
- Reconcile tree IDs, events, litres and monthly distinct trees, and expose unassigned records. Never duplicate rows in a many-to-many join, and keep inventory and area denominators explicit.
- Join previous- and next-month outcomes on exact dates before filtering. Never shift across missing months or join December to the wrong January. Earlier weather-only months may supply previous-month LST; no missing watering month is imputed.
- Use April–September of the complete years 2021–2025 for the main descriptions, with all-month and without-2022 sensitivities. Do not pick years by apparent association.
- For events, litres and distinct trees per hectare, report raw Spearman correlations and correlations of residuals after removing Ortsteil and year-month fixed effects from LST and log(1 + exposure), on the same complete cases. These are descriptive partial associations without p-values, intervals or significance claims.
- Report three alignments: previous-month LST with current watering, same-month LST with watering, and current watering with next-month LST.
- Add a sensitivity that keeps outcomes whose count is at least half the area's maximum. Call it a relative-count screen, not a clear-sky threshold, and keep missingness and availability counts in every output.
- Keep rainfall as `source_rain_mm_mean_unverified` until its aggregation and provenance are clear enough for an adjusted physical model.

The extension estimates neither causal cooling nor the older H2 dose coefficient, and it cannot settle RQ1, historical vulnerability interactions or allocation. The LST comparisons need clarified metadata before they count as thesis evidence.
