# RQ3 crown-health test: pre-specified plan, frozen on 24 November 2026

**Status: frozen on 24 November 2026**, before any aerial image was downloaded for the analysis. Its SHA-256 is recorded in `config/project.toml`, and the extraction and the stages refuse to run if the plan changes. Changes after the freeze go into a dated deviation note. Survival stays the primary RQ3 outcome ([four-year plan](rq3_four_year_survival_protocol.md)); crown health is the outcome that the data available now can test.

## Revision of 23 November 2026

The draft of 19 November was revised before any image was opened. Six changes:

1. **Outcome.** The greenness of sunlit vegetation pixels in the 2 m disc replaces the mean NDVI of the whole disc. Canopy fraction, shadow share and a 3–5 m background ring are recorded separately, so crown size and background no longer mix into the outcome.
2. **Consistency between flights.** Each flight gets its own thresholds from a fixed sample of windows. Stable surfaces (roofs, paving) are measured in every window, and never-watered older trees set a noise floor.
3. **Care.** An ordered level of care (never, occasional, repeated, sustained) replaces "any log" as the primary exposure. The primary estimate is the gain at sustained care implied by the trend. Any log becomes a secondary contrast.
4. **Population.** The population is stated as trees standing in the 2025 inventory, and the survivor bias is bounded under stated assumptions.
5. **Validity.** A check that never touches watering data asks whether a fall in greenness predicts removal a year later. If it does not, results are reported as greenness, not crown condition.
6. **Use.** The result enters RQ4 as a range ([analysis plan](analysis_plan.md)).

## Question

Did the crowns of young street trees that received more logged care between August 2020 and August 2025 become greener than those of comparable trees that were never watered? And can the data rule out a gain large enough to matter? Both answers are associations, not causal effects.

**Population.** Young street trees that stood in the 2025 inventory. Trees removed before early 2025 are missing, so the results describe survivors, not all trees planted (see S17 and S18).

## Already seen before this plan

- All logs from 2020 to 2025, and the 2025 and 2026 inventories.
- The one-year removal test ([deviation note](rq3_one_year_survival_deviation.md)).
- Catalogue metadata for the aerial flights: dates, bands, file formats and download sizes, and the layers and output formats of the map service.
- The projection below, built from the logs and the 2025 inventory, including the number of trees at each level of care.

No aerial image has been opened and no NDVI computed for any tree.

## Data

- **Images.** Three leaf-on flights at 20 cm with a near-infrared band, from the Berlin geodata catalogue:
  - 2–3 August 2015 (DOP20RGBI 2015), for the placebo test;
  - 1, 8, 12 and 16 August 2020 (TrueDOP20RGBI 2020), the baseline;
  - 11–12 August 2025 (TrueDOP20RGBI Sommer 2025), the outcome.

  All three are read through Berlin's map service (WMS, `https://gdi.berlin.de/services/wms/`) from each flight's colour-infrared layer (near-infrared, red, green), as lossless PNG on the native 20 cm grid. The bulk downloads deliver 2015 and 2020 only as ECW files, which open-source software cannot read, so the map service is the one route that reads every flight the same way. S16 compares the 2020 colour layer with that of a summer flight on 14–15 August 2023. The catalogue labels the 2023 flight both RGB and RGBI, but the map service has no infrared layer for it, so S16 uses colour either way. Other years were flown in spring, before full leaf-out.
- **Trees.** Positions (EPSG:25833), planting year and genus from the [2025 inventory](../data/raw/tree_inventory/snapshot_2025.json).
- **Logs.** The open export, cleaned as for the one-year test. It keeps the logs of every tree in the 2025 inventory.
- **Areas.** The 2021 planning areas (542).
- **Removals.** The 2026 inventory, for the validity check only.
- **Removal rates.** The one-year test's yearly removal risks (1.02% for watered and 1.23% for matched unwatered young trees), for the survivor bounds only.

## Measures

**Thresholds per flight.** Before it summarises any tree, the extraction reads 200 windows drawn with seed 42 from all windows of the flight.

- **Vegetation:** NDVI at or above the split of the sample's NDVI histogram that maximises the variance between the two classes (Otsu, 1979).
- **Shadow:** brightness below half the sample's median brightness. Brightness is the mean of the three served bands.

