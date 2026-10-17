> **October 2026 scope update:** historical design context is retained below. The active design is the October proposal: Part II civic heat response (core), Part I vegetation cooling loss (supporting), and Part III allocation (exploratory). See `docs/analysis_plan.md` and `examination/README.md`. Existing descriptive products remain valid within their stated limits.

# Temporal Analysis Protocol

## Purpose and status

This protocol adds a temporal layer to the study without overstating what the
current data can identify. The analysis has two distinct aims:

1. describe when and where **recorded** citizen watering occurred; and
2. conditionally test whether antecedent recorded watering intensity is
   associated with subsequent satellite-supported land-surface temperature
   (LST).

The temporal atlas is feasible with the current repository. A post-watering
thermal analysis is not yet feasible because event-aligned outcomes, weather
controls, logging-coverage diagnostics, and the pre-specified detectability
gate are not complete. Monthly maps are therefore exposure descriptions, not
evidence of cooling.

## Data scope and provenance

The current exposure source is the Gieß den Kiez snapshot registered as
`recorded_watering_events` in `config/datasets.toml`. The declared analysis
window is 18 May 2020 through 31 December 2025. The canonical neighbourhood
panel is
`data/processed/foundation/lor_month_recorded_watering_2020_2025.csv`; its
adjacent metadata file records source checksums, linkage totals, zero semantics,
and denominator limitations.

All source timestamps remain stored in UTC. Calendar dates and months used in
analysis are derived after conversion to `Europe/Berlin`. Exact duplicate
source rows are removed before any aggregation. New exposure variables use the
prefix `recorded_` to distinguish platform records from total irrigation.

## Locked analytical grains

### Local-date/tree-day

A tree-day is one catalogued tree identifier on one Europe/Berlin calendar
date. Multiple log rows for the same tree-day are retained in an audit count
but collapsed analytically:

- `recorded_events_tree_day`: number of deduplicated log rows;
- `recorded_litres_tree_day`: sum of recorded litres; and
- `multiple_logs_tree_day`: indicator for more than one log row.

Tree-days, rather than raw event rows, are the finest repeated exposure unit.
They prevent repeated entries for one tree and date from being treated as
independent observations.

### Planungsraum-month

The LOR-month panel is balanced across 542 Planungsräume and 68 months. Each
row contains monthly recorded events, recorded litres, distinct recorded
watered trees, and explicitly labelled current-inventory-normalised measures.
It is the primary grain for monthly mapping and neighbourhood seasonality.

May 2020 contains only 14 platform-live days. It must be marked
`partial_platform_start`, excluded from complete-month or year-on-year
comparisons, and never silently annualised. It may be shown in a chronology if
hatched or otherwise labelled as partial.

A zero in the panel means that no platform activity was recorded for that
Planungsraum-month. It does not mean that no municipal, private, or unlogged
watering occurred. Zero is therefore a valid descriptive platform value but
not, by itself, an untreated-control designation.

All denominator-dependent fields use the current inventory snapshot. They are
not historical monthly risk sets and may include trees planted after the month
being mapped or exclude trees removed before the snapshot. Results are called
"current-inventory-normalised recorded care," not historical irrigation
coverage.

### Year-specific monthly maps

Five atlas sheets show January--December separately for 2021, 2022, 2023,
2024, and 2025. Each map selects one actual year and month from the canonical
Planungsraum-month panel. No values are pooled across years. The shared
classification thresholds are calibrated once on positive April--September
2021--2025 rates and reused across all sixty maps, the active-season grid, and
the climatology. Pooling for scale calibration does not pool the mapped data.

Files are `output/03_spatial_equity_vulnerability/maps/yearly/` followed by
`YYYY_monthly_recorded_watering_atlas.png`. Panel annotations report matched
events and the count of Planungsräume with at least one recorded event. The
annual diagnostic table is
`data/processed/temporal/berlin_year_recorded_watering_2021_2025.csv`; it reports
events, litres, watered tree-months, active neighbourhoods and
neighbourhood-months, and the peak event month. These measures describe
observed exposure availability, not the completeness of platform logging.

### Calendar-month climatology

The calendar-month climatology uses the five complete calendar years
2021--2025. For each Planungsraum and calendar month, first calculate the
metric separately in each year and then report:

