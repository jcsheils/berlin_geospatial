# Reproducing the daily RQ1 pilot

This extends the frozen seminar results with the refined proposal's RQ1.
It uses Python 3.12 and the existing `requirements-spatial.txt` environment.
No network access, new downloads or additional dependencies are needed.

```bash
MPLCONFIGDIR=/tmp/berlin-rq1-mpl PYTHONPATH=src python pipelines/08_build_rq1_daily.py
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m berlin_heat validate
python tools/verify_examination.py
```

## Inputs and outputs

Inputs: the frozen Gieß den Kiez CSV, canonical tree-to-LOR crosswalk, monthly
foundation table for area metadata, canonical positive tree-day product for
reconciliation, and DWD 00433 historical ZIP. All are checksummed in
`output/rq1_daily/metadata.json`, along with implementation and protocol hashes
and Python/NumPy/pandas versions.

| Output | Meaning |
| --- | --- |
| `data/processed/rq1/lor_day_recorded_watering_apr_sep_2020_2025.csv.gz` | 542 areas × 1,051 days; events, litres, unique trees, coverage flag and contextual current stock |
| `output/rq1_daily/tables/daily_weather_features.csv` | Complete 2020–2025 weather calendar and strictly antecedent features; join to area-days by `date`, many-to-one |
| `output/rq1_daily/tables/city_day_*.csv` | Linked baseline, >500 L exclusion and all-valid-source comparisons |
| `output/rq1_daily/tables/annual_summary.csv` | Sample sizes, seasonal distinct trees, dispersion, sparsity and timestamp precision |
| `output/rq1_daily/tables/model_coefficients.csv` | Full 216-row coefficient grid across three outcomes; units are log1p |
| `output/rq1_daily/model_audit.json` | Dates entering/excluded from each fit and design condition numbers |
| `output/rq1_daily/report.md` | Findings, figures, sensitivity summaries and interpretation limits |

`extract_events`, `extract_litres` and `extract_distinct_trees` preserve raw
aggregated extract counts even on a date declared unavailable. Corresponding
outcome columns become missing on those dates. To supply a known outage
calendar, pass `--unavailable-dates path/to/dates.csv` with a unique date column.
This intentionally changes the analysis and output checksums. No outage file
was available for the default build. The pipeline does not infer outages from
zero logs. No date before platform launch is materialised as an observed zero.

Seasonal distinct trees are recomputed directly from tree IDs. Daily distinct
trees may be summed across disjoint areas on one day, but not across days to
obtain seasonal reach. The area metadata includes all current inventory trees;
no matched historical street-tree offset is claimed.

Tests independently check the daily HAC sandwich, calendar-gap handling,
dry-spell missingness and lag direction, local-date assignment, exact duplicate
removal, large-volume sensitivity, pre-launch exclusion, outage masking,
never-active areas, and conservation between city/area/canonical products.

The main matched street-tree hierarchical analysis, holidays, pump access,
spatial validation and formal stability contrasts remain future work. This
pilot does not create untouched hold-out seasons or establish causal effects.

## Release verification

The 26 October manifest extends the earlier package with explicitly selected
RQ1 files and updated active documentation. Existing seminar PDFs, maps and
September analysis tables are retained unchanged. Unrelated untracked local
authoring files are excluded. A future full-package build should review its
selection of untracked files before refreshing the manifest.
