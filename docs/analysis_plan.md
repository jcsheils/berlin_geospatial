# Active analysis plan — revised November 2026

The [refined October proposal](proposal/Proposal_Refined_October_2026.pdf) governs new analyses, as amended on 9 November 2026 by the [revised research design](revised_research_design_2026_11.md).
- **What the revision does.** It evaluates citizen watering as co-produced climate adaptation and replaces the proposal's purpose statement and research questions.
- **What the proposal still covers.** It remains the reference for data definitions, Appendix A and the RQ1 models in Appendix B.
- **Earlier work.** The [seminar package](../examination/README.md) documents earlier work; its RQ numbering and sampling commitments are superseded.

**Fundamental question.** To what extent does citizen watering help Berlin's street trees through heat and drought, which trees and neighbourhoods does it reach, and which levers under public control could make it more effective and more equitable?

| Question | Evidence sought | Current status and next step |
| --- | --- | --- |
| RQ1 — Civic drought response | How logged events and litres vary with heat, rain and accumulated drought; stability across seasons; share of young street trees' water need covered; persistence of care | Daily all-tree linked panel and citywide exploratory fits implemented. Next: verify coverage, match street-tree stock, fit hierarchical event / two-part volume models, and report effects in litres and as a share of need. |
| RQ2 — Public levers and reach | Change in logged care after pump repairs or failures; difference in discontinuities at the 10- and 12-year municipal-care limits; need-weighted reach by density, social status, residents per street tree and turnout | Existing equity summaries are contextual. Next: build a pump status panel from OpenStreetMap history and repair records, register the limit test, and build the precinct-to-LOR turnout crosswalk. |
| RQ3 — Tree outcomes | Survival (primary) and condition of young street trees with sustained logged care, near working pumps and on either side of the municipal-care limits; effects detected or ruled out | Feasibility counted: 3,247 young street trees with April–September logs, so four-year mortality differences of 1.8–3.0 points are detectable. Next: request an earlier full inventory and felling reasons; Gate A fixes the primary outcome. |
| RQ4 — Policy scenarios | Scale-up, retargeting, need-only against citizen-informed allocation, break-even funding, share of public supply and fairness of care | Planned for Month 5. The effective-care factor is bounded by RQ3; otherwise it is varied as a range. |

## RQ1 first implementation

Read the [daily pilot protocol](rq1_daily_exploratory_protocol.md) and the [initial results](../output/rq1_daily/report.md).

**Panel.**
- The pipeline re-audits source logs and reconciles canonical daily totals.
- It builds 542-area × 1,051-day April–September data for 2020–2025 (2020 starts 18 May).
- Weather lags precede season filtering, and missing rain remains missing.
- No-log zeros are conditional on assumed platform availability, and an optional outage calendar masks unavailable outcomes.
- Never-active areas remain in the panel.

**Pilot.**
- The pilot uses linked logs for all tree types and citywide log1p OLS, with calendar controls and calendar-distance HAC uncertainty.
- It is not the proposal's main model, a street-tree rate analysis, or a causal estimate.
- Existing annual counts in the proposal used different provisional samples. The new report states its inclusion rules and reproduces its own counts.
- The audit includes seasonal totals, distinct trees, sparsity, weather completeness and changes in timestamp precision.
- Annual and early/late fits and a fixed sensitivity grid are reported without selecting significant results.

**Main RQ1 inference.**
- **Population.** Match catalogued street-tree logs to the corresponding stock. Age 5–19 is a subgroup and allocation scenario, **not the sole primary population**. The current inventory cannot establish historical stock or municipal care.
- **Zero days.** Include observed zero days in all eligible areas. Fits restricted to participating areas are a sensitivity, not the primary selection rule.
- **Pooling.** Start partial pooling at Bezirksregion scale, then assess planning-area models.
- **Models.** Use hierarchical negative-binomial events and a two-part daily volume model, with nonlinear weather responses, holidays, participation context and prespecified lag windows. Flag sparse-area slopes as weakly identified.
- **Checks.** Assess dependence, predictive fit, held-out seasons, annual contrasts and early/late contrasts.
- **Units.** Report weather responses in litres and as shares of the daily guidance need of young street trees. The proposed smallest effect of interest is 1% of that need.
- **Persistence.** Separate first from repeat watering of the same tree.

This is exploratory work on already inspected data. Register the subsequent analysis plan with a disclosure of the September and October pilots and the November benchmarks. None of 2020–2025 may be described as an untouched confirmatory hold-out.

## Levers and tree outcomes (RQ2–RQ3)

Design details and feasibility counts are in the [revised research design](revised_research_design_2026_11.md). First numbers are in the [policy-relevance memo](policy_feedback_2026_11.md).

