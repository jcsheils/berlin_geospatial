# RQ3 four-year survival test: pre-specified plan, draft of 18 November 2026

**Status: draft.** This plan was written before any tree table from 2020–2024 was available. It is frozen once its SHA-256 is recorded in `config/project.toml` and it is lodged on OSF, both before CityLAB's data arrive. Changes after the freeze go into a dated deviation note. This is the main RQ3 test; the [one-year test](rq3_one_year_survival_protocol.md) was preliminary.

## Question

Among young street trees standing in one yearly tree table, were trees with logged citizen watering in earlier seasons removed from the cadastre by the next table less often than comparable trees that were never logged? And can the data rule out a reduction large enough to matter for policy? Both answers are associations, not causal effects.

## Already seen before this plan

- All logs from 2020 to 2025 (RQ1 work, and the open export to 30 April 2026).
- The 2025 and 2026 inventories, and removal rates 2025–2026 overall, by age band and by district.
- The one-year test of watering and removal 2025–2026: a void first run, a corrected run (−0.21 points; 95% interval −0.86 to 0.40; trees aged 16–40: −0.30) and the 117 logged trees absent in 2026 ([deviation note](rq3_one_year_survival_deviation.md)).
- The projection below, built from the logs and the 2025 inventory without any removal.

No tree table from 2020–2024 has been seen, and no removal before 2025. So the 2025–2026 interval stays out of the primary analysis. The smallest effect of interest below was proposed on 9 November in the [revised research design](revised_research_design_2026_11.md), before the one-year test ran.

## Data

- **Tree tables.** CityLAB's yearly imports for 2020–2024 (requested on 18 November 2026) and for 2025 (not yet requested). Without the 2025 import, the [2025 extract](../data/raw/tree_inventory/snapshot_2025.json) takes its place, subject to the completeness check below. A table's reference date is the cadastre date where CityLAB supplies one, otherwise the import date.
- **Logs.** CityLAB's full log history, including logs of trees the platform has deleted. It is cleaned as the open export is: exact duplicates removed, Europe/Berlin dates from 18 May 2020, positive litres, April–September only. It is never matched against a later tree table.
- **Deleted identifiers.** The identifiers each import deleted, with import dates.
- **Areas.** The 2021 planning areas (542) and Bezirksregionen (143).

## Design

- **Landmarks.** Every tree table with at least one complete April–September season before its reference date is a landmark; the next table is its outcome table. Yearly tables give four intervals: 2021–2022, 2022–2023, 2023–2024 and 2024–2025.
- **At risk.** Street trees in the landmark table with a planting year, aged 0–15 in the landmark year and inside a planning area. A tree enters every interval it is standing for.
- **Exposure.** Watered: at least one log in a complete season before the landmark's reference date, under the tree's identifier or an identifier it was re-keyed from. Control: no log before that date. Logs from the season inside the follow-up are not used.
- **Outcome.** Removed: the identifier is absent from the outcome table and the tree was not re-keyed. Re-keyed means a tree in the outcome table with a new identifier within 1 m, of the same genus and planting year. A tree replanted on the same site counts as removed.

**Why exposure ends before the landmark.** The revised research design started exposure after the earlier table. A tree felled before or during that season cannot be watered, so that design credits watering with survival. Federal law bars most felling from March to September (§ 39(5) BNatSchG), so removals cluster in winter, and the tables' reference dates are not yet known. Here all exposure precedes the landmark, and a later removal cannot change it.

## Comparison

- **Strata.** Exact matching on interval × district (12) × planting year × genus group. The groups are the ten most common genera among young street trees in the 2025 inventory (Tilia, Acer, Ulmus, Quercus, Carpinus, Prunus, Liquidambar, Fraxinus, Corylus, Aesculus) and the rest pooled. Strata without both a watered and a control tree drop out.
- **Why districts.** District offices decide removals, and removal rates differed more than fivefold between districts in 2025–2026 (0.57–3.26%). Matching within Bezirksregion or planning area drops 7–18% of watered tree-years and raises the detectable difference by 28–36% in the projection. Both are secondary analyses.
- **Estimate.** Risk difference in removal, watered minus matched controls, in percentage points. Controls are weighted so each stratum counts in proportion to its watered trees, which also pools the intervals by their watered trees. An interval shorter than 9 months or longer than 15 has its outcomes divided by its length in years. The result is a yearly risk difference; four times it approximates the four-year difference.
- **Inference.** A cluster bootstrap over planning areas, which also covers trees that enter several intervals: 5,000 resamples, seed 42, percentile intervals. The linearised interval is reported alongside.

## Primary tests

The smallest effect of interest, Δ, is a fall in removal risk of 0.5 points a year: a third of the 1.51% risk of young street trees in 2025–2026, or about 2 points over four years.

- **Test A, reduction.** Watered trees were removed less often if the two-sided 95% interval lies entirely below zero (α = 0.05).
- **Test B, reduction smaller than Δ.** A reduction of Δ or more is ruled out if the lower bound of the 90% interval lies above −Δ (one-sided α = 0.05; Lakens et al., 2018).

The two null hypotheses, no reduction and a reduction of at least Δ, cannot both hold, so neither test needs a correction.

| 95% interval | Lower bound of the 90% interval | Report |
| --- | --- | --- |
| Below zero | Above −Δ | Watered trees were removed less often, by less than Δ |
| Below zero | At or below −Δ | Watered trees were removed less often; whether by Δ or more stays open |
| Includes zero | Above −Δ | No reduction detected; a reduction of Δ or more is ruled out |
| Includes zero | At or below −Δ | Inconclusive; report the largest reduction the interval does not exclude |
| Above zero | Any | Watered trees were removed more often; residents may water trees that look stressed |

