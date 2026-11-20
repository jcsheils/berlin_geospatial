# Analysis plan, November 2026

New analyses follow the [refined October proposal](proposal/Proposal_Refined_October_2026.pdf) as amended on 9 November 2026 by the [revised research design](revised_research_design_2026_11.md). The revision replaces the proposal's purpose statement and research questions and frames citizen watering as co-produced climate adaptation. The proposal still defines the data, Appendix A and the RQ1 models in Appendix B. The [seminar package](../examination/README.md) records earlier work; its RQ numbering and sampling commitments no longer apply.

**Fundamental question.** To what extent does citizen watering help Berlin's street trees through heat and drought, which trees and neighbourhoods does it reach, and which levers under public control could make it more effective and more equitable?

| Question | Evidence sought | Status and next step |
| --- | --- | --- |
| RQ1: drought response | Logged events and litres against heat, rain and accumulated drought; stability across seasons; share of young street trees' water need covered; persistence of care | Daily panel and citywide exploratory fits done. Next: verify platform coverage, match street-tree stock, fit hierarchical event and two-part volume models, report effects in litres and as a share of need. |
| RQ2: levers and reach | Change in logged care after pump repairs or failures; difference in discontinuities at the 10- and 12-year municipal-care limits; need-weighted reach by density, social status, residents per street tree and turnout | Equity summaries exist as context. Next: build a pump status panel, register the age-limit test, build the precinct-to-LOR turnout crosswalk. |
| RQ3: tree outcomes | Survival (primary) and condition of young street trees with sustained care, near working pumps and either side of the care limits | 3,247 young street trees have April–September logs, enough to detect four-year mortality differences of 1.8–3.0 points. A 2025 inventory shows that identifiers persist (98.5% of street trees) and that 1.5% of young street trees left the cadastre within a year. A [pre-specified one-year test](rq3_one_year_survival_protocol.md) compares 2,145 young trees watered in 2020–2024 with matched unwatered trees; it can detect only a fall in removal risk of about 55–78%. The first run was void because its exposure table dropped removed trees; the [corrected run](rq3_one_year_survival_deviation.md) is inconclusive (−0.21 points, 95% interval −0.86 to 0.40). The 2020–2024 tables are requested from CityLAB. The draft [four-year plan](rq3_four_year_survival_protocol.md) compares yearly cohorts from 2021 to 2025; the projection puts the detectable difference at 0.47–0.66 points a year, against a smallest effect of interest of 0.5. The draft [crown-health plan](rq3_crown_health_protocol.md) compares crown NDVI change between the August 2020 and 2025 aerial images for 1,972 young trees first watered in between, with 2015–2020 as a placebo. Next: freeze both plans before their data are opened; request felling reasons. Gate A fixes the primary outcome. |
| RQ4: policy scenarios | Scale-up, retargeting, need-only against citizen-informed allocation, break-even funding, share of public supply, fairness of care | Month 5. RQ3 bounds the effective-care factor; without RQ3 results, the scenarios vary it over a range. |

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
- **Survival.** The primary RQ3 outcome is removal of a young street tree between inventory snapshots. Exposure ends before a snapshot that shows treated and control trees alive, so a later removal cannot change it; matching is within district, planting year and genus group, with local matching as a secondary analysis ([four-year plan](rq3_four_year_survival_protocol.md)); felling reasons separate deaths from planned removals. Crown NDVI change from 20 cm leaf-on aerial images (August 2015, 2020 and 2025) is the secondary outcome for young trees ([crown-health plan](rq3_crown_health_protocol.md)); Sentinel-2 condition for trees older than 20 and colour-infrared vitality for mature trees are further secondary outcomes.
- **Logged is not received.** The lever designs capture all water from their source. Comparisons within age bands beyond municipal-care ages limit municipal confounding. Sensitivity analyses vary the share of unlogged care.
- **Dropped.** Area-level greenness regressions, because the minimum detectable per-tree effect is 0.08–0.25 NDVI.

## Part I: cooling

Part I now only supplies the canopy-to-cooling conversion for RQ4. It needs a valid-overpass Landsat morning-LST panel with canopy and low vegetation, antecedent drought, dated greenness and built-form controls. The model compares dry and wet vegetation gradients with date effects, partial pooling, spatial validation and propagated uncertainty. The supplied monthly Ortsteil LST file lacks verified scene and boundary metadata and cannot replace this panel. Appendix A keeps watering-induced satellite cooling out of scope.

## RQ4: scenarios

- **Allocation.** Use catalogued street trees aged 5–19, with wider age ranges as sensitivities. Predict the probability of logged care and conditional litres from information available at allocation time. Compare need-only and citizen-informed allocations under one hypothetical budget. Include minimum public-care shares, caps on care-based reductions, no reductions where evidence is too uncertain, and an explicit report of burden shifted onto volunteers.
- **Scale-up** (for example to 100,000 participants). Report litres, coverage of young-tree need, share of public supply, peak-day demand and pump capacity. Per-person volumes need user identifiers.
- **Retargeting.** Move care from trees older than 20 towards trees aged 11–20.
- **Funding.** Compare platform and campaign costs with the water's replacement value plus avoided replacements at about €3,000 per young tree.

Keep logged care separate from vulnerability and inferred need. Low recorded care does not show absent watering, unwillingness or unmet demand, and no current output validates municipal priorities or ecological benefits.

## Milestones

1. **Month 1.** Resolve the street/park classification and historical-stock questions. Audit platform availability, timestamps, pump access and holiday calendars. Request the 2020–2024 inventories, felling reasons, pump repair dates, district watering lists and age-limit history, user identifiers and platform costs. Build the pump status panel and estimate pre-period Sentinel-2 noise. Register outcomes, thresholds, contrasts, validation folds and sensitivity ranges, disclosing all prior inspection.
2. **Gate A (end of Month 1).** Data access decides whether survival is the primary RQ3 outcome and which RQ2 designs proceed.
3. **Months 2–3.** RQ1 hierarchical models; RQ2 pump design, limit test and reach comparisons.
4. **Months 3–4.** RQ3 survival and condition. **Gate B:** where the detectable effect exceeds the registered threshold, report bounds and carry ranges into RQ4.
5. **Months 5–6.** RQ4 scenarios, synthesis, writing and code release.
