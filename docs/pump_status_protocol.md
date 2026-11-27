# Street-pump status panel — protocol, 15 November 2026

This note documents the treatment side of the RQ2 street-pump design ([revised research design](revised_research_design_2026_11.md), RQ2 item 1; [analysis plan](analysis_plan.md), "Street pumps"). It builds a dated status history for Berlin's street pumps from OpenStreetMap, with design-feasibility counts.
- **No outcomes.** The build reads no watering logs, joins no pump status to watering, and computes no watering outcome near pumps. It reads no tree ages.
- **Registration.** The pump design and its smallest effect of interest can therefore still be registered before any outcome is examined.
- **Enforcement.** A unit test checks that the module refers to none of the watering or age fields.

Build and audit:

```bash
python pipelines/09_build_pump_status_panel.py
PYTHONPATH=src python -m unittest tests.test_pump_status -v
```

The [audit summary](../output/pump_status/report.md) reports the counts quoted below.

## Source and selection

- **Snapshot.** The source is OpenStreetMap full history from the ohsome API, frozen in [`data/raw/osm_pumps/`](../data/raw/osm_pumps/README.md) with data to 27 July 2026. It was acquired in two requests:
  - a tag-filtered discovery of every node in Berlin that was ever a water well, a lifecycle-prefixed water well, or carried a platform selector or pump status tag;
  - every version of those 2,331 nodes, requested by id.
- **Universe.** The universe is the 2,093 nodes in Berlin that carried the platform's selector in at least one version: `network=Berliner Straßenbrunnen`, or `description=Berliner Straßenbrunnen` before the harvester switched on 10 May 2021. "In Berlin" means within the LOR 2021 union plus 10 m. Excluded from the universe:
  - 221 water wells that never carried either tag;
  - 11 nodes tagged only `name=Berliner Straßenbrunnen`.
- **Validation.** The selection reproduces the platform's own published pump layer exactly in both selector eras: 1,862 pumps on 2 May 2021 and 1,940 on 2 April 2023, with identical status labels and check dates.

## Status of one version

The rules apply in this order; the first that matches decides.

| Rule | Status |
| --- | --- |
| No `man_made=water_well`, but `removed:`, `razed:`, `demolished:`, `destroyed:` or `was:man_made=water_well` | `removed` |
| No `man_made=water_well`, but `disused:` or `abandoned:man_made=water_well` | `disused` |
| Neither a water well nor a lifecycle-prefixed one | `not_a_pump` |
| `pump:status`, or failing that `pump_status`, `pump.status`, `operational_status`, `operational:status` or `status`: `ok`/`functional` | `working` |
| The same keys: `broken`, `missing_beam`, `out_of_order`, `non_functional`, `damaged` | `broken` |
| The same keys: `locked`, `blocked` | `locked` |
| The same keys: `missing` | `removed` |
| Free-text values with a clear meaning, from an explicit table of the 16 found in the snapshot | as listed in `FREE_TEXT_STATUS` |
| No recognised status, but `disused=yes` / `abandoned=yes` | `disused` |
| No recognised status, but `locked=yes` | `locked` |
| No recognised status, but `pump=no` or `removed:pump=*` | `pump_absent` |
| A status value that is not understood (3 versions: `?`, `off` and an *unbekannt* note) | `unrecognised` |
| No status at all | `unknown` |

- **Usable.** `usable` is 1 for `working` and 0 for `broken`, `locked`, `pump_absent`, `disused` and `removed`. It is missing for `unknown`, `unrecognised`, `not_a_pump`, `deleted` and not yet mapped. Missing status is missing information, not a working pump.
- **Matching codes.** Codes match after lower-casing and removing spaces and dots, so `OK` and `o k.` count as `ok`. The platform's own label (*funktionsfähig*, *defekt*, *verriegelt*, *unbekannt*) is kept for comparison.

## Changes and their dates

- **Segments.** Each node's history runs from its first version mapped as a pump or former pump; earlier versions count as not yet mapped. Gaps in validity, and an end before the snapshot end, are deleted periods.
- **Changes.** A change is a pair of consecutive segments with different statuses; the first mapping is not a change. Change types:
  - `repair` (usable 0 → 1) and `failure` (1 → 0);
  - `status_reported` (unknown → known) and `status_withdrawn` (known → unknown);
  - `reclassified` (for example broken → removed);
  - `exit` (deleted or no longer a pump) and `reentry`.
