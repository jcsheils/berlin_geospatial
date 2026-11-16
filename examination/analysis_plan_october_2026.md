# Seminar analysis plan, October 2026

> Superseded on 26 October 2026 by the [current analysis plan](../docs/analysis_plan.md). RQ numbers here follow the [seminar proposal](proposal/Proposal_October_2026.pdf); read its [qualifications](proposal/README.md) alongside.

## Part II: daily civic heat response (core)

RQ2 asks whether recorded watering responds to daily heat and dryness, and whether the response varies with neighbourhood social status once baseline participation is accounted for.

- **Panel.** Build a balanced area-day panel that separates unavailable periods, observed zeros and missing weather.
- **Model.** Model whether an area ever participates, then fit a hierarchical negative-binomial model for daily events among participating areas. Litres and distinct trees serve as secondary descriptions and sensitivities.
- **Offset.** The proposed offset is the historical eligible street-tree population aged 5–19. The current all-tree inventory is a sensitivity denominator, not an unqualified substitute.
- **Covariates.** Tmax, antecedent dry spells, precipitation, heat-warning days, weekday, holidays, year and season, plus status, age composition and turnout as area predictors.
- **Checks.** Partial pooling, uncertainty intervals, temporal stability and scale sensitivity.
- **Participation.** User IDs would separate breadth of participation from a few very active contributors; without them, report tree-based proxies and their limits.

Existing evidence: monthly weather associations, spatial and equity context, the LOR-month panel and the positive tree-day table. The daily panel and model do not exist yet. Any registration must disclose prior examination of these outcomes, and no inspected period counts as untouched.

## Part I: vegetation cooling loss (supporting)

RQ1 asks how the relationship between vegetation and morning LST weakens on dry clear-sky days, and how that loss is distributed across planning areas. The main period is 2017–2024.

- **Panel.** Build a valid-overpass Landsat panel with canopy and low-vegetation fractions, dated Sentinel-2 greenness, drought anomalies and built-form controls.
- **Model.** Fit one hierarchical model with date effects and vegetation × drought × status terms. Separate per-unit loss from total area loss.
- **Checks.** Propagate uncertainty; run sealed-cell placebos, spatial dependence checks and blocked validation.

The monthly Ortsteil file cannot serve as this panel: its cloud filtering, boundaries, count meaning and acquisition dates are unverified. The borough maps are legacy context.

## Part III: allocation comparison (exploratory)

RQ3 predicts logged care for eligible young street-tree seasons with regularised logistic regression and gradient boosting, validated spatially and temporally and calibrated.

- **Leakage.** Build features inside training folds; previous-season neighbourhood care must not leak held-out labels.
- **Comparison.** Compare need-only and complement-based rankings by expected unmet water, with full sensitivity to assumed doses and weights.
- **Status.** This is normative decision support, not a causal effect or an optimised service rule. The equity screening maps are groundwork, not predictions or rankings.
- **Fallback.** If supporting data or valid predictions are late at the end of Month 4, reduce this part to a descriptive comparison.

## Integration and priorities

The H4 bridge relates posterior response slopes to cooling-loss estimates, and only once both exist. Keep behaviour and need as separate layers; reducing public service where residents volunteer needs an explicit policy justification.

Priority order: Part II, then Part I, then Part III. The [readiness assessment](readiness.md) lists missing inputs, open decisions and the six-month schedule. No output estimates causal cooling, heat-mortality effects or an optimal allocation.
