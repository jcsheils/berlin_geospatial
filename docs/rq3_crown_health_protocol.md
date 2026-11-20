# RQ3 crown-health test: pre-specified plan, draft of 19 November 2026

**Status: draft.** This plan was written before any aerial image was opened for the analysis. It is frozen once its SHA-256 is recorded in `config/project.toml`, before any image is downloaded. Changes after the freeze go into a dated deviation note. Survival stays the primary RQ3 outcome ([four-year plan](rq3_four_year_survival_protocol.md)); crown health is the outcome that the data available now can test.

## Question

Did the crowns of young street trees first watered between August 2020 and August 2025 become greener than the crowns of comparable trees that were never watered? And can the data rule out a gain large enough to matter? Both answers are associations, not causal effects.

## Already seen before this plan

- All logs from 2020 to 2025, and the 2025 and 2026 inventories.
- The one-year removal test ([deviation note](rq3_one_year_survival_deviation.md)).
- Catalogue metadata for the aerial flights: dates, bands and download sizes.
- The projection below, built from the logs and the 2025 inventory.

No aerial image has been opened and no NDVI computed for any tree.

## Data

- **Images.** Three leaf-on flights with red, green, blue and near-infrared bands at 20 cm, from the Berlin geodata catalogue (2 km tiles, JPEG 2000):
  - 2–3 August 2015 (DOP20RGBI 2015), for the placebo test;
  - 1, 8, 12 and 16 August 2020 (TrueDOP20RGBI 2020, about 7 GB), the baseline;
  - 11–12 August 2025 (TrueDOP20RGBI Sommer 2025, about 19 GB), the outcome.

  A colour-only summer flight from 2023 (TrueDOP20RGB) serves one secondary analysis. Every other year was flown in spring, before full leaf-out.
- **Trees.** Positions (EPSG:25833), planting year and genus from the [2025 inventory](../data/raw/tree_inventory/snapshot_2025.json).
- **Logs.** The open export, cleaned as for the one-year test. It keeps the logs of every tree in the 2025 inventory.
- **Areas.** The 2021 planning areas (542).

## Design

- **Cohort.** Street trees in the 2025 inventory planted from 2005 to 2019 (aged 1–15 in 2020), inside a planning area, whose disc (below) lies inside both images. Trees planted in 2020 may postdate the flight and are excluded.
- **Watered.** At least one log between 17 August 2020 and 10 August 2025, and none before 17 August 2020.
- **Control.** No log before 11 August 2025.
- **Watered before the 2020 flight.** Excluded from the primary analysis, because their baseline already reflects some watering; added back in S4.
- **Outcome.** For each tree and flight, the mean NDVI of the pixels within 2 m of the inventory position, with NDVI = (near-infrared − red) / (near-infrared + red) from the delivered values. The primary outcome is the 2025 value minus the 2020 value.

**Why a fixed 2 m disc.** It holds a median young crown (7 m², a radius of 1.5 m) plus position error, and needs no crown diameter, which is missing for 28% of street trees. Its change reflects growth, vigour and loss of the crown together. A tree removed between the 2025 inventory and the August flight stays in, with whatever its disc shows.

## Comparison

- **Estimate.** A regression of the change on watering, with fixed effects for planning area and for planting year × genus group. The genus groups are those of the [four-year plan](rq3_four_year_survival_protocol.md). Planning-area effects absorb differences between flight days, tiles and neighbourhoods; planting year × genus absorbs growth curves.
- **Why not exact matching.** Exact strata of planning area × planting year × genus group would drop 384 of 1,972 watered trees (19%). They are a secondary analysis.
- **Inference.** A cluster bootstrap over planning areas: 5,000 resamples, seed 42, percentile intervals. The cluster-robust interval is reported alongside.

## Primary tests

The smallest effect of interest, Δ, is half the mean one-year gain in disc NDVI with age: five seasons of watering add at least half a year of crown growth. The design stage estimates the gain as the slope of disc NDVI on age among street trees aged 3–15 in the 2020 image, pooled over watering. If the slope is not positive, Δ is 0.2 standard deviations of the pooled change.

- **Test A, gain.** Watered crowns became greener if the two-sided 95% interval lies entirely above zero (α = 0.05).
- **Test B, gain smaller than Δ.** A gain of Δ or more is ruled out if the upper bound of the 90% interval lies below Δ (one-sided α = 0.05; Lakens et al., 2018).

The two null hypotheses, no gain and a gain of at least Δ, cannot both hold, so neither test needs a correction.

| 95% interval | Upper bound of the 90% interval | Report |
| --- | --- | --- |
| Above zero | Below Δ | Watered crowns became greener, by less than Δ |
| Above zero | At or above Δ | Watered crowns became greener; whether by Δ or more stays open |
| Includes zero | Below Δ | No gain detected; a gain of Δ or more is ruled out |
| Includes zero | At or above Δ | Inconclusive; report the largest gain the interval does not exclude |
| Below zero | Any | Watered crowns lost greenness; residents may water trees that look stressed |