- **Dates.** `change_time_utc` is the edit instant and `edit_date` its Europe/Berlin date.
- **`check_date` backing.** A change is backed by `check_date` when a version within one day of the edit adds or changes `check_date` to a date between 365 days before the edit and one day after it. `event_date` is that `check_date` when it has day precision, and otherwise `edit_date`.
- **Flags.**
  - `reverted_within_14d` marks a change undone within 14 days.
  - `successor_osm_id` marks a deletion where another pump node lies within 15 m and either existed at the time or was created within 31 days (remapping rather than removal).
  - `net_change_if_restored` gives the net transition when a deleted node is later restored. For example, working → deleted → removed is a net failure.

## Season panel

- **Grain.** The panel has one row per pump and April–September season for 2019–2025. A season runs from 1 April 00:00 to 1 October 00:00 Europe/Berlin. The panel is balanced over the universe (14,651 rows): not-yet-mapped and deleted states are explicit statuses.
- **Content.** Each row holds:
  - the status, usability, platform visibility and latest `check_date` at season start;
  - the status at season end;
  - counts of each change type in the season, with first repair and failure dates;
  - flags for any repair or failure and for a `check_date`-backed one;
  - the number of `check_date` updates;
  - the status path, for example `broken>working`.
- **Timing basis.** All panel timing uses edit instants, so the start status and the in-season counts agree. Dating the 400 repairs and failures by `check_date` instead would move 2 of them across a season boundary.

## Design feasibility

- **Trees counted.** Catalogued street trees come from the restored frozen inventory: one row per tree ID, preferring the street-tree row, which gives 433,176 trees. They are counted within 100 m and 200 m, straight-line and inclusive, of each pump's last mapped position. The median pump has 35 street trees within 100 m and 123 within 200 m; 5.3% have none within 100 m.
- **Per-season groups.** For each season the audit counts:
  - pumps with a repair, a failure, either, or a `check_date`-backed one;
  - distinct trees near those pumps;
  - comparison pumps, which were mapped at season start with a known status, show no change of any type and are still water wells at season end;
  - comparison trees, which exclude trees near a treated pump.
- **Counts so far.** Pumps with a repair or failure per season, 2019–2025: 3, 64, 57, 82, 42, 22 and 31. In 2022 these 82 pumps have 3,393 street trees within 100 m and 11,185 within 200 m.

No minimum detectable effect is computed here. One would need outcome variance, and that may only be estimated after registration.

## First audit

- **Mapping coverage.** Coverage grows quickly before 2021. On 1 April, 1,109 pumps were mapped as water wells in 2019, 1,875 in 2021 and 1,946 in 2025. The share with a known status was 26% in 2019 and 2020, 64% in 2021 and 77% in 2025.
- **Stale checks.** The median time since the last `check_date` at season start exceeds a year in most seasons.
- **Changes.** There are 1,702 recorded transitions. Most are first status reports (1,114); there are 210 repairs and 190 failures.
  - Of the repairs and failures, 84% are backed by `check_date` (78% at day precision), with a median lag of 0 days.
  - Three repairs or failures were reverted within 14 days.
- **2022 comparison.** In 2022 OpenStreetMap mapped 1,878–1,938 pumps as water wells, of which 920–1,087 were recorded as working. A further 557–659 had no status. Among pumps with a known status, 75–79% were working, against the reported 1,614 of 2,079 (77.6%). OpenStreetMap therefore covers fewer pumps and fewer status reports than the reported total, but a similar working share where status is known.

## Limits and choices left to registration

- **Edit timing.** Edits record when a mapper reported a status. Status edits may follow use, including by platform users, so edit timing can depend on watering itself.
  - `check_date`-backed changes and district repair records, which have been requested, are preferred.
  - The registration should fix the timing basis, and whether unbacked or quickly reverted changes count.
- **Treatment definition.** Repairs and failures may be pooled or separated.
  - Also to fix: whether lifecycle removals and net changes across deletions count, and how `unknown` start statuses and the early low-coverage seasons (2019–2020) enter.
- **Exposure.** Radius (100 or 200 m), assignment of trees near several pumps, and walking against straight-line distance.
  - Tree counts use the current inventory, so trees removed before it are missing and later plantings are included.
- **Smallest effect of interest.** This is to be stated in litres per tree-season before outcomes are examined. Cross-sectional distance gradients stay descriptive.
