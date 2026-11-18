# RQ3 one-year survival test: deviation and result, 18 November 2026

This note reports how the analysis departed from the [registered protocol](rq3_one_year_survival_protocol.md), which stays unchanged. The protocol was pushed to the repository as commit `81c19a4` at 09:26 on 18 November 2026, before the outcome stage ran.

## The registered run is void

The registered run found zero removals among 2,145 watered trees aged 0–15 and among 3,820 aged 16–40. At the overall rate of about 1.5% a year, about 32 and 57 removals were expected.

The cause is the exposure source the protocol names, `data/processed/temporal/recorded_tree_day_watering_2020_2025.csv`. That table kept only logged trees still present in the 2026 inventory. Every watered tree that was removed therefore counted as unwatered. The raw log export keeps these trees. The registered result (`output/rq3_one_year_survival/outcome.json`) is an artefact and is not evidence.

## Seen before the corrected run

Diagnosing the fault meant comparing logged trees with the 2026 inventory. Of the logged trees in the 2025 inventory, 117 were absent in 2026: 107 street trees and 10 green-space trees. By age in 2025, 25 were 0–15, 49 were 16–40 and 43 were older. The corrected run is therefore not blind.

## Changes

1. **Exposure** comes from the raw export (`data/giessdenkiez_bewässerungsdaten (1).csv`). It is cleaned as for the tree-day table (exact duplicates removed, Europe/Berlin dates, 18 May 2020 to 31 December 2025, positive litres) but not matched to any inventory. This adds 23 watered trees aged 0–15 (2,181 against 2,158) and 43 aged 16–40. No tree watered in the tree-day table loses its exposure.
2. **The interval** comes from a cluster bootstrap over planning areas (2,000 resamples, seed 42, percentile interval). The registered linearised variance gets nothing from strata with one control and gave S4 an interval of zero width. On synthetic data with well-filled strata the two intervals agree. Both are reported; the bootstrap interval is primary.

Cohort, strata, outcome, analyses and interpretation rules are as registered.

## Result

| Analysis | Watered | Removed | Risk, watered | Risk, matched controls | Difference (pp) | 95% bootstrap interval | Linearised interval |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| Primary: any log 2020–2024, age 0–15 | 2,167 | 22 | 1.02% | 1.23% | −0.21 | −0.86 to 0.40 | −0.54 to 0.11 |
| S1: identifier absent | 2,167 | 22 | 1.02% | 1.23% | −0.22 | −0.86 to 0.40 | −0.54 to 0.11 |
| S2: 500 L or more in a season | 218 | 1 | 0.46% | 1.13% | −0.67 | −1.67 to 0.64 | −1.10 to −0.24 |
| S3: older trees, age 16–40 | 3,863 | 43 | 1.11% | 1.42% | −0.30 | −0.69 to 0.12 | −0.62 to 0.01 |
| S4: matched within planning area | 1,994 | 21 | 1.05% | 1.19% | −0.13 | −0.86 to 0.54 | zero width |

Full output: `output/rq3_one_year_survival/corrected.json`.

## Interpretation under the registered rules

- **Primary: inconclusive.** The interval includes zero. It does not exclude a fall in removal risk of up to 0.86 points (70% of the control risk), nor a rise of up to 0.40 points.
- **Older trees show a gap of the same size** (−0.30 against −0.21 points). The protocol reads this as pointing to selection or to the data rather than to watering. Residents may water trees on streets that see less felling.
- **Dose:** one removal among 218 heavily watered trees. Too few trees for any conclusion.

## Consequences

- Any survival exposure must come from logs that do not depend on the later inventory.
- The raw export appears to lack logs for trees deleted before 2025: only 1 of its 11,278 trees is absent from the 2025 inventory. A four-year test therefore needs the platform's full log history, including deleted trees, as well as the 2020–2024 inventories.
