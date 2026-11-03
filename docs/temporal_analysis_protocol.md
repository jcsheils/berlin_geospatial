# Temporal Analysis Protocol

## Purpose and status

This protocol documents the descriptive temporal layer: when and where
**recorded** citizen watering occurred. Monthly maps are exposure descriptions,
not evidence of cooling. Individual watering-induced satellite cooling is
outside the active design; see the [analysis plan](analysis_plan.md).

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

## Temporal alignment

A pooled May map may combine neighbourhoods watered only in May 2021 with
others watered only in May 2024. It describes where May activity occurred
across the study period; it cannot identify the exposure preceding a May 2024
temperature observation. Joining those data on calendar month alone would
assign watering to the wrong observation dates and could distort an association
in either direction, including obscuring it.
Weather and outcome joins therefore use actual dates, never calendar month alone.

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
  date but not credible within-day ordering.
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

## Claim limits

LST is not air temperature or felt heat, a platform zero is not no watering,
and a polished temporal map does not strengthen an identification design.