- the five-year mean monthly value as the primary map statistic;
- the median as a skewness sensitivity; and
- the share of the five years with any recorded activity as a persistence
  measure.

May 2020 and partial 2026 are excluded. "Climatology" here denotes a recurring
calendar-month pattern in recorded activity, not a climate normal.

### Imagery-support/overpass

Future thermal analysis will use one observation per non-overlapping,
approximately 1 ha imagery-support unit and valid satellite overpass. Tree-day
records feed exposure sums within the support. The outcome is support-mean LST,
not an individual-tree temperature and not an independent value for every
resampled 30 m Landsat product cell. The spatial support, overlap rule, edge
treatment, CRS, and tree-to-support crosswalk must be frozen before outcome
modelling.

## Descriptive temporal atlas

The atlas will present:

- annual monthly time series of events, litres, and distinct recorded trees;
- year-by-calendar-month heatmaps;
- five separate year-specific January--December map sheets, each using the
  dated panel rather than the calendar-month climatology;
- monthly Planungsraum maps of recorded litres, events, distinct watered
  trees, and current-inventory-normalised reach;
- the 2021--2025 calendar-month climatology and persistence maps; and
- age- and genus-stratified temporal summaries where denominators are adequate.

The year-specific sheets retain all twelve months, including recorded-zero
winter months. An additional April--September grid places the five years side
by side for active-season comparison; the twelve-month climatology remains a
separate descriptive summary.

For each metric, one map scale is selected from the pooled comparison period
and locked across all months and years. Recorded zero receives its own visible
class. If a fixed upper cap is needed because of extreme concentration, the cap
and the share of capped observations are reported and used identically in every
panel. Raw totals and normalised rates use separate, clearly labelled legends;
their colours are not interpreted as comparable magnitudes. Boundaries,
projection, missing-data colour, and layout remain constant across panels.

## Temporal alignment and choice of years

A pooled May map may combine neighbourhoods watered only in May 2021 with
others watered only in May 2024. It describes where May activity occurred
across the study period; it cannot identify the exposure preceding a May 2024
temperature observation. Joining those data on calendar month alone would
assign watering to the wrong observation dates and could distort an association
in either direction, including obscuring it. It would not establish that a
null result is biological.

Thermal analysis must retain spatial support and the actual acquisition date
as keys. For example, the primary window for an overpass on 20 May 2024 sums
recorded watering from 20 April through 19 May 2024. May observations from
2021--2023 or 2025 contribute nothing to that exposure. Windows follow real
calendar dates, so a legitimate 30-day window in January may extend into the
preceding December; the rule is date alignment, not a blanket prohibition on
crossing 1 January. The climatology is never substituted for these dated sums.

Keeping several years does not itself create temporal misalignment. Retain
all years satisfying pre-specified eligibility rules, with actual overpass-date
controls and year-specific diagnostics. Restricting the analysis to one year
is justified only when the data support that restriction, and may reduce
available variation and precision. Assess, before inspecting cooling estimates:

- dated imagery availability, cloud quality, and pre/post exposure coverage;
- antecedent weather and compatible spatial support;
- logging coverage and the change in timestamp precision during 2024;
- within-year dose variation, common support, spatial concentration, and
  independent support/date information; and
- the existing detectability gate for the proposed sample.

The exposure summary alone cannot determine a preferred year. In particular,
the largest event total need not provide the most informative thermal sample.
Record the year-selection rule before estimating cooling associations; do not
choose a year based on which produces a significant or larger apparent effect.
Where feasible, compare year-specific estimates and leave-one-year-out results
as pre-specified sensitivity analyses after the pooled eligible sample passes
the gate. The current repository still lacks the dated thermal panel needed
to make this year-selection decision.

## Empirical exposure audit

The following facts are locked to the current source snapshot and must be
regenerated if that snapshot changes:

- The source contains 58,847 rows. After removing 111 exact duplicates, 58,474
  source events fall in the declared study window. Of these, 57,786 events and
  2,249,502 litres are tree-linked and assigned to a Planungsraum, covering
  11,127 trees; 688 source events are unmatched or spatially unassigned.
- Activity is strongly seasonal: 53,916/58,474 events (92.2%) occur from May
  through September, and 41,879/58,474 (71.6%) occur from June through August.