**Negative control.** Watering should matter less for trees aged 16–40. If their gap has the same sign and its 95% interval excludes zero, the young-tree result is reported as likely reflecting selection or the data, whatever its significance, together with the difference between the two gaps.

## Projected detectability

Projected from the 2025 inventory and the open export ([projection](../output/rq3_four_year_survival/projection.json)). Both miss trees removed before 2025, so the counts are lower bounds. The design stage replaces them.

| Analysis | Watered tree-years | Without control | Detectable difference (points a year) |
| --- | ---: | ---: | --- |
| Primary: any earlier log, age 0–15 | 6,516 | 39 | 0.47–0.66 |
| S2: three or more log days in a season | 2,460 | 0 | 0.72–1.02 |
| S2: logs in two or more seasons | 1,034 | 10 | 1.12–1.58 |
| S2: 500 L or more in a season | 552 | 0 | 1.51–2.13 |
| S3: older trees, age 16–40 | 11,166 | 54 | 0.35–0.49 |
| S4: matched within Bezirksregion | 6,076 | 479 | 0.60–0.85 |
| S5: matched within planning area | 5,408 | 1,147 | 0.64–0.90 |
| S6: logged in the last season | 3,245 | 21 | 0.64–0.91 |

Detectable differences are at 80% power, without and with a design effect of 2, at the 2025–2026 removal risk (1.51% for ages 0–15, 1.58% for 16–40). In the primary analysis, test A has 57–85% power if watering cuts removal by Δ, and test B has 68–91% power if watering makes no difference. A difference of 0.59–0.82 points between the young and older gaps is detectable.

## Stages

1. **Check.** Runs on the delivered data without comparing exposure and outcome. The test stops, and CityLAB is asked, if any check fails:
   - every table has an import date, and the tables are in date order;
   - at least 99% of the open export's cleaned logs appear in the full history;
   - at least 99% of logs resolve to an identifier in some table or deleted-identifier list;
   - CityLAB confirms that deleting a tree keeps its logs. A masked check then counts, per interval, watered trees absent from the outcome table, and prints only whether the count reaches 10% of what the pooled removal risk predicts. A count of zero, the signature of the void one-year run, fails;
   - if the 2025 table is the extract, the pooled share of 2024 street trees absent from it must lie within the range of the earlier intervals. Otherwise the 2024–2025 interval drops.
2. **Design.** Builds cohorts, exposure and strata, and writes the pooled removal risk per interval (not split by watering), the detectable differences and the power of both tests.
3. **Outcome.** Runs only while this plan matches its recorded hash and the sample matches the design stage.

## Secondary analyses

These are reported with intervals and without significance claims.

- **S1.** Outcome without the re-key correction: any identifier absent from the outcome table.
- **S2. Dose.** Three or more log days in a season; logs in two or more seasons; 500 L or more in a season. Each is compared with never-logged trees.
- **S3. Older trees** (16–40), and the difference between the young and older gaps.
- **S4, S5. Local matching** within Bezirksregion, and within planning area as the analysis plan first proposed.
- **S6. Recent care:** logged in the season just before the landmark.
- **S7. Dry season:** the interval whose follow-up contains the 2022 season, against the others.
- **S8.** The 2025–2026 interval added, although it is not blind.
- **S9. Removal reasons**, if felling records are obtained: deaths and damage against planned removals. Watering cannot prevent a removal for construction, so planned removals serve as a negative-control outcome.

## Use in RQ4

The 95% interval bounds avoided removals per watered tree and year, and RQ4 carries the whole interval, not the point estimate. In the projection, Δ equals about 8 avoided removals a year among the 1,600 young trees with logged care per landmark, or €24,000 at €3,000 per replacement. Once CityLAB reports platform and campaign costs, the break-even reduction is set against the interval without a further test: costs minus the water's replacement value, divided by watered young trees × €3,000.

## If the data fall short

- **Fewer tables.** The same rules apply to each consecutive pair, and longer intervals are scaled to a year.
- **No logs of deleted trees.** The test does not run.
- **No tables.** The four-year test does not run, and RQ3 reports the one-year bounds.

## Not done

- No table of watering or removal by single year of age or by municipal-care limit. The pump and care-limit versions of the survival test get their own plans.
- No exposure from the season inside the follow-up.
- No covariates, outcomes or subgroups chosen after the data arrive. Any further analysis is labelled exploratory.

## Limits

- **Self-selection.** Residents choose which trees to water. Matching cannot remove this; S3 and S9 test for it.
- **Unlogged watering.** Residents who do not log, district crews and contractors also water. This biases the difference towards zero.
- **Removal is not death.** Trees are also removed for construction or safety, and dead trees may stay listed for a while.
- **Identifier changes.** Trees re-keyed and moved by more than 1 m count as removed; S1 shows how much the correction matters.
- **Timing.** A tree that dies in the season just before a landmark and is removed before it falls in the previous interval, where its exposure is one season older.

## Reproduction

```bash
python -m analysis.rq3_four_year_projection
```

This writes `output/rq3_four_year_survival/projection.json` and opens no removal data. The check, design and outcome stages are written once the data's format is known, before any outcome is opened.

Lakens, D., Scheel, A. M., and Isager, P. M. (2018). Equivalence testing for psychological research: A tutorial. *Advances in Methods and Practices in Psychological Science*, 1(2), 259–269. https://doi.org/10.1177/2515245918770963
