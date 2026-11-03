# RQ1 daily pilot — 26 October 2026

This is an exploratory implementation protocol, written before fitting this
daily pilot. It is **not a preregistration**: the monthly outcomes and earlier
descriptions of these years have already been inspected. The governing source
is the [refined October proposal](proposal/Proposal_Refined_October_2026.pdf),
especially pp. 4 and 7–8. The examination PDF and September reports remain frozen
historical deliverables.

## Question and scope

RQ1 asks how logged events and litres vary with heat, rainfall and antecedent
dryness, and whether those associations persist across seasons. This first
stage builds daily inputs and a citywide adjusted descriptive baseline; it
does not implement the proposed hierarchical negative-binomial event model
or two-part volume model. No local response slopes or historical rates are
estimated here.

## Samples and coverage

- Remove exact source-row duplicates, parse timestamps as UTC and assign
  Europe/Berlin local dates, retaining 18 May 2020–31 December 2025.
- Retain positive, finite reported volumes and nonempty tree IDs. Report
  exclusions. Match to the existing unique tree-to-LOR crosswalk; reconcile
  daily events and litres to the canonical positive tree-day product.
- Primary pilot: linked trees of all types, not a street-tree rate sample.
  Separately report all valid source logs, including unassigned logs; these
  are a source-coverage comparison, not independently verified Berlin totals.
- Build all 542 planning-area-days within the declared platform window, then
  restrict to April–September. Include never-active areas. A zero means no
  log in this extract, conditional on presumed availability. The repository
  has no verified outage calendar. Accept an optional CSV of unavailable
  dates; mask outcomes on those dates and retain the underlying counts for
  reconciliation. Never fill pre-launch dates with observed zeros.
- Current all-tree inventory counts are contextual fields, not historical
  offsets. The matched street-tree population remains a main-model task.
- Retain daily event counts, litres and distinct trees; recompute seasonal
  distinct trees from IDs. Never sum daily distinct counts into seasonal reach.
- Flag event volumes >500 L; compare excluding those events. Do not discard
  them as known errors. Timestamp precision changes in 2024–2025 preclude
  hour-of-day analysis and qualify cross-year interpretation.

## Weather and adjustment

Use the frozen DWD Tempelhof 00433 archive. Build weather features on the
complete calendar, before filtering seasons or outcome availability. Missing
rain stays missing. Antecedent dry-spell length is the number of consecutive
days with rain <1 mm ending yesterday. Missing rain makes length unknown
until a known wet day resets it; the initial unknown run is also unknown.
Today's rain never enters the antecedent feature. Store yesterday's rain and
the previous seven days' cumulative rain (all seven must be known).

For each of events, litres and distinct trees, fit OLS to log(1 + daily total).
Prespecified weather terms: Tmax/5°C, today's rain/10 mm, yesterday's rain/10 mm,
and antecedent dry spell/7 days. Controls: year, calendar month, weekday and
a common linear day-within-month term. Retain zero days. Use joint complete
cases; list dates excluded because weather is missing. Report coefficients
and approximate 95% Bartlett HAC intervals with 14 **actual calendar-day**
lags. The existing calendar-distance sandwich estimator is reused, so gaps
between seasons and years are never collapsed. These are log1p outcome-unit
associations, not exact percentage changes in arithmetic means. No p-value
selection or multiplicity-adjusted confirmatory claims.

Report the full three-outcome grid for: linked baseline, 2021–2025 only,
excluding 2022, excluding >500 L events, all valid source logs, 7- and 28-day
HAC, year-by-month controls, a quadratic Tmax term, and seven-day antecedent
rain replacing yesterday's rain and dry spell. Also fit each year and the
2020–2022 / 2023–2025 groups separately with the baseline specification.
These exploratory subgroup estimates are not a formal test of stability;
overlap of intervals or non-significance does not establish stability.

Plot annual activity and year-specific associations. Report event variance /
mean and zero-day shares to motivate count modelling. Do not select the main
model using this grid. Holiday/campaign controls, nonlinear response curves,
hierarchical estimation, held-out-season validation and formal annual contrasts
remain for the registered main analysis. No year examined here is untouched.

## Reproduction and safeguards

`PYTHONPATH=src .venv/bin/python pipelines/08_build_rq1_daily.py`

Optional: `--unavailable-dates path/to/dates.csv` with a unique `date` column.
Outputs include compressed balanced area-day data, city-day and weather tables,
yearly audit, complete coefficient grid, figures, report and source SHA-256
checksums. Tests must cover lag direction, missing rain, calendar gaps,
pre-launch exclusion, outage masking, never-active areas, duplicate logs,
volume filtering and reconciliation. No external data downloads are needed.