- Clock-time precision changes during April 2024. All 2020--2023 records have a
  non-midnight time; 3,528/3,679 records in 2024 and all 4,601 records in 2025
  are stamped exactly at 00:00 UTC. From May 2024 onward, the data preserve a
  date but not credible within-day ordering. Primary exposure windows therefore
  end on the day before an overpass.
- Before inventory or LOR matching, the 58,474 in-window source events form
  50,818 tree-days. Of these, 5,484 have multiple logs, accounting for 13,140
  source event rows; the maximum is 16 logs for one tree-day. Analyses aggregate
  these records before spatial or temporal joins.
- Exposure is sparse: 6,002/36,856 LOR-months (16.3%) are positive, 80/542
  Planungsräume never have a recorded event, and the median Planungsraum is
  active in nine of 68 months.
- The need for year-specific maps is visible in May: the 2021--2025 union
  contains 338 Planungsräume with recorded May activity, but only 12 record
  activity in May of all five years and 125 in May of only one year. Active
  May Planungsräume by year are 50, 273, 165, 141, and 113 respectively;
  corresponding event totals are 359, 2,805, 894, 701, and 654. The union
  cannot be interpreted as exposure for any single May.
- Exposure is concentrated: the Gini coefficient of cumulative litres across
  recorded trees is 0.70; the top 1% of trees account for 17.7% of litres and
  the top 10% for 57.9%. Dose models must report leverage and common support.
- Age is observed for almost all linked events but is imbalanced: 13,237 events
  concern trees aged 0--9 years at watering, 43,047 concern trees older than
  10 years, 1,292 concern trees exactly age 10, and 210 have unknown age.
- Type is also imbalanced. Among the 57,786 matched-and-assigned in-window
  events, 54,550 (94.4%) link to street trees and 3,236 (5.6%) to park trees.
  Linden and maple together account for approximately 60% of enriched in-window
  event rows, while the long tail of named species is sparse. Inventory-wide
  planting year is missing especially often for park trees, despite high age
  completeness among trees that were logged.

These counts describe rows and recorded doses, not independent observations or
effective sample size.

## Tiered post-watering cooling design

### Tier 1: exposure-only description

The temporal atlas and tree-type/age timing summaries are the guaranteed
deliverables. Permitted conclusions concern timing, concentration, recurrence,
and spatial distribution of recorded care.

### Tier 2: event-aligned descriptive outcomes

After a cloud-audited outcome panel exists, plot support-level LST and
vegetation-condition trajectories around pre-defined recorded-watering bursts.
Burst thresholds and washout periods must be fixed before examining outcomes.
Use strictly antecedent whole-day exposure for the cross-year analysis; any
same-day timing analysis is restricted to periods with validated clock times
and remains secondary. Lead patterns, observation availability, and the weather
distribution of clear-sky overpasses are reported. These results remain
descriptive because watering is likely to respond to heat and drought.

### Tier 3: qualified observational association

The primary exposure for support unit \(s\) and overpass date \(t\) is:

\[
W^{30}_{st} = \frac{1}{1{,}000 A_s}
\sum_{d=t-30}^{t-1}\text{recorded litres}_{sd},
\]

where \(A_s\) is support area in hectares. The coefficient unit is K per
additional 1,000 recorded L/ha during the preceding 30 complete local dates.
Seven- and 14-day windows are secondary; season-to-date dose is exploratory.
Same-day dose is excluded from the primary definition.

Subject to the detectability gate, the primary model is:

\[
Y_{st} = \alpha_s + \delta_t + \beta W^{30}_{st}
       + \rho Y_{s,pre} + X_{st}'\gamma + \varepsilon_{st},
\]

where \(Y_{st}\) is support-mean LST, \(\alpha_s\) are support fixed effects,
and \(\delta_t\) are overpass-date or scene fixed effects. The pre-period
outcome and all covariates in the primary adjustment set must precede the
exposure window or be demonstrably unaffected by watering.

The adjustment set includes antecedent LST and Sentinel-2 greenness; dated tree
density and composition; imperviousness, built form, building height/shade, and
water proximity; acquisition sensor, quality, cloud, view, and emissivity
information; and acquisition-day plus 7-, 14-, and 30-day weather summaries for
temperature, humidity/dew point, precipitation, wind, radiation, and drought
context. Time-invariant support characteristics are absorbed by support fixed
effects. Contemporaneous greenness, which may mediate watering effects, is not
used as a primary confounder control.

