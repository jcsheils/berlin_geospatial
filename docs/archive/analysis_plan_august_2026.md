# Feedback-Integrated Three-Part Analysis Plan

> Current-stage update, 29 September 2026: the agreed exploratory deliverable
> follows [watering_response_exploratory_protocol.md](watering_response_exploratory_protocol.md).
> RQ2 in that agreement concerns watering response to heat/dryness. Its
> observational response analysis is separate from the conditional cooling
> analysis described below. The addendum takes precedence for this stage.

## Scope authority

This plan follows the feedback-incorporated proposal revised on 12 August 2026. It
supersedes the earlier five-pillar plan. Part III is the guaranteed thesis core;
Part II is conditional on an up-front detectability gate; Part I is the planned
biophysical foundation.

The thesis studies land-surface-temperature (LST) associations and the
distribution of **recorded** citizen care. It does not equate LST with air
temperature or felt heat, treat the absence of a platform log as no watering,
or promise a causal watering effect from incomplete observational logs.

## Research questions and primary hypotheses

### Part I — Urban heat, vegetation, and drought

**RQ1.** How do vegetation greenness, built density, imperviousness, water
proximity, and temporal drought conditions jointly relate to summer LST across
Berlin?

**H1.** Higher Sentinel-2 NDVI/vegetation greenness is associated with lower
summer Landsat LST after adjustment for built form and acquisition conditions;
the association weakens during drier city-wide periods.

### Part II — Citizen watering and thermal association

**RQ2.** Conditional on adequate detectability, is greater cumulative recorded
watering intensity associated with lower local LST at satellite-supported units
with demonstrably high logging coverage?

**H2.** Greater 30-day recorded litres per hectare are associated with lower
LST after adjustment for pre-period LST, greenness, built form, tree
composition, weather, location, and acquisition. Season-to-date dose is
secondary.

### Part III — Spatial equity and vulnerability

**RQ3.** Is recorded citizen watering distributed in proportion to thermal and
socioeconomic need, or do some high-need areas remain underserved?

**H3.** Recorded care aligns more strongly with environmental need than with
socioeconomic vulnerability, leaving a subset of high-need areas underserved.

The existing Planungsraum results (Spearman rho = +0.486 for environmental and
thermal burden, rho = -0.123 for child poverty, and ten screened care-gap
areas) are preliminary, descriptive, and hypothesis-generating because they
informed H3. H3 becomes a hypothesis-guided validation analysis only after the
care measures, component transformations, weights, geography, exclusions, and
multiplicity handling are locked. The term **confirmatory** is reserved for H1
and, if its gate passes, H2.

## Shared reproducible foundation

Current evidence includes:

- 58,847 source rows in the Gieß den Kiez snapshot;
- strong tree-ID linkage to the local cadastre;
- tree-to-LOR assignment for 542 Planungsräume;
- inventory-normalised LOR and district summaries;
- global and local spatial clustering;
- a descriptive LOR social and environmental-justice join;
- a balanced 542-LOR by 68-month recorded-watering panel covering May 2020
  through December 2025, with May 2020 explicitly partial.

Remaining shared work is limited to products needed by the current three-part
design:

- a persisted crosswalk for the complete tree inventory;
- stronger denominator and registry-coverage diagnostics;
- version-locked source and run manifests;
- stable crosswalks among Planungsraum, Bezirksregion, district, and remote-
  sensing supports.

## Descriptive temporal extension

The recorded-watering data support a temporal atlas before satellite outcomes
are available. The canonical products use local Berlin calendar dates and keep
their observational grains separate:

- an event-positive tree-day table records when each linked tree has platform
  activity and aggregates repeat logs on the same local date;
- the balanced Planungsraum-month panel supports monthly spatial summaries;
- separate January-December plates retain each actual month in 2021, 2022,
  2023, 2024, and 2025, with no cross-year averaging;
- January-December climatology maps pool only the five complete calendar years
  2021-2025, while the observed timeline retains and labels partial May 2020;
