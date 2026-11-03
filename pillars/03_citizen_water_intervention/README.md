> **October 2026 scope update:** historical design context is retained below. The active design is the October proposal: Part II civic heat response (core), Part I vegetation cooling loss (supporting), and Part III allocation (exploratory). See `docs/analysis_plan.md` and `examination/README.md`. Existing descriptive products remain valid within their stated limits.

# Part II — Citizen Watering and Thermal Association

**Readiness: blocked-planned; conditional on detectability**

## Primary question

Conditional on adequate detectability, is greater cumulative recorded watering
intensity associated with lower local LST at satellite-supported units with
demonstrably high logging coverage?

## Current evidence

The repository establishes event timing, concentration, tree selectivity,
inventory-normalised reach, spatial clustering, and social/environmental
alignment. A balanced LOR-month exposure panel and a positive-exposure
tree-local-date audit also exist. These are
descriptive exposure and participation results, not thermal effects.

## Pre-outcome gate

Month 1 audits exposure and logging coverage. During Months 1–2, fit an
outcome-only nuisance model without recorded-watering exposure to estimate
residual LST variance and spatial covariance. At the end of Month 2, simulate
power using the observed continuous-dose distribution.

The gate-driving exposure is recorded litres per 1,000 L/ha during the
preceding 30 days at approximately 1 ha support. The SESOI is -0.03 K per
additional 1,000 recorded L/ha/30 days (about -0.10 K per 3,500 L/ha).
Confirmatory H2 requires at least 80% simulated power at two-sided alpha = 0.05
and a simulated MDE no larger in magnitude than the SESOI. The threshold is a
design scenario, not an assumed watering effect.

## Conditional primary design

- 2021–2024 imagery-aligned window;
- 30-day logged litres ending on the day before an overpass as the primary
  continuous dose; season-to-date is secondary;
- primary analysis within logged units/periods with high platform coverage;
- no-record matching, acute effects, and seven-/14-day windows as secondary;
- common-support, balance, spillover, timing, and shifted-date/location placebo
  diagnostics.

Age and genus are secondary support-level effect modifiers only after the main
gate passes. They use pre-specified no-gap age functions and a small set of
sufficiently supported genera; they are not individual-tree temperature
effects.

## Claim boundary

No platform record does not mean no watering. Municipal and unlogged resident
care remain unobserved. A Landsat value is not an individual-tree temperature.
Without adequate power the result is non-detectability, not evidence that
watering has no physiological effect.
