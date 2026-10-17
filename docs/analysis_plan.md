# Active analysis plan — October 2026

The [October proposal](../examination/proposal/Proposal_October_2026.pdf) is authoritative. Read its [qualifications](../examination/proposal/README.md) alongside it. The [August plan](archive/analysis_plan_august_2026.md) is retained as historical context; its conditional watering-to-LST gate is not an active requirement.

## Part II — Daily civic heat response (core)

RQ2 asks whether recorded citizen watering responds to daily heat and dryness and whether response varies with neighbourhood social status after accounting for baseline participation. Build a balanced area-day panel, explicitly distinguishing unavailable periods, observed zeros and missing weather. Model whether an area ever participates, then use a hierarchical negative-binomial model for daily event counts among participating areas. Litres and distinct trees provide secondary descriptions and sensitivity analyses.

The proposed primary offset is the historical eligible street-tree population aged 5–19; the current all-tree inventory is a sensitivity denominator, not a substitute without qualification. Planned controls include Tmax, antecedent dry spells, precipitation, heat-warning days, weekday, holidays, year and season, with status, age composition and turnout as area predictors. Use partial pooling, uncertainty intervals, temporal stability checks and scale sensitivity. Optional user IDs would distinguish participation breadth from highly active contributors; without them, report tree-based proxies with limits.

Current evidence: monthly weather associations, spatial/equity context, the LOR-month panel and positive tree-day table. The daily model and balanced daily panel are not implemented. Any registration must disclose prior examination of these outcomes; no already-inspected data period should be labelled untouched.

## Part I — Vegetation cooling loss (supporting)

RQ1 concerns the weakening of the vegetation–morning-LST relationship on dry clear-sky days and its distribution across planning areas. The intended main period is 2017–2024. Build a valid-overpass Landsat panel with canopy and low-vegetation fractions, dated Sentinel-2 greenness, temporal drought anomalies and built-form controls. Fit one hierarchical model with date effects and vegetation × drought × status terms. Distinguish per-unit loss from total area loss; propagate uncertainty, check sealed-cell placebos, spatial dependence and blocked validation.

The provisional monthly Ortsteil file is not this panel. Cloud filtering, original boundaries, count semantics and acquisition dates remain unverified. Existing borough maps are descriptive legacy context.

## Part III — Allocation comparison (exploratory)

RQ3 predicts logged care for eligible young street-tree seasons with regularised logistic regression and gradient boosting, followed by spatial/temporal validation and calibration. Features must be constructed inside training folds; previous-season neighbourhood care must not leak held-out labels. Compare need-only and complement-based rankings using expected unmet water, with full sensitivity to assumed doses and weights.

This is a normative decision-support comparison, not a causal effect or an optimised public service rule. Existing equity screening maps are contextual groundwork; they are not completed predictions or allocation rankings. At the end of Month 4, reduce this part to descriptive comparison if supporting data or valid predictions are delayed.

## Integration and feasibility

The H4 bridge relates posterior civic-response slopes to cooling-loss estimates only when both exist. Keep behaviour and need as separate layers; giving less public service to places because residents volunteer requires an explicit policy justification.

Prioritise Part II, then supporting Part I, then exploratory Part III. The [readiness assessment](../examination/readiness.md) records missing inputs, decisions and the six-month schedule. No current output estimates causal cooling, heat-mortality effects, or an economically optimal allocation.
