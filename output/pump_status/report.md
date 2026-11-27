# Street-pump status panel: audit summary

Treatment side of the RQ2 pump design only ([protocol](../../docs/pump_status_protocol.md)). No watering outcome is joined, tabulated or examined here.

- **Snapshot.** OpenStreetMap full history via the ohsome API, data to 2026-07-27T09:00:00Z; 2,331 candidate nodes, 15,602 versions.
- **Universe.** 2,093 Berlin nodes carried the platform selector (`network` or, before May 2021, `description` = `Berliner Straßenbrunnen`) in at least one version. 221 other water wells never did and are excluded.
- **Changes.** 1,702 recorded status transitions, of which 400 are repairs or failures; 84.0% of these are backed by a `check_date` set within a day of the edit (78.0% at day precision). 3 were reverted within 14 days.
- **Deletions.** 41 pump nodes were deleted; 4 have another pump node within 15 m (remapping rather than removal). 32 exits were later restored on the same node; `net_change_if_restored` gives the net transition across the gap (failure 5, none 5, reclassified 13, repair 1, status_reported 8).

## Check against the platform's published pump layer

The platform's harvester published its pump layer weekly. At each frozen layer's commit instant, the snapshot's selection reproduces these pumps, labels and check dates:

| commit | committed_utc | selector | published_pumps | replicated_pumps | in_both | only_published | only_replicated | status_label_agreement | check_date_agreement |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9eb7bee | 2021-05-02T04:07:01Z | description | 1862 | 1862 | 1862 | 0 | 0 | 1862 | 1862 |
| b7471fc | 2023-04-02T04:05:56Z | network | 1940 | 1940 | 1940 | 0 | 0 | 1940 | 1940 |

## Pumps at season start (1 April)

| season | mapped_as_water_well | platform_visible | working | broken | locked | pump_absent | unknown | removed | disused | deleted | not_mapped | water_wells_with_known_status_pct | working_pct_of_known | median_days_since_check |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2019 | 1109 | 0 | 215 | 47 | 9 | 14 | 824 | 0 | 0 | 0 | 984 | 25.7 | 75.4 | 455.0 |
| 2020 | 1504 | 1467 | 285 | 62 | 16 | 33 | 1108 | 1 | 0 | 1 | 587 | 26.3 | 72.0 | 821.0 |
| 2021 | 1875 | 1862 | 863 | 307 | 18 | 5 | 682 | 76 | 0 | 5 | 136 | 63.6 | 72.3 | 212.0 |
| 2022 | 1880 | 1873 | 920 | 276 | 17 | 8 | 659 | 81 | 1 | 11 | 119 | 64.9 | 75.3 | 565.0 |
| 2023 | 1945 | 1940 | 1092 | 271 | 19 | 3 | 560 | 121 | 2 | 10 | 14 | 71.2 | 78.8 | 666.0 |
| 2024 | 1948 | 1943 | 1160 | 296 | 19 | 3 | 470 | 127 | 2 | 11 | 4 | 75.9 | 78.5 | 622.0 |
| 2025 | 1946 | 1941 | 1178 | 300 | 19 | 3 | 446 | 133 | 2 | 11 | 0 | 77.1 | 78.5 | 975.0 |

Mapping coverage grew quickly before 2021, so early seasons mix real status with missing mapping: `not_mapped` pumps were added to OSM later, and `unknown` pumps carried no status tag.

## Repairs and failures by edit year

| year | failure_changes | repair_changes | failure_check_date_backed | repair_check_date_backed |
| --- | --- | --- | --- | --- |
| 2010 | 1 | 0 | 0 | 0 |
| 2011 | 1 | 0 | 0 | 0 |
| 2018 | 2 | 6 | 1 | 5 |
| 2019 | 2 | 2 | 2 | 1 |
| 2020 | 34 | 59 | 26 | 51 |
| 2021 | 15 | 44 | 15 | 42 |
| 2022 | 38 | 59 | 26 | 50 |
| 2023 | 29 | 18 | 25 | 15 |
| 2024 | 20 | 11 | 15 | 8 |
| 2025 | 25 | 7 | 23 | 6 |
| 2026 | 23 | 4 | 21 | 4 |

## Comparison with the reported 2022 status

