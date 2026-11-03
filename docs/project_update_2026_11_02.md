# Project update — 2 November 2026

The active project is **Spatiotemporal Modeling of Citizen Tree Watering in Berlin: Weather Responses and Neighborhood Variation**. The refined 26 October design has four questions. The [active analysis plan](analysis_plan.md) describes them in the repository; the examination package preserves the earlier seminar design and evidence.

## RQ1: first daily results

The [daily pilot](../output/rq1_daily/report.md) constructs a balanced 542-area × 1,051-day April–September panel: **569,642 area-days and 55,634 linked events**. The partial 2020 season starts on 18 May. The all-month foundation, used by the atlas, has **57,786 events and 2,249,502 recorded litres** over May 2020–December 2025. These are different inclusion windows, not conflicting totals.

Citywide exploratory OLS models use log(1 + daily events), log(1 + daily litres), or log(1 + daily distinct trees), calendar controls and actual-calendar-day HAC uncertainty. In the baseline event model, temperature (+5°C) is associated with +0.501 log1p units (approximate 95% interval 0.422–0.580); an antecedent dry spell (+7 days) with +0.451 (0.343–0.558); current rainfall (+10 mm) with −0.340 (−0.519 to −0.161). These are descriptive adjusted associations, not causal effects or exact percentage changes in mean counts.

All six annual temperature estimates are positive, with varying magnitudes. Annual overdispersion and 92–98% zero area-days motivate hierarchical count and two-part volume models. The full coefficient grid, annual sample audit, inclusion audit, figures and source hashes accompany the report. See [protocol](rq1_daily_exploratory_protocol.md) and [reproduction instructions](rq1_daily_reproduction.md).

## Interactive atlas

The [Earth Engine demo](../earth_engine/README.md) includes monthly events and litres, events per 1,000 current inventory trees, pooled distinct-tree reach, static social status, clickable area histories, daily citywide RQ1 charts, and live Landsat 8/9 monthly surface temperature with scene-count coverage.

The demo embeds aggregated data and simplified LOR geometry. Satellite temperature is environmental context, distinct from the station air temperature in RQ1. Static social context is not historical monthly vulnerability. No inferred local climate-response slopes or municipal allocation recommendations are displayed. Live Earth Engine execution and App publication remain pending.

## Next research steps

| Question | Current position | Next step |
| --- | --- | --- |
| RQ1: climate response | Daily citywide exploratory fits, balanced panel and sensitivity grid | Audit platform coverage, match street-tree denominators, add participation/calendar covariates and fit hierarchical count / two-part volume models |
| RQ2: inequality | Descriptive social/environmental context and recorded-care summaries | Audit pump access and matched stock; estimate adjusted comparisons |
| RQ3: added spatial information | Spatial descriptions and candidate discordance | Define separate information layers; test incremental prediction with temporal/spatial validation |
| RQ4: allocation consequences | Scenario design remains planned | Equal-budget comparisons, reporting sensitivities and explicit minimum-public-care safeguards |

Logs are platform activity, not all watering. Current inventory is not historical stock. Missing rain is not zero rain, and a dry spell is not measured tree stress. All 2020–2025 seasons have already been inspected; later validation on these years is retrospective.

## Validation

The 52-test Python suite passed on 2 November 2026, including independent daily HAC, lag/missingness, duplicate handling, outage masking and reconciliation checks. The atlas builder verifies area/month coverage and canonical monthly totals; generated JavaScript syntax has been checked. Release checksums and local documentation links are verified separately before publishing this update. Existing seminar artifacts remain unchanged.
