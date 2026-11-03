# Watering response: agreed exploratory stage

Agreement recorded in the conversation on 29 September 2026. This addendum
governs the current exploratory deliverable. It supersedes the older plan's
definition of RQ2 for this stage; the previous satellite cooling design remains
a separate feasibility proposal, not a prerequisite for studying response.

## Questions retained provisionally

1. How large is the vegetation–cooling gradient in Berlin, how does it vary
   under drought, and how is it distributed with respect to thermal exposure
   and socioeconomic vulnerability?
2. Does logged citizen watering respond to heat and dryness, and does the
   strength of that association differ with neighbourhood vulnerability?
3. Where does predicted citizen care fail to coincide with independently
   assessed need, and what municipal priorities follow under explicit
   allocation assumptions?

Weak, null or opposite associations are valid results. Question retention
depends on measurement, coverage and feasibility, not statistical significance.

## Deliverable and geographical scope

- Count recorded events, recorded litres and distinct tree IDs per actual
  calendar month at Berlin, district (Bezirk) and LOR Planungsraum scales.
- Keep 2020's incomplete platform window visible. Never fill January–April
  2020 as observed zero; label May as partial (18–31 May).
- Reuse the assigned-tree crosswalk. Distinct trees are recomputed from IDs
  for each reporting period; monthly distinct counts are not summed into
  annual distinct counts. Reconcile aggregates to the foundation panel.
- Rates use the current inventory, not a historical eligible-tree risk set.
- Describe social-status groups using the existing MSS 2025 classification
  (reference 31 December 2024). This is a static contextual comparison, not
  historical income or the socioeconomic status of individual volunteers.
- Ortsteile are not LORs or Bezirke. The supervisor's Ortsteil file requires
  schema/metadata inspection and a verified spatial mapping before any join.

## Weather fallback specified before estimating associations

The supplied monthly Landsat/rainfall CSV was initially unavailable behind
SharePoint authentication. The user supplied a local copy on 29 September
2026; its provisional extension is specified below. Do not substitute the
existing summer snapshots for monthly observations.

Use DWD Berlin-Tempelhof station 00433 as an explicitly labelled, single-station
temporal context if its historical archive covers the required dates. Select
it for its long continuous Berlin record, not its correlation with watering.
Preserve the archive and its metadata, source URL, download date and checksum.
Daily TMK is mean air temperature (°C), TXK maximum air temperature (°C), and
RSK precipitation (mm). Convert -999 to missing. Preserve quality codes.
Only calculate monthly means/totals when every day of that month has a valid
measurement for the relevant variable. Never treat missing rain as zero.

Monthly exploratory associations use the 60 complete calendar months of
2021–2025, keeping zero-activity months. Outcomes are separately log(1+events),
log(1+litres), and log(1+distinct trees). For each outcome, fit two separate
ordinary least-squares models:

- same-month mean air temperature and rainfall;
- previous-calendar-month mean air temperature and rainfall.

Both include calendar-month and year indicators. Scale temperature to 5 °C
and rainfall to 10 mm. Report slopes in log(1+outcome) units and approximate
95% uncertainty intervals using Newey–West HAC with three monthly lags.
Raw Spearman correlations are descriptive, with sample sizes and no naive
independent-observation p-values. Fit the same models excluding 2022 as a
sensitivity check. HAC must retain actual calendar-month distances when a
year is removed; do not treat December 2021 and January 2023 as adjacent.

This is a small, retrospective exploratory panel with several outcomes and
specifications. Intervals are approximate and not multiplicity-adjusted;
report the full grid rather than selecting significant results. Calendar-month
and year adjustment reduces broad seasonality and yearly level differences,
but does not remove changes in logging, campaigns, participation or all other
confounding. A prior-month association is not proof of behavioural motivation.
Do not interpret log(1+y) slopes as exact percentage changes in arithmetic
mean counts or litres.

Station weather is shared temporal context, not 12 independent district
weather measurements. This first report describes monthly social-status
differences; formal vulnerability-by-weather interactions require a separate
specified model accounting for repeated neighbourhood and shared-date errors.
Do not use station air temperature as the outcome of a local cooling test.

## Cooling feasibility and next input

Inspect the supervisor CSV for geographic IDs, month/year, source and units,
LST acquisition dates, clear-sky counts, quality masks, spatial averaging and
rainfall provenance. The monthly file may support descriptive same-month and
next-month LST associations; a monthly aggregate cannot establish event order
within a month. Estimating cooling requires a separate identification and
detectability assessment at a defensible spatial and temporal support.

The report will explicitly distinguish completed descriptive/response work
from unavailable local-temperature, causal-cooling and allocation results.

## Supplied monthly LST extension (29 September 2026)

The received file has 9,312 rows for 2018–2025, 96 distinct Ortsteil names,
and two differing Buckow records per month. It omits Schlachtensee. Count is
zero exactly when LST is missing; large counts and repeated per-area maxima
suggest a spatial count, but its meaning remains unverified. Acquisition
dates, sensor selection, cloud masks, compositing, source polygons and
rainfall provenance are absent. These limitations prevent interpreting count
as the number of satellite overpasses or using it as an inferential weight.

Before examining watering–LST correlations:

- Preserve the received CSV unchanged. Keep the two Buckow records in a
  separate audit table, without averaging or selecting either record.
- Retrieve the official ALKIS Ortsteil polygons and assign tree-inventory
  points directly to them in EPSG:25833. This is a provisional current-boundary
  alignment, not confirmation of the source CSV's original polygons.
- Retain all 97 official Ortsteile in the watering panel. Exclude Buckow from
  the LST join because its outcome key is ambiguous. Exclude Nikolassee and
  Zehlendorf because Schlachtensee was formed from parts of them in December
  2020, and source geography is unspecified. Schlachtensee has no source LST.
  The remaining 93 areas are the provisional comparison sample.
- Reconcile assigned tree IDs, events, litres and distinct monthly trees;
  expose any spatially unassigned records. Never duplicate observations in
  a many-to-many join. Keep current inventory and area denominators explicit.
- Join previous- and next-month outcomes by exact calendar dates, before
  filtering the sample. Never shift across missing observations or join
  December to January of the wrong year. Earlier weather-only dates can
  supply previous-month LST, but no missing watering month is imputed.
- Use complete years 2021–2025, April–September watering months, for the
  primary provisional descriptions. Report all-calendar-month and
  excluding-2022 sensitivities. Do not choose years by apparent association.
- For events, litres and distinct trees per hectare, report unadjusted
  Spearman correlation and correlation of residuals after removing Ortsteil
  and actual year-month fixed effects from LST and log(1 + exposure).
  Residualise using the same complete-case sample for both variables.
  These are descriptive partial associations, without p-values, confidence
  intervals or claims of statistical significance.
- Report three alignments separately: previous-month LST versus current
  watering (response-oriented), same-month LST versus watering, and current
  watering versus next-month LST (subsequent-temperature description).
- Add a sensitivity retaining outcomes whose reported count is at least
  half that area's maximum observed count. Call this a relative-count
  screen, not a validated clear-sky-coverage threshold. Retain missingness
  and availability counts in all outputs.
- Preserve rainfall as `source_rain_mm_mean_unverified`. Its aggregation and
  provenance must be clarified before it enters an adjusted physical model.

This extension estimates neither causal cooling nor the older confirmatory
H2 dose coefficient. It cannot settle RQ1, historical vulnerability interactions
or municipal allocation. Metadata clarification is necessary before treating
the local LST comparisons as validated substantive thesis evidence.