| source | date | pumps | working | not_working | status_unknown | working_pct_of_pumps | working_pct_of_known_status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| OpenStreetMap (this snapshot) | 2022-01-01 | 1880 | 922 | 301 | 657 | 49.0 | 75.4 |
| OpenStreetMap (this snapshot) | 2022-04-01 | 1880 | 920 | 301 | 659 | 48.9 | 75.3 |
| OpenStreetMap (this snapshot) | 2022-07-01 | 1878 | 928 | 302 | 648 | 49.4 | 75.4 |
| OpenStreetMap (this snapshot) | 2022-10-01 | 1938 | 1079 | 298 | 561 | 55.7 | 78.4 |
| OpenStreetMap (this snapshot) | 2022-12-31 | 1937 | 1087 | 293 | 557 | 56.1 | 78.8 |
| Berliner Mieterverein, 'Berliner Wasserpumpen: Trinkwasser per Muskelkraft' (04/2024), reporting 2,079 street pumps of which 1,614 worked (status 2022) | 2022 (status year) | 2079 | 1614 | 465 |  | 77.6 | 77.6 |

## Design feasibility (counts only)

Distinct catalogued street trees within 100 m and 200 m of pumps with a dated repair or failure in the season, and of comparison pumps whose known status did not change. Comparison trees exclude trees near a treated pump.

| season | group | pumps | trees_within_100m | trees_within_200m | trees_within_100m_also_near_treated | trees_within_200m_also_near_treated |
| --- | --- | --- | --- | --- | --- | --- |
| 2019 | repair | 2 | 78 | 216 |  |  |
| 2019 | failure | 1 | 39 | 158 |  |  |
| 2019 | repair_or_failure | 3 | 117 | 374 |  |  |
| 2019 | repair_or_failure_check_backed | 2 | 80 | 284 |  |  |
| 2019 | unchanged_comparison | 282 | 10635 | 30779 | 0 | 55 |
| 2020 | repair | 33 | 983 | 3581 |  |  |
| 2020 | failure | 33 | 1109 | 3741 |  |  |
| 2020 | repair_or_failure | 64 | 2062 | 7072 |  |  |
| 2020 | repair_or_failure_check_backed | 56 | 1657 | 5768 |  |  |
| 2020 | unchanged_comparison | 325 | 12242 | 34827 | 60 | 1965 |
| 2021 | repair | 44 | 1042 | 3824 |  |  |
| 2021 | failure | 15 | 387 | 1315 |  |  |
| 2021 | repair_or_failure | 57 | 1413 | 5080 |  |  |
| 2021 | repair_or_failure_check_backed | 55 | 1403 | 4996 |  |  |
| 2021 | unchanged_comparison | 1133 | 39531 | 112355 | 43 | 1756 |
| 2022 | repair | 53 | 2263 | 7617 |  |  |
| 2022 | failure | 35 | 1313 | 4611 |  |  |
| 2022 | repair_or_failure | 82 | 3393 | 11185 |  |  |
| 2022 | repair_or_failure_check_backed | 67 | 2681 | 9033 |  |  |
| 2022 | unchanged_comparison | 1127 | 38655 | 109343 | 72 | 3001 |
| 2023 | repair | 16 | 373 | 1470 |  |  |
| 2023 | failure | 29 | 1014 | 3719 |  |  |
| 2023 | repair_or_failure | 42 | 1332 | 4848 |  |  |
| 2023 | repair_or_failure_check_backed | 37 | 1187 | 4321 |  |  |
| 2023 | unchanged_comparison | 1341 | 47192 | 133631 | 82 | 2040 |
| 2024 | repair | 8 | 323 | 1270 |  |  |
| 2024 | failure | 15 | 587 | 2031 |  |  |
| 2024 | repair_or_failure | 22 | 863 | 3093 |  |  |
| 2024 | repair_or_failure_check_backed | 21 | 816 | 2913 |  |  |
| 2024 | unchanged_comparison | 1454 | 50854 | 144294 | 34 | 1184 |
| 2025 | repair | 7 | 308 | 1112 |  |  |
| 2025 | failure | 24 | 965 | 3129 |  |  |
| 2025 | repair_or_failure | 31 | 1273 | 4191 |  |  |
| 2025 | repair_or_failure_check_backed | 29 | 1209 | 3939 |  |  |
| 2025 | unchanged_comparison | 1468 | 51334 | 145565 | 35 | 1874 |

## Claim limits

- An edit date records when a mapper reported a status, not when a pump broke or was repaired. Status edits may follow use, including by platform users; check_date-backed and district repair dates are preferred for registration.
- `unknown` is missing information, not a working pump. Early seasons have low status coverage.
- Tree counts use the current inventory and straight-line distance; they are feasibility counts, not exposure measures.