NDVI is (near-infrared − red) / (near-infrared + red) from the served values. Pixels with all three bands at zero lie outside the image and are left out.

**Regions.** Discs of 1, 2 and 3 m around each inventory position, and a background ring from 3 to 5 m.

**Per tree, region and flight:**

| Measure | Definition | Role |
| --- | --- | --- |
| Greenness | Mean NDVI of sunlit vegetation pixels | Primary outcome (2 m disc) |
| Canopy fraction | Share of pixels at or above the vegetation threshold | Crown size (S10); validity check |
| Shadow share | Share of pixels below the shadow threshold | S14 |
| Disc NDVI | Mean NDVI of all pixels | The draft of 19 November (S11) |

**Per window and flight:** the median near-infrared, red and NDVI of sunlit pixels without vegetation (stable surfaces: roofs and paving).

**Primary outcome.** Greenness of the 2 m disc in 2025 minus that in 2020.

**Why this outcome.** A fixed disc mixes crown condition with crown size, bare paving and soil. Greenness counts only vegetation pixels, so it does not rise just because a crown fills more of the disc; canopy fraction records that growth separately. Shadowed pixels have low values and noisy NDVI, so they are left out. The disc holds a median young crown (7 m², a radius of 1.5 m) plus position error, and needs no crown diameter, which is missing for 28% of street trees. Thresholds set per flight absorb differences in camera, date and rendering that shift all of a flight's values. A tree removed between the 2025 inventory and the August flight stays in, with whatever its disc shows.

## Care between the flights

Logs between 17 August 2020 and 10 August 2025. A season runs from April to September.

| Level | Definition |
| --- | --- |
| 0 Never | No log before 11 August 2025 |
| 1 Occasional | Any log between the flights, not repeated or sustained |
| 2 Repeated | Three or more log days in one season, or logs in two seasons |
| 3 Sustained | Logs in three or more seasons |

Trees with a log before 17 August 2020 are excluded from the primary analysis, because their baseline already reflects some care; S7 adds them back.

## Cohort

Street trees in the 2025 inventory planted from 2005 to 2019 (aged 1–15 in 2020), inside a planning area, whose 2 m disc lies inside both images. Trees planted in 2020 may postdate the flight and are excluded.

## Comparison

- **Estimate.** A regression of the change on the level of care (0–3), with fixed effects for planning area and for planting year × genus group. The genus groups are those of the [four-year plan](rq3_four_year_survival_protocol.md). Planning-area effects absorb differences between flight days, tiles and neighbourhoods; planting year × genus absorbs growth curves. The primary estimate, G, is the gain from no care to sustained care that the trend implies: three times the coefficient.
- **Why a trend.** Sustained care alone covers 174 trees. The trend uses all 1,972 trees with care and asks whether more care goes with more greenness, which is what persistence of care should show. S3 reports each level separately, so a gain carried by occasional care alone is visible.
- **Inference.** A cluster bootstrap over planning areas: 5,000 resamples, seed 42, percentile intervals. The cluster-robust interval is reported alongside.

## Primary tests

The smallest effect of interest, Δ, is half the mean one-year gain in greenness with age: five seasons of sustained care add at least half a year of crown development. The design stage estimates the gain as the slope of 2 m greenness on age among street trees aged 3–15 in the 2020 image, pooled over care. If the slope is not positive, Δ is 0.2 standard deviations of the pooled change.

- **Test A, gain.** More care went with greener crowns if the two-sided 95% interval for G lies entirely above zero (α = 0.05).
- **Test B, gain smaller than Δ.** A gain of Δ or more at sustained care is ruled out if the upper bound of the 90% interval for G lies below Δ (one-sided α = 0.05; Lakens et al., 2018).

The two null hypotheses, no gain and a gain of at least Δ, cannot both hold, so neither test needs a correction.

| 95% interval | Upper bound of the 90% interval | Report |
| --- | --- | --- |
| Above zero | Below Δ | More care went with greener crowns, by less than Δ at sustained care |
| Above zero | At or above Δ | More care went with greener crowns; whether by Δ or more stays open |
| Includes zero | Below Δ | No gain detected; a gain of Δ or more at sustained care is ruled out |
| Includes zero | At or above Δ | Inconclusive; report the largest gain the interval does not exclude |
| Below zero | Any | More care went with less green crowns; residents may water trees that look stressed |

