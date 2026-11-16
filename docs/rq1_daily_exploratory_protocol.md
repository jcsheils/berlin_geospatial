# RQ1 daily pilot protocol, 26 October 2026

This exploratory protocol was written before the daily pilot was fitted. It is **not a preregistration**: the monthly outcomes and earlier descriptions of these years had already been inspected. It follows the [refined October proposal](proposal/Proposal_Refined_October_2026.pdf), especially pp. 4 and 7–8. The examination PDF and the September reports stay frozen.

## Question and scope

RQ1 asks how logged events and litres vary with heat, rainfall and antecedent dryness, and whether those associations persist across seasons. This stage builds the daily inputs and a citywide adjusted descriptive baseline. It does not fit the proposed hierarchical negative-binomial event model or the two-part volume model, and it estimates no local slopes or historical rates.

## Samples and coverage

- Drop exact duplicate rows, parse timestamps as UTC, assign Europe/Berlin dates and keep 18 May 2020–31 December 2025.
- Keep positive, finite volumes with nonempty tree IDs, and report exclusions. Match to the unique tree-to-LOR crosswalk and reconcile daily events and litres with the canonical tree-day product.
- The primary sample is linked trees of all types, not a street-tree rate sample. Report all valid source logs, including unassigned ones, as a coverage comparison; they are not verified Berlin totals.
- Build all 542 planning-area-days within the platform window, then restrict to April–September, keeping areas that never log. A zero means no log in this extract, assuming the platform was available. No verified outage calendar exists, so accept an optional CSV of unavailable dates: mask outcomes on those dates and keep the raw counts for reconciliation. Never fill pre-launch dates with zeros.
- Current inventory counts are context, not historical offsets. Matching the street-tree population belongs to the main model.
- Keep daily events, litres and distinct trees. Recompute seasonal distinct trees from IDs; never sum daily distinct counts into seasonal reach.
- Flag events above 500 L and compare fits without them, but do not discard them as errors. The 2024–2025 change in timestamp precision rules out hour-of-day analysis and qualifies comparisons across years.

## Weather and adjustment

Use the frozen DWD Tempelhof 00433 archive and build weather features on the full calendar, before filtering seasons or availability. Missing rain stays missing.

- **Dry spell:** consecutive days with rain below 1 mm, ending yesterday. Missing rain makes the length unknown until a known wet day resets it; the initial run is also unknown. Today's rain never enters this feature.
- **Rain lags:** yesterday's rain and the previous seven days' total (all seven must be known).

For events, litres and distinct trees, fit OLS to log(1 + daily total) with Tmax/5 °C, today's rain/10 mm, yesterday's rain/10 mm and dry spell/7 days. Controls: year, calendar month, weekday and a linear day-within-month term. Keep zero days and use joint complete cases, listing dates dropped for missing weather. Report coefficients with approximate 95% Bartlett HAC intervals over 14 **actual calendar-day** lags; the reused calendar-distance sandwich estimator never collapses gaps between seasons or years. Coefficients are in log1p units, not exact percentage changes in means. No p-value selection and no multiplicity-adjusted confirmatory claims.

Report the full three-outcome grid for: the linked baseline; 2021–2025 only; excluding 2022; excluding events above 500 L; all valid source logs; 7- and 28-day HAC; year-by-month controls; a quadratic Tmax term; and seven-day rain replacing yesterday's rain and dry spell. Fit each year and the 2020–2022 and 2023–2025 groups with the baseline specification. These subgroup fits do not test stability formally: overlapping intervals or non-significance do not establish it.

Plot annual activity and year-specific associations, and report event variance-to-mean ratios and zero-day shares to motivate count models. Do not choose the main model from this grid. Holiday and campaign controls, nonlinear responses, hierarchical estimation, held-out-season validation and formal annual contrasts belong to the registered main analysis. No year examined here is untouched.

## Reproduction and safeguards

```bash
MPLCONFIGDIR=/tmp/berlin-rq1-mpl PYTHONPATH=src python pipelines/08_build_rq1_daily.py
```

Optionally pass `--unavailable-dates path/to/dates.csv` with a unique `date` column. Outputs: the compressed balanced area-day panel, city-day and weather tables, the yearly audit, the full coefficient grid, figures, the report and source SHA-256 checksums. Tests must cover lag direction, missing rain, calendar gaps, pre-launch exclusion, outage masking, never-active areas, duplicate logs, volume filtering and reconciliation. The pipeline needs no downloads.
