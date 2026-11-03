# Active analysis plan — refined proposal, 26 October 2026

The [refined October proposal](proposal/Proposal_Refined_October_2026.pdf)
governs new analyses. The frozen [seminar proposal](../examination/proposal/Proposal_October_2026.pdf),
[seminar analysis plan](archive/analysis_plan_october_2026_seminar.md) and September
reports document earlier work; their RQ numbering and sampling commitments are
superseded. The refined proposal has four questions, with Part II as the core.

| Question | Evidence sought | Current status and next step |
| --- | --- | --- |
| RQ1 — Civic climate response | How do logged events and litres vary with heat, rain and antecedent drought; how stable are responses? | Daily all-tree linked panel and citywide exploratory fits implemented. Next: verify coverage, match street-tree population, add controls and fit hierarchical event / two-part volume models. |
| RQ2 — Vulnerability and resource inequality | Crude and adjusted care differences by environmental vulnerability, tree stock, social conditions and pump accessibility | Existing equity summaries are contextual. Audit pumps and matched denominators before adjusted comparisons. |
| RQ3 — Added spatial information | Stable discordance with conventional assessments and incremental prediction of subsequent logged care | Define separate environmental, social, tree-need and civic layers; use temporal and spatial validation with uncertainty. Weak correlation alone is not added value. |
| RQ4 — Allocation consequences | Rank changes, priority overlap and group shares under equal-budget need-only and civic-informed rules | Scenario analysis remains planned; vary reporting factors and apply explicit fairness safeguards. |

## RQ1 first implementation

Read the [daily pilot protocol](rq1_daily_exploratory_protocol.md) and
[initial results](../output/rq1_daily/report.md). The pipeline re-audits source
logs, reconciles canonical daily totals, and builds 542-area × 1,051-day
April–September data for 2020–2025 (2020 starts 18 May). Weather lags precede
season filtering; missing rain remains missing. No-log zeros are conditional
on assumed platform availability, and an optional outage calendar masks
unavailable outcomes. Never-active areas remain in the panel.

The pilot uses linked logs for all tree types and citywide log1p OLS, with
calendar controls and calendar-distance HAC uncertainty. It is not the
proposal's main model, a street-tree rate analysis, or a causal estimate.
Existing annual counts in the proposal used different provisional samples;
the new report states its inclusion rules and reproduces its own counts.
Seasonal totals, distinct trees, sparsity, weather completeness and changes
in timestamp precision are included in the audit. Annual and early/late fits
and a fixed sensitivity grid are reported without selecting significant results.

For main RQ1 inference, match catalogued street-tree logs to the corresponding
stock. Age 5–19 is a subgroup and allocation scenario, **not the sole primary
population** in the refined design. Current inventory cannot establish historical
stock or municipal care. Include observed zero days in all eligible areas;
participating-area-only fits are a sensitivity, not the primary selection rule.
Start partial pooling at Bezirksregion scale, then assess planning-area models.
Use hierarchical negative-binomial events and a two-part daily volume model,
nonlinear weather responses, holidays, participation context and prespecified
lag windows. Flag sparse-area slopes as weakly identified. Assess dependence,
predictive fit, held-out seasons, annual contrasts and early/late contrasts.

This is exploratory work on already inspected data. Register the subsequent
analysis plan with a disclosure of the September and October pilots. None of
2020–2025 may be described as an untouched confirmatory hold-out.

## Supporting environmental analysis

Part I supports RQ2–RQ3; it is no longer numbered RQ1. Build valid-overpass
Landsat morning-LST data with canopy and low vegetation, antecedent drought,
dated greenness and built-form controls. Compare dry/wet vegetation gradients
with date effects, partial pooling, spatial validation and propagated uncertainty.
The supplied monthly Ortsteil LST file lacks verified scene and boundary
metadata and is not a replacement for this panel. Individual watering-induced
satellite cooling is outside the active design.

## Allocation and interpretation

RQ4 uses catalogued street trees aged 5–19 as a scenario population, with wider
age ranges as sensitivities. Predict logged-care probability and conditional
litres using only information available at allocation time. Compare need-only
and civic-informed allocations under the same hypothetical budget, varying
effective-care factors and reporting assumptions. Include minimum public-care
shares, caps on care-based reductions and no reductions where evidence is
too uncertain. Report shifts of maintenance burden onto volunteers explicitly.

Keep logged care separate from vulnerability and inferred need. Low recorded
care is not proof of no watering, unwillingness, or unmet physiological demand.
No current output validates municipal priorities or ecological benefits.

## Next milestones

1. Resolve street/park classification and historical-stock uncertainty; audit
   availability, timestamp semantics, pump access and holiday calendars.
2. Lock main outcomes, contrasts, nonlinear terms, validation folds and
   sensitivity ranges; disclose all prior inspection.
3. Fit RQ1 hierarchical event and volume models, then extend to RQ2 after
   the environmental and resource inputs pass their audits.
4. Build RQ3 comparisons before attempting RQ4 allocation scenarios. Keep
   the end-of-Month-4 decision on reducing allocation to descriptive scenarios.