## Validity of the outcome

The design stage asks, before any comparison by care, whether greenness tracks crown condition. It uses no watering data.

- **Trees.** Cohort trees whose 2 m discs lie inside both images and still show a crown in 2025 (canopy fraction of at least 0.1). Discs that are already bare are left out, because a tree felled before the flight would trivially look bare.
- **Outcome.** Removal: the identifier is absent from the 2026 inventory and was not re-keyed.
- **Model.** A linear probability model of removal on the standardised 2020-to-2025 change in greenness, with the primary fixed effects and a cluster-robust interval. The same model is reported for the change in canopy fraction and for 2025 greenness, with the area under the curve for each.
- **Rule.** The check passes if at least 30 trees were removed and the 95% interval for greenness change lies below zero, so that a fall in greenness goes with removal. If it fails, the outcome stage still runs, but every result is reported as crown greenness, not crown condition.

Removals include planned fellings, which dilute the link; felling reasons are requested from the districts. Colour-infrared vitality ratings from the Senate environment department, if received, are compared descriptively and do not change the rule.

## Consistency between flights

- **Check stage, without logs.** The thresholds of each flight. For 2015 to 2020 and 2020 to 2025: the median and interquartile range across windows of the shift in stable-surface NDVI, and its rank correlation with the window's mean change in young-tree greenness.
- **Design stage.** The noise floor: the residual standard deviation of the greenness change among never-watered trees aged 16–40.
- **Outcome stage.** S13 adds each window's stable-surface shift to the primary model as a covariate.

## Selection checks

Both checks are pre-specified and bind the interpretation.

- **Placebo, 2015 to 2020.** The same trend regression on the 2015-to-2020 change, for cohort trees planted by 2014, with care measured between 2020 and 2025. The platform started in May 2020, so the expected trend is zero. If its 95% interval excludes zero in the direction of the primary result, the primary result is reported as likely selection. The primary estimate minus the placebo estimate is then reported for the trees in both.
- **Older trees, 16–40.** The same trend for established trees, where the logged doses matter less. If their 95% interval excludes zero in the direction of the primary result, the same rule applies.

## Survivor bounds (S17)

If trees removed before 2025 had been observed, the primary estimate would be about

G_full = G (1 − r_c) + (r_n − r_c)(m_n − L),

where r_c and r_n are the five-year shares removed among cared-for and never-watered trees, m_n is the never-watered mean change and L is the change a removed tree would show. The formula treats G as a difference between two groups, so it is approximate for the trend.

- **Shares.** The one-year risks compounded over five years (5.0% cared-for, 6.0% never watered), the same two swapped, and both at 6.0%.
- **Removed trees' change.** The 1st percentile and the median of the never-watered change.

The six combinations give a range for G and its interval. S18 replaces the assumptions with observations once CityLAB's 2020 tree table and full log history arrive.

## Projected detectability

Projected from the 2025 inventory and the open export ([projection](../output/rq3_crown_health/projection.json)). Detectable differences are at 80% power, without and with a design effect of 2, in standard deviations of the residual change. For the trend they refer to the gain at sustained care. The design stage converts them into greenness units and computes the power of both tests.

| Analysis | Trees with care | Never watered | Detectable difference (residual SD) |
| --- | ---: | ---: | --- |
| Primary: trend over levels of care | 1,064 occasional, 734 repeated, 174 sustained | 48,441 | 0.12–0.17 |
| S3: occasional | 1,064 | 48,441 | 0.09–0.13 |
| S3: repeated | 734 | 48,441 | 0.11–0.15 |
| S3: sustained | 174 | 48,441 | 0.22–0.31 |
| S4: any log between the flights | 1,972 | 48,441 | 0.07–0.10 |
| S5: 500 L or more in a season | 167 | 48,441 | 0.22–0.31 |
| S6: logs in the 2022 season | 884 | 48,441 | 0.10–0.14 |
| Placebo (2015–2020) and S15 (2020–2025): planted by 2014 | 577, 368, 94 | 36,120 | 0.17–0.24 |
| Older trees, 16–40 | 1,575, 793, 155 | 176,742 | 0.11–0.16 |

