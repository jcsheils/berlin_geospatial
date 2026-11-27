# Analysis plan, November 2026

New analyses follow the [refined October proposal](proposal/Proposal_Refined_October_2026.pdf) as amended on 9 November 2026 by the [revised research design](revised_research_design_2026_11.md). The revision replaces the proposal's purpose statement and research questions and frames citizen watering as co-produced climate adaptation. On 23 November 2026, RQ4 was reframed as a question of priorities under a fixed budget, and the crown-health plan was revised (both below). The proposal still defines the data, Appendix A and the RQ1 models in Appendix B. The [seminar package](../examination/README.md) records earlier work; its RQ numbering and sampling commitments no longer apply.

**Fundamental question.** To what extent does citizen watering help Berlin's street trees through heat and drought, which trees and neighbourhoods does it reach, and which levers under public control could make it more effective and more equitable?

| Question | Evidence sought | Status and next step |
| --- | --- | --- |
| RQ1: drought response | Logged events and litres against heat, rain and accumulated drought; stability across seasons; share of young street trees' water need covered; persistence of care | Daily panel and citywide exploratory fits done. Next: verify platform coverage, match street-tree stock, fit hierarchical event and two-part volume models, report effects in litres and as a share of need. |
| RQ2: levers and reach | Change in logged care after pump repairs or failures; difference in discontinuities at the 10- and 12-year municipal-care limits; need-weighted reach by density, social status, residents per street tree and turnout | Equity summaries exist as context. Next: build a pump status panel, register the age-limit test, build the precinct-to-LOR turnout crosswalk. |
| RQ3: tree outcomes | Survival (primary) and condition of young street trees with sustained care, near working pumps and either side of the care limits | 3,247 young street trees have April–September logs, enough to detect four-year mortality differences of 1.8–3.0 points. A 2025 inventory shows that identifiers persist (98.5% of street trees) and that 1.5% of young street trees left the cadastre within a year. A [pre-specified one-year test](rq3_one_year_survival_protocol.md) compares 2,145 young trees watered in 2020–2024 with matched unwatered trees; it can detect only a fall in removal risk of about 55–78%. The first run was void because its exposure table dropped removed trees; the [corrected run](rq3_one_year_survival_deviation.md) is inconclusive (−0.21 points, 95% interval −0.86 to 0.40). The 2020–2024 tables are requested from CityLAB. The draft [four-year plan](rq3_four_year_survival_protocol.md) compares yearly cohorts from 2021 to 2025; the projection puts the detectable difference at 0.47–0.66 points a year, against a smallest effect of interest of 0.5. The [crown-health plan](rq3_crown_health_protocol.md), frozen on 24 November before any image was downloaded, relates the change in crown greenness between the August 2020 and 2025 aerial images to the level of care in between. All five flights were read and every [check](../output/rq3_crown_health/check.json) passed. A fall in greenness predicts removal ([design](../output/rq3_crown_health/design.json)), so the result reads as crown condition. The [result](../output/rq3_crown_health/outcome.json) is inconclusive: sustained care goes with a gain of 0.0055 NDVI over no care (95% interval −0.0016 to 0.0123), from 965 young trees with occasional, 668 with repeated and 152 with sustained care against 45,775 never watered. The interval excludes gains above about three years of crown growth with age, but neither no gain nor the smallest effect of interest (0.0019). The 2015–2020 placebo and older trees show no gap in the same direction. Adjusted for 2020 greenness, the estimate is 0.0006; survivor bounds widen the interval to −0.0033 to 0.0134. Next: freeze the four-year plan before its data are opened; request felling reasons and CityLAB's 2020 tree table, which allows the crown result without survivor selection. Gate A fixes the primary outcome. |
| RQ4: priorities under a fixed budget | Which young street trees and planning areas support for volunteer watering should reach first, given potential water stress, existing care, pump access and social vulnerability; whether that ranking holds across the RQ3 effect range; scale-up, break-even funding and share of public supply as supporting analyses | Month 5. Reframed on 23 November 2026. RQ3 enters as a range, so a null RQ3 still leaves a ranking. |