- **Detectability before outcomes.**
  - For each primary estimand, compute the minimum detectable effect from design counts or pre-period data.
  - Before outcomes are examined, register a smallest effect of interest in policy units: litres, share of need, avoided replacements or euros.
  - Where the minimum detectable effect is larger, report descriptions and bounds.
  - Use equivalence tests, so that null results state which effects they rule out.
- **Street pumps.**
  - Build a dated status panel from OpenStreetMap history and district repair records.
  - Compare logged watering of trees within walking distance before and after a repair or failure with trees near unchanged pumps (staggered difference in differences).
  - Prefer dated repairs, because status edits may follow use.
  - Cross-sectional distance gradients stay descriptive.
- **Municipal-care limits.**
  - Compare the change in watering between ages 9–10 and 11–12 in districts that stop municipal watering at 10 years with the change in districts that stop at 12 years.
  - Use inference methods for a discrete running variable.
  - **Do not tabulate watering by tree age near the limits before the test is registered.**
  - The design detects only strong compensation: the minimum detectable effect is 0.56–1.21 percentage points, against seasonal watered shares of 0.81–1.9%.
- **Survival.**
  - The primary RQ3 outcome is removal of a young street tree between inventory snapshots. Satellite condition is unsuitable because young crowns cover a median 3–13% of a 10 m pixel.
  - Start exposure only after a snapshot that shows treated and control trees alive.
  - Match within planning area, genus group and planting year.
  - Use felling reasons to separate deaths from planned removals.
  - Secondary outcomes are Sentinel-2 condition for trees older than 20 and colour-infrared vitality for mature trees.
- **Logged is not received.**
  - The lever designs capture all water from their source.
  - Comparisons within age bands beyond municipal-care ages limit municipal confounding.
  - Sensitivity analyses vary the share of unlogged care.
- **Excluded.** Area-level greenness regressions are not run, because the minimum detectable per-tree effect would be 0.08–0.25 NDVI.

## Supporting environmental analysis

Part I is reduced to one role: supplying the conversion from canopy to cooling in the RQ4 scenarios.
- **Panel.** Build valid-overpass Landsat morning-LST data with canopy and low vegetation, antecedent drought, dated greenness and built-form controls.
- **Comparison.** Compare dry/wet vegetation gradients with date effects, partial pooling, spatial validation and propagated uncertainty.
- **Supplied file.** The supplied monthly Ortsteil LST file lacks verified scene and boundary metadata and is not a replacement for this panel.
- **Out of scope.** Individual watering-induced satellite cooling stays outside the design (Appendix A).

## Policy scenarios and interpretation

**Allocation.**
- **Population.** RQ4 uses catalogued street trees aged 5–19 as the allocation scenario population, with wider age ranges as sensitivities.
- **Prediction.** Predict logged-care probability and conditional litres using only information available at allocation time.
- **Comparison.** Compare need-only and citizen-informed allocations under the same hypothetical budget. Bound the effective-care factor with RQ3 results or, failing that, vary it together with the reporting assumptions.
- **Safeguards.** Include minimum public-care shares, caps on care-based reductions, and no reductions where evidence is too uncertain.
- **Burden.** Report shifts of maintenance burden onto volunteers explicitly.

**Other scenarios.**
- **Scale-up** (for example 100,000 participants). Report litres, coverage of young-tree need, the share of public supply, peak-day demand and pump capacity. Per-person volumes need user identifiers.
- **Retargeting.** Move care from trees older than 20 towards trees aged 11–20.
- **Funding.** Compare platform and campaign costs with the water's replacement value plus avoided replacements, at about €3,000 per young tree.

**Interpretation.** Keep logged care separate from vulnerability and inferred need. Low recorded care is not proof of no watering, unwillingness, or unmet physiological demand. No current output validates municipal priorities or ecological benefits.

## Next milestones

1. **Month 1.**
   - **Audits.** Resolve street/park classification and historical-stock uncertainty. Audit availability, timestamp semantics, pump access and holiday calendars.
   - **Data requests.** Request an earlier full inventory, felling reasons, pump repair dates, district watering lists and limit history, user identifiers and platform costs.
   - **Builds.** Build the pump status panel and estimate pre-period Sentinel-2 noise.
   - **Registration.** Register outcomes, thresholds, contrasts, validation folds and sensitivity ranges, disclosing all prior inspection.
2. **Gate A (end of Month 1).** Data access decides whether survival is the RQ3 primary outcome and which RQ2 lever designs proceed.
3. **Months 2–3.** Fit the RQ1 hierarchical event and volume models. Run the RQ2 pump design, the limit test and the reach comparisons.
4. **Months 3–4.** Run the RQ3 survival and condition analyses.
   - **Gate B.** Where the minimum detectable effect exceeds the registered threshold, report bounds and carry ranges into RQ4.
5. **Months 5–6.** RQ4 scenarios, then synthesis, writing and code release.