Another 958 young trees were logged before the 2020 flight. The trend detects less than the any-log contrast did; that is the price of putting persistence first.

## Stages

1. **Check.** Runs without logs. The test stops if any check fails:
   - every response is a three-band image of the requested size;
   - in 50 windows per infrared flight drawn with seed 42, the red and green bands of the colour-infrared layer match those of the colour layer (median absolute difference of at most 2 on the 0–255 scale), which confirms the band order and shows that neither layer was stretched on its own;
   - every infrared flight has its thresholds, the same in every shard;
   - at least 98% of cohort discs lie fully inside both the 2020 and 2025 images;
   - in 200 discs drawn with seed 42 regardless of watering, at most 10% miss the tree by eye in the 2025 image.

   It also records the consistency between flights.
2. **Design.** Builds the cohort and levels of care, runs the validity check, and writes Δ, the noise floor, the pooled standard deviation of the change, the detectable differences and the power of both tests.
3. **Outcome.** Runs only while this plan matches its recorded hash and the sample matches the design stage.

## Secondary analyses

These are reported with intervals and without significance claims. Unless stated, they use the primary trend and outcome.

- **S1. Crown core:** a 1 m disc.
- **S2. Wider disc:** a 3 m disc.
- **S3. Levels:** occasional, repeated and sustained care, each against never-watered trees.
- **S4. Any log** between the flights against never-watered trees (the earlier primary contrast).
- **S5. Volume:** 500 L or more in a season.
- **S6. Timing:** logs in the dry 2022 season.
- **S7.** Trees watered before the 2020 flight added; any log against never.
- **S8. Exact matching** within planning area × planting year × genus group; any log against never.
- **S9. Adjusted level:** 2025 greenness, adjusted for 2020 greenness. With the change score, it brackets the association under standard assumptions (Angrist and Pischke, 2009, section 5.4).
- **S10. Canopy fraction** of the 2 m disc: crown size.
- **S11. Disc NDVI:** the mean of all pixels in the 2 m disc, as in the draft of 19 November.
- **S12. Background:** the change in greenness minus that of the 3–5 m ring.
- **S13. Stable surfaces:** the window's shift in stable-surface NDVI as a covariate.
- **S14. Without shaded discs:** discs with at most half their pixels in shadow in both years.
- **S15. Crowns over the tree pit:** trees planted by 2014, whose crowns had at least six seasons to grow over the pit by 2020. These are the placebo trees, so S15 and the placebo compare the same trees in two periods.
- **S16. After the 2022 drought:** the 2020-to-2023 change in the green share of the disc, G / (R + G + B), from the two colour layers. Care means a first log between 17 August 2020 and 13 August 2023; the controls are the never-watered trees of the primary analysis.
- **S17. Survivor bounds** (above).
- **S18. Without survivor selection**, once CityLAB's 2020 tree table and full log history arrive: all trees standing in 2020, including those removed by 2025, whose discs then show the loss.

## Use in RQ4

RQ4 ranks where support for volunteer watering would do most under a fixed budget. It takes the effect of care as a range, not a point: the primary interval, widened by the survivor bounds, alongside the survival intervals. If the ranking is the same across that range, the decision does not depend on RQ3. If the validity check fails, crown greenness does not enter RQ4's survival range.

## Not done

- **Water content.** Water indices need shortwave infrared, which no aerial flight records and Sentinel-2 records only at 20 m.
- **Canopy temperature.** Thermal pixels are 70–100 m.
- **A yearly series.** Sentinel-2 (10 m) and PlanetScope (3 m) pixels are too coarse for young crowns. A Sentinel-2 test for trees older than 20 would need its own plan.
- **Delivered files.** A comparison of served values with the delivered 2025 JPEG 2000 tiles is not part of this plan.
- No table of watering by single year of age or by municipal-care limit. The age slope that sets Δ pools ages 3–15 and is not split by watering.
- No covariates, outcomes or subgroups chosen after the images are opened. Any further analysis is labelled exploratory.

## Limits