## RQ1

See the [daily pilot protocol](rq1_daily_exploratory_protocol.md) and the [pilot results](../output/rq1_daily/report.md).

**Panel.** The pipeline re-audits the source logs and reconciles daily totals with the canonical tree-day product. It builds a 542-area × 1,051-day April–September panel for 2020–2025, starting 18 May in 2020. It computes weather lags before filtering seasons and keeps missing rain missing. A zero means no log, assuming the platform was available; an optional outage calendar masks unavailable days. Areas that never log stay in the panel.

**Pilot.** The pilot fits citywide log1p OLS on linked logs for all tree types, with calendar controls and HAC uncertainty over calendar distance. It is neither the proposal's main model nor a street-tree rate analysis nor a causal estimate. The proposal's annual counts came from different provisional samples, so the report states its own inclusion rules and counts. Annual fits, early/late fits and a fixed sensitivity grid are all reported, without selecting on significance.

**Main inference.**

- **Population.** Match logs on catalogued street trees to the corresponding stock. Ages 5–19 form a subgroup and an allocation scenario, not the sole primary population. The current inventory cannot establish historical stock or municipal care.
- **Zero days.** Include observed zero days in all eligible areas. Restricting fits to participating areas is a sensitivity analysis only.
- **Pooling.** Start partial pooling at Bezirksregion scale, then assess planning-area models.
- **Models.** Fit hierarchical negative-binomial event models and a two-part daily volume model, with nonlinear weather terms, holidays, participation context and prespecified lag windows. Flag slopes in sparse areas as weakly identified.
- **Checks.** Assess dependence, predictive fit, held-out seasons, and annual and early/late contrasts.
- **Units.** Report responses in litres and as shares of young street trees' daily guidance need. The proposed smallest effect of interest is 1% of that need.
- **Persistence.** Separate first from repeat watering of the same tree.

All of 2020–2025 has already been inspected. The registered plan must disclose the September and October pilots and the November benchmarks, and it may not call any of these years an untouched hold-out.

## RQ2 and RQ3

The [revised research design](revised_research_design_2026_11.md) specifies these designs and their feasibility counts. The [benchmarks memo](policy_feedback_2026_11.md) has the first numbers. Rules that bind the analysis:

- **Detectability first.** Compute each primary estimand's minimum detectable effect from design counts or pre-period data. Register a smallest effect of interest in policy units (litres, share of need, avoided replacements, euros) before examining outcomes. Where the detectable effect is larger, report descriptions and bounds, and use equivalence tests so null results state what they rule out.
- **Pumps.** Build a dated status panel from OpenStreetMap history and district repair records, then run a staggered difference in differences on trees within walking distance. Prefer dated repairs, since status edits may follow use. Distance gradients stay descriptive.
- **Care limits.** Compare the change in watering between ages 9–10 and 11–12 in 10-year districts with the same change in 12-year districts, using inference for a discrete running variable. **Do not tabulate watering by tree age near the limits before registering the test.** The design detects only strong compensation (minimum detectable effect 0.56–1.21 points against watered shares of 0.81–1.9%).
- **Survival.** The primary RQ3 outcome is removal of a young street tree between inventory snapshots. Exposure ends before a snapshot that shows treated and control trees alive, so a later removal cannot change it; matching is within district, planting year and genus group, with local matching as a secondary analysis ([four-year plan](rq3_four_year_survival_protocol.md)); felling reasons separate deaths from planned removals. The change in crown greenness from 20 cm leaf-on aerial images (August 2015, 2020 and 2025) is the secondary outcome for young trees, against an ordered level of care ([crown-health plan](rq3_crown_health_protocol.md)); Sentinel-2 condition for trees older than 20 and colour-infrared vitality for mature trees are further secondary outcomes.
- **Logged is not received.** The lever designs capture all water from their source. Comparisons within age bands beyond municipal-care ages limit municipal confounding. Sensitivity analyses vary the share of unlogged care.
- **Dropped.** Area-level greenness regressions, because the minimum detectable per-tree effect is 0.08–0.25 NDVI.