## Selection checks

Both checks are pre-specified and bind the interpretation.

- **Placebo, 2015 to 2020.** The same regression on the 2015-to-2020 change, for cohort trees planted by 2014, compares trees later watered with trees never watered. The platform started in May 2020, so the expected difference is zero. If its 95% interval excludes zero in the direction of the primary result, the primary result is reported as likely selection. The primary estimate minus the placebo estimate is then reported for the trees in both.
- **Older trees, 16–40.** The same comparison for established trees, where the logged doses matter less. If their 95% interval excludes zero in the direction of the primary result, the same rule applies.

## Projected detectability

Projected from the 2025 inventory and the open export ([projection](../output/rq3_crown_health/projection.json)). Detectable differences are at 80% power, without and with a design effect of 2, in standard deviations of the residual change. The design stage converts them into NDVI units and computes the power of both tests.

| Analysis | Watered | Never watered | Detectable difference (residual SD) |
| --- | ---: | ---: | --- |
| Primary: watered between the flights | 1,972 | 48,441 | 0.07–0.10 |
| S3: three or more log days in a season | 737 | 48,441 | 0.11–0.15 |
| S3: logs in two or more seasons | 492 | 48,441 | 0.13–0.19 |
| S3: 500 L or more in a season | 167 | 48,441 | 0.22–0.31 |
| Placebo, planted by 2014 | 1,039 | 36,120 | 0.09–0.13 |
| Older trees, 16–40 | 2,523 | 176,742 | 0.06–0.08 |

Another 958 young trees were logged before the 2020 flight.

## Stages

1. **Check.** Runs without any comparison by watering. The test stops if any check fails:
   - each flight has four bands and the stated dates;
   - at least 98% of cohort discs lie inside both the 2020 and 2025 images;
   - in 200 discs drawn with seed 42 regardless of watering, at most 10% miss the tree by eye in the 2025 image.
2. **Design.** Builds the cohort and exposure, and writes Δ, the pooled standard deviation of the change, the detectable differences and the power of both tests.
3. **Outcome.** Runs only while this plan matches its recorded hash and the sample matches the design stage.

## Secondary analyses

These are reported with intervals and without significance claims.

- **S1. Crown core:** a 1 m disc.
- **S2. Wider disc:** a 3 m disc.
- **S3. Dose:** three or more log days in a season; logs in two or more seasons; 500 L or more in a season. Each is compared with never-watered trees.
- **S4.** Trees watered before the 2020 flight added to the watered group.
- **S5. Exact matching** within planning area × planting year × genus group.
- **S6. Adjusted level:** the 2025 value, adjusted for the 2020 value.
- **S7. After the 2022 drought:** the 2020-to-2023 change in the green share of the disc, G / (R + G + B), from the colour-only 2023 flight.
- **S8. Without survivor selection**, once CityLAB's 2020 tree table and full log history arrive: all trees standing in 2020, including those removed by 2025, whose discs then show the loss.

## Not done

- **Water content.** Water indices need shortwave infrared, which no aerial flight records and Sentinel-2 records only at 20 m.
- **Canopy temperature.** Thermal pixels are 70–100 m.
- **A yearly series.** Sentinel-2 (10 m) and PlanetScope (3 m) pixels are too coarse for young crowns. A Sentinel-2 test for trees older than 20 would need its own plan.
- No table of watering by single year of age or by municipal-care limit. The age slope that sets Δ pools ages 3–15 and is not split by watering.
- No covariates, outcomes or subgroups chosen after the images are opened. Any further analysis is labelled exploratory.

## Limits

- **Self-selection.** Residents choose which trees to water. The placebo and the older trees test for this; neither removes it.
- **Survivors only.** Trees removed before early 2025 are missing from the cohort. If watering saves weak trees, this biases the difference towards zero; S8 measures it.
- **Unlogged watering.** District crews, contractors and residents who do not log also water. This biases the difference towards zero.
- **Uncalibrated images.** The flights used different cameras and days. Fixed effects and the change design absorb shifts common to a planning area, not a flight-line boundary that crosses one.
- **The 2015 image is not a true orthophoto.** Crowns lean slightly away from the image centre; young trees are short, so the shift is small.
- **Small doses.** The median watered tree receives 60 L a season, about 1% of the rain on its crown ([benchmarks memo](policy_feedback_2026_11.md)).
- **Greenness is not survival.** A crown-health gain does not convert into avoided replacements by itself. RQ4 uses it to check whether the survival bounds are plausible.

## Reproduction

```bash
python -m analysis.rq3_crown_health_projection
```

This writes `output/rq3_crown_health/projection.json` and opens no image. The check, design and outcome stages are written after the freeze, before any image is opened.

Lakens, D., Scheel, A. M., and Isager, P. M. (2018). Equivalence testing for psychological research: A tutorial. *Advances in Methods and Practices in Psychological Science*, 1(2), 259–269. https://doi.org/10.1177/2515245918770963