- **Self-selection.** Residents choose which trees to water. The placebo and the older trees test for this; neither removes it. Residents who water more may also choose differently, so a rising trend does not remove selection either.
- **Survivors only.** Trees removed before early 2025 are missing from the cohort. If watering saves weak trees, this biases the difference towards zero. S17 bounds it under assumptions; S18 measures it.
- **Unlogged watering.** District crews, contractors and residents who do not log also water. This biases the difference towards zero.
- **Uncalibrated images.** The flights used different cameras and days. Thresholds per flight, fixed effects and the change design absorb shifts common to a flight or a planning area, not a flight-line boundary that crosses one. The stable surfaces show how large such shifts are.
- **Thresholds.** A pixel near the vegetation threshold can change class between flights without any change in the tree. This adds noise to canopy fraction more than to greenness, which is why canopy fraction is secondary.
- **Served images.** The map service may render values that differ from the delivered files. The check confirms the band order and equal values across its two layers; it cannot detect a stretch applied to both. Thresholds per flight absorb a stretch that is the same across the flight.
- **Tree-pit vegetation.** Grass and weeds in the pit are vegetation pixels too. If residents water the pit, that vegetation stays green in a dry August, and part of a gain may come from the ground under the tree. The bias is largest for the newest trees, whose crowns do not yet cover the pit; S15 leaves them out.
- **The 2015 image is not a true orthophoto.** Crowns lean slightly away from the image centre; young trees are short, so the shift is small.
- **Small doses.** The median watered tree receives 60 L a season, about 1% of the rain on its crown ([benchmarks memo](policy_feedback_2026_11.md)). Sustained care covers 174 young trees.
- **Greenness is not survival.** The validity check links the two only through removal a year later, which includes planned fellings.

## Reproduction

```bash
python -m analysis.rq3_crown_health_projection
```

This writes `output/rq3_crown_health/projection.json` and opens no image.

**Extraction.** The images are read on GitHub Actions ([workflow](../.github/workflows/rq3-crown-health.yml)), started by hand for one flight at a time, so no image passes through a local machine.

- **Windows.** Each cohort tree falls in one 50 m cell; the request for a cell covers the 5 m rings of its trees, snapped outward to the 20 cm grid. Street trees planted from 1980 to 2019 (about 232,000) fill about 65,000 windows, roughly 3.7 GB per flight.
- **Thresholds.** Every shard first reads the same 200 sampled windows and sets the flight's thresholds; combining the shards stops if they differ.
- **Load on the service.** Six shards, at most two at once, each at most three requests a second, about an hour per shard.
- **Kept.** For each tree and region, the pixel counts and the measures above; for each window, the SHA-256 of the response and its stable-surface values. No image is stored.
- **Blind.** The extraction holds no watering data. The tables it writes are joined to the logs only in the design and outcome stages.
- **Freeze guard.** It refuses to start unless this plan matches its hash in `config/project.toml`.

```bash
python -m analysis.rq3_crown_health_extract plan
```

This counts the windows without network access. The workflow has three tasks: `extract` reads the three infrared layers and, for S16, the 2020 and 2023 colour layers; `crosscheck` compares the layers of each infrared flight; `chips` draws the eye-check sample. The combined tables go into `data/processed/rq3_crown_health/`, with the eye-check sheet filled in by hand (`on_tree`: yes or no).

**Stages.** These run locally on the combined tables. The design stage also needs the 2026 inventory (`python tools/restore_tree_inventory.py`).

```bash
python -m analysis.rq3_crown_health_test check
python -m analysis.rq3_crown_health_test design
python -m analysis.rq3_crown_health_test outcome
```

They write `check.json`, `design.json` and `outcome.json` to `output/rq3_crown_health/`. Each stage runs only after the one before it, and the outcome stage stops if the plan or any sample changed since the design stage. The extraction and the stages were written and tested on synthetic data before the freeze; any later fix goes into a dated deviation note.

## References

Angrist, J. D., and Pischke, J.-S. (2009). *Mostly Harmless Econometrics.* Princeton University Press.

Lakens, D., Scheel, A. M., and Isager, P. M. (2018). Equivalence testing for psychological research: A tutorial. *Advances in Methods and Practices in Psychological Science*, 1(2), 259–269. https://doi.org/10.1177/2515245918770963

Otsu, N. (1979). A threshold selection method from gray-level histograms. *IEEE Transactions on Systems, Man, and Cybernetics*, 9(1), 62–66. https://doi.org/10.1109/TSMC.1979.4310076
