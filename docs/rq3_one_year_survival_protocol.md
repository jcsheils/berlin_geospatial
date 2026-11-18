# RQ3 one-year survival test: registration, 17 November 2026

This protocol was fixed before any tree removal was compared by watering status. Its SHA-256 is recorded in `config/project.toml`, and the outcome stage of [`analysis/rq3_one_year_survival.py`](../analysis/rq3_one_year_survival.py) refuses to run unless the file is unchanged. The registration date is that of the commit that adds the protocol to the public repository.

It is a preliminary test on one year of data. The four-year survival design in the [analysis plan](analysis_plan.md) remains the main RQ3 test and is registered separately once the 2020–2024 inventories are available. If that design ends with the 2025 inventory, the two tests share no outcomes.

## Already seen before registration

- Removal rates for all street trees from 2025 to 2026, overall, by age band and by district ([benchmarks](../output/feedback_benchmarks/benchmarks.json), `inventory_ids_2025_to_2026`). None is split by watering.
- The design-stage output below, which uses the 2025 inventory and the logs, but not the 2026 inventory.
- That all but one logged tree are in the 2025 inventory (see the assumption below).

## Question

Among young street trees standing in early 2025, were trees with logged citizen watering in 2020–2024 removed from the tree cadastre by 2026 less often than comparable trees without logs? The answer is an association, not a causal effect.

## Data

- **Cohort.** Street trees in the [2025 inventory](../data/raw/tree_inventory/snapshot_2025.json) with planting year 2010–2025 (age 0–15 in 2025): 47,069 trees. Trees outside the 2021 planning areas are excluded (28 trees of all ages).
- **Exposure.** At least one April–September log in 2020–2024 in the tree-day product (`data/processed/temporal/recorded_tree_day_watering_2020_2025.csv`). Logs from 2025 are not used: a tree removed during 2025 cannot be watered afterwards, which would make watering look protective.
- **Outcome.** Removed: the tree's identifier is absent from the 2026 inventory (962,545 rows; hash in [`snapshot.json`](../data/raw/tree_inventory/snapshot.json)) and the tree was not re-keyed. Re-keyed means a 2026 tree with a new identifier within 1 m, of the same genus and planting year. A tree replanted on the same site counts as removed.

## Assumption the test rests on

The log export ends on 30 April 2026. Of its 11,278 tree identifiers, all but one (a single 2022 log) are in the 2025 inventory. These include the 108 trees logged in March–April 2026, so none is a tree added in 2026. So the platform was still using its 2025 tree table when the export was made. Logs of trees removed between 2025 and 2026 should therefore still be in the export. Logs of trees deleted before 2025 are missing, which does not affect a cohort alive in 2025.

This will be confirmed with CityLAB: the date of the 2026 tree import, and whether logs are deleted together with a tree. If the export postdates that import, or logs of trees removed in this window were deleted, the test is void and is not reported as evidence.

## Comparison

- **Strata.** Exact matching on district (12) × planting year × genus group (the 10 most common genera among young street trees, others pooled). Strata without both a watered and an unwatered tree drop out.
- **Estimate.** Risk difference in removal, watered minus matched controls, in percentage points. Controls are weighted so each stratum counts in proportion to its watered trees.
- **Inference.** Two-sided 95% confidence interval from the linearised variance, clustered by planning area (542). Significance level 0.05. Only the primary analysis carries a significance claim.

## Fixed sample (design stage)

| Analysis | Watered | Without control | Controls | Effective controls | Detectable difference (pp) |
| --- | ---: | ---: | ---: | ---: | --- |
| Primary: any log 2020–2024, age 0–15 | 2,145 | 13 | 25,655 | 8,139 | 0.83–1.17 |
| S2: 500 L or more in one season | 217 | 0 | 7,757 | 2,433 | 2.42–3.42 |
| S3: older trees, age 16–40 | 3,820 | 16 | 98,506 | 32,068 | 0.60–0.85 |
| S4: matched within planning area | 1,974 | 184 | 12,882 | 3,257 | 0.97–1.38 |

Detectable differences are at 80% power, without and with a design effect of 2, at the overall removal risk (1.51% for ages 0–15, 1.58% for 16–40). The outcome stage stops if the sample differs from this table.

## Detectability and interpretation

The primary test can detect a fall in removal risk of about 55–78%. A reduction of a third (0.5 points) would matter for policy but lies below what the test can detect. The 2025–2026 removal rate was far lower than the 3.5–5.1% that earlier benchmarks assumed, which is why the detectable difference is so large.

- **Interval entirely below zero:** watered trees were removed less often than comparable unwatered trees. Report as an association; it does not establish that watering caused survival.
- **Interval entirely above zero:** watered trees were removed more often. Report it, noting that residents may water trees that already look stressed.
- **Interval includes zero:** inconclusive. Report the interval and the largest reduction it does not exclude, never "no effect".

## Secondary analyses

These are reported with intervals and without significance claims.

- **S1. Outcome without the re-key correction:** any identifier absent from the 2026 inventory.
- **S2. Dose:** trees that received 500 L or more in at least one season, against unwatered trees. Too few trees for anything but large differences.
- **S3. Older trees (16–40):** the same comparison for established trees, where watering should matter less. A difference as large as the primary one points to selection or to the data rather than to watering.
- **S4. Local matching:** strata of planning area × planting year, following the analysis plan's matching for the four-year test. The primary analysis matches within districts because local strata drop 184 watered trees and raise the detectable difference to about 1–1.4 points.

## Not done

- No table of watering or removal by single year of age or by municipal-care limit. Those belong to the age-limit test, registered separately.
- No covariates, outcome definitions or subgroups chosen after seeing results. Any further analysis is labelled exploratory.

## Limits

- **Self-selection.** Residents choose which trees to water, for example near their homes or trees that look stressed. Matching on district, planting year and genus cannot remove this.
- **Unlogged watering.** Residents who do not log, district crews and contractors also water. Some controls were watered, which biases the difference towards zero.
- **Removal is not death.** Trees are also removed for construction or traffic safety, and dead trees may stay listed for a while. Felling reasons are not available.
- **One year, survivors only.** Only trees alive in early 2025 enter, and only one year of removals is observed.
- **Third-party 2025 inventory.** The archive holds about 39,500 fewer trees than the platform's 2025 import.

## Reproduction

```bash
python -m analysis.rq3_one_year_survival design
python -m analysis.rq3_one_year_survival outcome --inventory /path/to/Berlin_trees.gpkg
```

The design stage writes `output/rq3_one_year_survival/design.json` and opens no outcome data. The outcome stage writes `outcome.json` after checking the protocol hash and the sample.
