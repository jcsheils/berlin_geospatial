# Temporal analysis protocol

This protocol covers the descriptive temporal layer: when and where citizens **recorded** watering. Monthly maps describe exposure; they are not evidence of cooling. Watering-induced satellite cooling is outside the design (see the [analysis plan](analysis_plan.md)).

## Data

The exposure source is the Gieß den Kiez snapshot registered as `recorded_watering_events` in `config/datasets.toml`, analysed from 18 May 2020 to 31 December 2025. The canonical panel is `data/processed/foundation/lor_month_recorded_watering_2020_2025.csv`; its metadata file records source checksums, linkage totals, zero semantics and denominator limits.

Timestamps stay in UTC. Calendar dates and months come from conversion to Europe/Berlin. Exact duplicate rows are dropped before aggregation. Exposure variables carry the prefix `recorded_` to separate platform records from total irrigation.

## Grains

### Tree-day

A tree-day is one catalogued tree ID on one Berlin calendar date, the finest exposure unit. Repeated logs for the same tree and date collapse into one row, so they do not count as independent observations:

- `recorded_events_tree_day`: deduplicated log rows;
- `recorded_litres_tree_day`: summed litres;
- `multiple_logs_tree_day`: flag for more than one log.

### Planungsraum-month

The LOR-month panel is balanced: 542 Planungsräume × 68 months. Each row holds recorded events, litres, distinct watered trees and labelled current-inventory rates. It is the main grain for monthly maps and seasonality.

- **May 2020** has only 14 platform days. Flag it `partial_platform_start`, exclude it from complete-month and year-on-year comparisons, and never annualise it. Chronologies may show it if hatched or labelled.
- **Zero** means no platform activity in that area-month, not an absence of municipal, private or unlogged watering. It is a valid descriptive value but does not mark an untreated control.
- **Denominators** use the current inventory. They may include trees planted after the month mapped and miss trees removed before the snapshot, so call the results "current-inventory-normalised recorded care", not historical coverage.

### Year-specific monthly maps

Five atlas sheets show January–December for each of 2021–2025, drawing each map from one actual year and month. Shared class thresholds, calibrated once on positive April–September 2021–2025 rates, apply to all sixty maps, the active-season grid and the climatology. Calibrating the scale on pooled data does not pool the mapped values.

The sheets live at `output/03_spatial_equity_vulnerability/maps/yearly/YYYY_monthly_recorded_watering_atlas.png`. Panel labels give matched events and the number of active Planungsräume. `data/processed/temporal/berlin_year_recorded_watering_2021_2025.csv` reports annual events, litres, watered tree-months, active areas and area-months, and the peak month. These describe observed exposure, not logging completeness.

### Calendar-month climatology

The climatology uses the complete years 2021–2025. For each Planungsraum and calendar month, compute the metric per year, then report the five-year mean (the main map statistic), the median (a skewness check) and the share of years with any activity (persistence). May 2020 and partial 2026 are excluded. "Climatology" means a recurring calendar pattern in recorded activity, not a climate normal.

## Atlas contents

- monthly time series of events, litres and distinct trees;
- year-by-month heatmaps;
- the five year-specific January–December sheets;
- monthly Planungsraum maps of litres, events, distinct trees and current-inventory reach;
- the 2021–2025 climatology and persistence maps;
- age- and genus-stratified summaries where denominators allow.

The year sheets keep all twelve months, including winter zeros. A separate April–September grid sets the five years side by side.

Each metric gets one scale, chosen on the pooled comparison period and fixed across all months and years. Recorded zero has its own class. If extreme concentration needs a cap, report the cap and the share of capped values, and apply it to every panel. Totals and rates use separate legends; their colours are not comparable. Boundaries, projection, missing-data colour and layout stay constant.

## Temporal alignment

A pooled May map can combine areas watered only in May 2021 with areas watered only in May 2024. It shows where May activity happened over the period, but it cannot identify the exposure before a May 2024 temperature reading. Joining on calendar month alone would assign watering to the wrong dates and could bias an association either way, or hide it. Weather and outcome joins therefore use actual dates.

## Exposure audit

These counts hold for the current source snapshot; regenerate them if it changes.

- **Totals.** The source has 58,847 rows. After removing 111 exact duplicates, 58,474 events fall in the study window. Of these, 57,786 events and 2,249,502 litres link to a tree and a Planungsraum, covering 11,127 trees; 688 events are unmatched or unassigned.
- **Seasonality.** 92.2% of events (53,916) fall in May–September and 71.6% (41,879) in June–August.
- **Timestamps.** Clock precision changes in April 2024. Every 2020–2023 record has a non-midnight time; 3,528 of 3,679 records in 2024 and all 4,601 in 2025 sit at exactly 00:00 UTC. From May 2024 the data keep the date but not the order within a day.
- **Repeat logs.** The 58,474 in-window events form 50,818 tree-days. 5,484 tree-days have multiple logs (13,140 rows in total), up to 16 for one tree-day. Analyses aggregate these before spatial or temporal joins.
- **Sparsity.** 16.3% of LOR-months (6,002 of 36,856) are positive, 80 of 542 Planungsräume never record an event, and the median area is active in 9 of 68 months.
- **Why year-specific maps.** 338 Planungsräume record May activity in some year of 2021–2025, but only 12 do so in all five years and 125 in just one. Active May areas by year: 50, 273, 165, 141 and 113, with 359, 2,805, 894, 701 and 654 events. The union is not exposure for any single May.
- **Concentration.** The Gini coefficient of cumulative litres across trees is 0.70. The top 1% of trees receive 17.7% of litres and the top 10% receive 57.9%, so dose models must report leverage and common support.
- **Age.** 13,237 events concern trees aged 0–9 at watering, 1,292 trees aged exactly 10, 43,047 older trees, and 210 have unknown age.
- **Type and genus.** 94.4% of linked events (54,550) concern street trees and 5.6% (3,236) park trees. Linden and maple account for about 60% of events; most other species are sparse. Planting year is often missing for park trees in the inventory, though nearly complete for logged trees.

These counts describe rows and doses, not independent observations or effective sample size.

## Claim limits

LST is not air temperature or felt heat. A platform zero is not an absence of watering. A polished map does not strengthen an identification design.