- one fixed classification scale is reused across the atlas, and recorded zero
  is distinguished from a missing current-inventory denominator.

The main atlas presents all 12 months for each complete year and gives
April-September an additional comparison grid because 96.3% of matched events
occur in that active-season window. An annual exposure table reports event
and litre totals, active Planungsräume, and active Planungsraum-months.
These are exposure availability diagnostics; eligible thermal-analysis years
also require usable dated outcomes, weather, logging coverage, dose variation,
and the detectability gate. Exposure joins must retain actual year and date;
the pooled climatology cannot be used as the watering history of an overpass.
Age and genus profiles at this stage describe exposure
timing only. The full interpretation and future thermal design are locked in
`docs/temporal_analysis_protocol.md`.

## Part I plan

### Data windows and support

- Valid summer Landsat 8/9 observations from 2013–2024 support descriptive
  thermal mapping.
- The main Sentinel-linked analytical panel covers 2017–2024.
- Landsat LST is distributed on a 30 m product grid but originates from roughly
  100 m native thermal sampling. Adjacent 30 m outputs are not treated as
  independent native measurements.
- Sentinel-2 NDVI is vegetation greenness, not ready-made canopy cover.
- ERA5 supplies the primary harmonised temporal controls: 2 m temperature,
  dew point or derived relative humidity, total precipitation, 10 m wind,
  surface pressure, and 7-, 14-, and 30-day antecedent summaries. ERA5 and ESA
  CCI moisture or moisture-balance variables are drought sensitivities, not
  neighbourhood moisture gradients.
- DWD supplies station-observed daily temperature, precipitation, humidity,
  wind, and sunshine-duration sensitivity and plausibility checks. It is not
  the primary spatial weather control and does not directly validate LST.

### Analysis and validation

- align valid Landsat overpasses with contemporaneous Sentinel-2 greenness,
  dated built-form inputs, imperviousness, water proximity, and acquisition-day
  weather;
- fit separate adjusted predictor models before a full specification to expose
  multicollinearity;
- test greenness-by-temporal-drought interactions;
- compare spatially blocked and random cross-validation to quantify leakage;
- diagnose residual spatial dependence with Moran's I, maps, and appropriate
  spatial alternatives;
- report the weather distribution of observed clear-sky overpasses versus all
  summer days and limit inference to that acquisition regime.

## Part II detectability gate and conditional analysis

Part II uses imagery-aligned observations from 2021–2024. Month 1 audits the
recorded-exposure distribution, logging coverage, crosswalks, and usable-image
counts. During Months 1–2, the minimal Landsat outcome panel is built and an
outcome-only nuisance model estimates residual LST variance and spatial
covariance without using recorded-watering exposure (preferably from
pre-platform summers or by cross-fitting). The H2 coefficient remains masked
until the definitive end-Month-2 gate is recorded.

The primary exposure is additional recorded litres per 1,000 L/ha during the
preceding 30 days in a non-overlapping approximately 1 ha imagery-support unit.
The smallest effect size of interest (SESOI) is -0.03 K in support-mean Landsat
LST per additional 1,000 recorded L/ha/30 days, equivalent to about -0.10 K for
3,500 L/ha/30 days. The latter is a physical design scenario of roughly ten
adequately watered tree-month equivalents, not an assumed or published effect.
Simulations preserve the observed continuous-dose distribution, clustering,
and measurement-error scenarios.

At two-sided alpha = 0.05, confirmatory H2 proceeds only if simulated power is
at least 80% for beta = -0.03 K per 1,000 L/ha and the simulated minimum
detectable effect is no larger in magnitude than this SESOI. Otherwise, the
Part II deliverable is the exposure audit, power result, and clearly labelled
exploratory diagnostics. Season-to-date dose is secondary.

If the gate passes:

1. use 30-day logged litres per hectare as the primary continuous dose and
   season-to-date dose as a secondary exposure;
2. restrict the primary contrast to logged units and periods with a logging-
   coverage score fixed before outcome modelling;
3. retain seven- and 14-day windows, acute effects, and no-record matching as
   secondary diagnostics;