The primary sample is restricted to support units and periods satisfying a
logging-coverage rule fixed without reference to LST. Recorded-zero units are
not assumed unwatered. No-record matching is, at most, a secondary diagnostic.

## Detectability gate and diagnostics

Before estimating or viewing the H2 exposure coefficient, an outcome-only
nuisance model estimates residual LST variance and spatial covariance. Power
simulations preserve the observed continuous-dose distribution, clustering,
effective sample size, and plausible exposure-measurement error. Confirmatory
H2 proceeds only when simulated power is at least 80% at two-sided
\(\alpha=0.05\) for \(\beta=-0.03\) K per additional 1,000 recorded L/ha/30
days and the simulated minimum detectable effect is no larger in magnitude than
0.03 K. Failure of the gate returns the analysis to Tiers 1--2; it is not
evidence of no physiological effect.

Required diagnostics are:

- usable-overpass counts, dose density, positivity, leverage, and effective
  sample size;
- covariate balance and common-support plots;
- residual spatial dependence and uncertainty robust to support and date
  clustering, using spatial block bootstrap or another justified alternative;
- negative leads and pre-trend plots;
- shifted-date and shifted-location placebos;
- spillover exclusions and alternative support radii;
- 7-/14-day timing, carryover, washout, nonlinear-dose, and influential-dose
  sensitivities;
- comparison of observed clear-sky weather with all summer days; and
- missingness, sensor, cloud-mask, exposure-outlier, and timestamp-era
  sensitivities.

## Age and genus heterogeneity

Age and genus are secondary effect-modification analyses at the imagery-support
level. They do not create individual-tree temperature outcomes.

Tree age at watering is local calendar year minus planting year. The preferred
specification uses continuous age with a pre-specified spline. A categorical
sensitivity uses exhaustive, non-overlapping bands of 0--9, 10--19, 20--39,
40--59, 60+ years, and unknown; no exact age is dropped. Age-specific dose or a
total-dose-by-age-composition interaction is estimated only where within-support
variation and common support are adequate.

Taxonomy is standardised from the tree inventory before modelling. Genus, not
the sparse named-species field, is the default level. Genera are collapsed using
a rule fixed from exposure counts and biological relevance before outcome
inspection, with explicit `other` and `unknown` groups. Hierarchical partial
pooling is preferred to separate unregularised coefficients. Interaction
estimates include uncertainty intervals and multiplicity control, and are
omitted where dose components are collinear or unsupported. Because age and
genus covary with canopy size, location, and watering selection, estimates are
described as heterogeneous adjusted associations.

## Inputs required before Tier 2 or Tier 3

- Cloud-audited Landsat 8/9 LST with acquisition timestamps, sensor metadata,
  QA bands, native-resolution limitations, and repeated pre-period outcomes.
- Sentinel-2 antecedent greenness/vegetation-condition observations.
- ERA5 harmonised temporal controls and DWD station sensitivity data, including
  precipitation and heat before each overpass.
- Dated imperviousness, built form, shade/building height, water proximity, and
  relevant hydrological context.
- A complete tree-to-imagery-support crosswalk with canonical taxonomy,
  planting year, source layer, crown diameter, height, and historical
  eligibility diagnostics.
- A pre-outcome logging-coverage score and, where obtainable, municipal and
  otherwise unlogged watering information or defensible proxies.
- A version-locked run manifest and the completed detectability record.

Individual-tree or near-ground cooling claims would additionally require local
canopy, soil, or air-temperature sensors and a design with exogenous watering
assignment or timing.

## Claim ladder

1. **Data audit:** completeness, timestamp precision, linkage, sparsity, and
   measurement limitations.
2. **Descriptive temporal/spatial pattern:** when and where recorded care is
   concentrated.
3. **Event-aligned descriptive outcome:** observed LST or greenness trajectories
   around recorded watering without an effect claim.
4. **Qualified observational association:** adjusted support-level association
   after the gate, with diagnostics and explicit identifying assumptions.
5. **Quasi-experimental or causal estimate:** permitted only if watering timing
   or dose is credibly exogenous, with supported exchangeability, positivity,
   consistency, interference, and missing-observation assumptions.

Absent a randomized or defensibly quasi-random watering schedule, Tier 3 is the
highest warranted claim. LST is not air temperature or felt heat, a platform
zero is not no watering, and a polished temporal map does not strengthen the
identification design.
