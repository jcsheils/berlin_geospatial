# RQ3 crown-health test: notes after the freeze

This note records how the analysis applies or departs from the [pre-specified plan](rq3_crown_health_protocol.md), which was frozen in commit `ebfcbf3` on 24 November 2026 and stays unchanged. Entries are dated and added in order.

## 24 November 2026: what counts as a miss in the eye check

The check stage stops the test if more than 10% of 200 discs "miss the tree by eye in the 2025 image". The plan does not define a miss.

**How the chips were rated.** The chips task (workflow run 4, artifact `crown-health-chips-2025`) drew 200 young trees with seed 42, regardless of watering. Each chip shows about 10 × 10 m of the 2025 colour image around the tree's inventory position, with the 2 m disc drawn. One person rated all 200 by hand with [tools/eye_check.py](../tools/eye_check.py). The rating page asked "Does the magenta circle sit on the tree?" and showed neither tree identifiers nor the running share of misses.

**Rule for unclear chips.** Chips where no crown could be made out in the disc, for example in deep shadow, were rated `no` and count as misses. This makes the check stricter than a rule that counts only visible misses.

**Timing.** This rule was recorded after the 200 chips were rated and before the share of misses was counted.

**Sheet.** `data/processed/rq3_crown_health/eye_check.csv`, SHA-256 `e37d70d9fc35c18b0ef82f8d3b60d5785f9e2dd2f860710103e434333852729f`.

**Result.** 12 of 200 chips were rated `no` (6.0%; Wilson 95% interval 3.5–10.2%). The plan allows at most 20, so the eye check passes. The check stage records the same figure in `check.json`.

## 27 November 2026: which commit each run used

Workflow runs 1–6 (the three crosschecks, the chips, and the 2020 and 2025 extractions) ran on the frozen commit `ebfcbf3`. Runs 7–9 (the 2015, 2020 colour and 2023 extractions) ran on `759a655`, which adds only the eye-check note, tool, test and sheet above. The plan, the extraction code, the configuration and the workflow are the same in both commits. Every shard of all five flights records the same plan, code and inventory hashes (`ed820d90…`, `0b21bfdb…` and `d4c739f8…`). The check, design and outcome stages ran locally on the extracted tables, with stage code unchanged since the freeze (`8b42fd70…`, recorded in each output).