4. adjust for pre-period LST, greenness, built form, tree composition, weather,
   location, and acquisition;
5. report common support, covariate balance, spillover exclusions, shifted-date
   and shifted-location placebos, and timing sensitivity;
6. describe results as adjusted associations unless the full identification
   assumptions are demonstrably supported.

Age- and genus-specific estimates are secondary effect-modification analyses,
not separate individual-tree outcomes. They proceed only after the main H2 gate
passes and use a small pre-specified set of no-gap age bands or continuous age
functions and sufficiently supported genus groups. The primary antecedent dose
ends on the day before an overpass because clock-time precision degrades in the
2024-2025 watering export.

With adequate power, a near-zero estimate and confidence interval are a
substantive satellite-scale result. Without adequate power, non-detectability is
not evidence that watering has no physiological or microclimatic effect.

## Part III guaranteed core

Part III can use recorded care through December 2025. Its first deliverables
are the component relationships, not a single composite score:

- logged litres per catalogued tree;
- share of catalogued trees with a recorded watering;
- logged events per 1,000 catalogued trees;
- thermal exposure and low-greenness measures;
- MSS 2025 socioeconomic indicators;
- Environmental Justice Atlas 2023/24 indicators;
- population and older-population share when obtained.

The full analysis is repeated at Planungsraum, Bezirksregion, and district
scales. The MAUP analysis is a headline robustness result. Tree-, area-, and
population-normalised rates, registry-density maps, and restricted samples test
denominator sensitivity. Area-level associations describe places, not volunteer
motives or individual behaviour.

Part III produces a transparent care-gap atlas. If Part I is delayed, the
Berlin Environmental Justice Atlas thermal-load indicator is the declared
thermal fallback. Part II never determines the vulnerability index; if feasible,
it adds a separate association-evidence layer.

## Schedule-protection triggers

- **End of Month 2 — Part I:** if the reproducible Landsat/Sentinel panel is not
  assembled, freeze Part I at descriptive LST/greenness outputs and a data
  audit, and use the Environmental Justice Atlas thermal layer for Part III.
- **End of Month 3 — Part III:** if the full specification is behind, freeze the
  minimum core at Planungsraum plus district sensitivity, the three recorded-
  care measures, MSS and Environmental Justice Atlas components, denominator
  sensitivity, and the screening atlas. Defer Bezirksregion, population-age
  extensions, and alternative weighting.
- If the Part III minimum core is incomplete at that checkpoint, pause Part II
  modelling even when its detectability gate passed.

## Work order and locked deliverables

1. **Protocol and coverage audit:** version-lock sources, build crosswalks, and
   lock the Part III care-rate foundation.
2. **Minimal Part I panel and Part II gate:** build the blinded outcome-only
   nuisance model, then issue the end-Month-2 go/no-go memo before examining H2.
3. **Part I:** complete the valid-overpass panel and thermal-need layer, or
   activate the declared end-Month-2 fallback.
4. **Core Part III:** complete multi-scale care–need analysis and atlas.
5. **Conditional Part II:** run qualified association models only if the gate
   passes.
6. **Synthesis:** integrate three-part evidence, limitations, and policy
   interpretation without manufacturing missing evidence.

No later phase may displace Part III. A failed Part II gate reallocates effort
to Part III robustness, atlas quality, and thesis synthesis.

## Objectives removed from the active thesis scope

The following remain possible future extensions, not current deliverables:

- planting-event or cooling-lag estimation;
- heat-attributed mortality modelling;
- a causal individual-tree temperature effect;
- municipal-watering cost comparison;
- energy, productivity, or welfare cost-benefit analysis.

## Claim ladder

Every result is labelled as one of:

- data audit;
- descriptive association;
- spatial association;
- predictive model;
- qualified observational association;
- quasi-experimental estimate, only if its assumptions are supported.

Advancing up the ladder requires the relevant identification assumptions,
diagnostics, and sensitivity checks. A polished map does not strengthen the
underlying evidence by itself.