## Part I: cooling

Part I now only supplies the canopy-to-cooling conversion for RQ4. It needs a valid-overpass Landsat morning-LST panel with canopy and low vegetation, antecedent drought, dated greenness and built-form controls. The model compares dry and wet vegetation gradients with date effects, partial pooling, spatial validation and propagated uncertainty. The supplied monthly Ortsteil LST file lacks verified scene and boundary metadata and cannot replace this panel. Appendix A keeps watering-induced satellite cooling out of scope.

## RQ4: priorities under a fixed budget

Reframed on 23 November 2026:

> With a fixed budget for supporting volunteer watering, which young street trees and planning areas should Berlin prioritise, given potential water stress, existing care, access to a working pump and social vulnerability? How robust is that ranking to the uncertain effect of care on survival?

- **Inputs that need no RQ result.** Catalogued street trees aged 5–19, with wider age ranges as sensitivities.
  - **Potential water stress:** age, sealed tree pits, heat exposure, dry spells.
  - **Existing care:** logged care and municipal care up to age 10 or 12, by district.
  - **Pump access:** distance to a working street pump.
  - **Social vulnerability:** the MSS status index.
- **Support.** Levers the city can buy, each with a cost: pump repairs, watering bags, campaigns or map prompts, municipal top-ups. RQ2's pump design gives the care added per lever.
- **Objective.** Fixed before the ranking is computed: need-weighted young-tree seasons newly covered per euro, and avoided losses per euro, under an equity constraint. Weighting the inputs is a value choice, so results are a frontier across weightings, not one ranking.
- **RQ3 as a range.** Avoided losses use the survival intervals and, where the validity check holds, the crown-health interval with its survivor bounds. The ranking is recomputed from zero effect to each interval's upper bound. If the top areas stay the same, the decision does not depend on RQ3; if not, the report names the areas that switch and the effect at which they do.
- **Safeguards.** Minimum public-care shares, caps on care-based reductions, no reductions where evidence is too uncertain, and an explicit report of burden shifted onto volunteers.
- **Supporting analyses.**
  - **Scale-up** (for example to 100,000 participants): litres, coverage of young-tree need, share of public supply, peak-day demand and pump capacity. Per-person volumes need user identifiers.
  - **Retargeting:** move care from trees older than 20 towards trees aged 11–20.
  - **Funding:** platform and campaign costs against the water's replacement value plus avoided replacements at about €3,000 per young tree.

Keep logged care separate from vulnerability and inferred need. Low recorded care does not show absent watering, unwillingness or unmet demand, and no current output validates municipal priorities or ecological benefits.

## Milestones

1. **Month 1.** Resolve the street/park classification and historical-stock questions. Audit platform availability, timestamps, pump access and holiday calendars. Request the 2020–2024 inventories, felling reasons, pump repair dates, district watering lists and age-limit history, user identifiers and platform costs. Build the pump status panel and estimate pre-period Sentinel-2 noise. Register outcomes, thresholds, contrasts, validation folds and sensitivity ranges, disclosing all prior inspection.
2. **Gate A (end of Month 1).** Data access decides whether survival is the primary RQ3 outcome and which RQ2 designs proceed.
3. **Months 2–3.** RQ1 hierarchical models; RQ2 pump design, limit test and reach comparisons.
4. **Months 3–4.** RQ3 survival and condition. **Gate B:** where the detectable effect exceeds the registered threshold, report bounds and carry ranges into RQ4.
5. **Months 5–6.** RQ4 priorities and supporting scenarios, synthesis, writing and code release.
