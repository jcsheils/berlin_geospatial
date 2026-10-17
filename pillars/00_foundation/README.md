> **October 2026 scope update:** historical design context is retained below. The active design is the October proposal: Part II civic heat response (core), Part I vegetation cooling loss (supporting), and Part III allocation (exploratory). See `docs/analysis_plan.md` and `examination/README.md`. Existing descriptive products remain valid within their stated limits.

# 00 — Shared Spatial and Data Foundation

**Readiness: partial-ready**

## Role

This workstream creates stable spatial crosswalks, cleaned event records, shared
time conventions, and analysis-ready panels used by every thesis pillar. It is
infrastructure, not an additional results chapter.

## Available evidence

- recorded citizen-watering events from May 2020 through April 2026;
- a local Berlin tree inventory linked through pitid;
- official 2021 LOR boundaries;
- tree-to-LOR assignment and cumulative 2020-2025 LOR metrics;
- a balanced 542-LOR by 68-month recorded-watering panel for May 2020 through
  December 2025;
- a reusable crosswalk for the 11,127 recorded trees observed in that complete
  analysis window;
- current district, spatial-cluster, and equity outputs.

## Missing foundation products

- a complete-inventory persisted tree-to-LOR crosswalk suitable for canopy
  work beyond recorded trees;
- historical month-specific eligible-tree risk sets;
- a source manifest with checksums and acquisition metadata;
- run manifests and automated contract checks for scientific pipelines.

## Immediate output completed

`data/processed/foundation/lor_month_recorded_watering_2020_2025.csv`
distinguishes the partial May 2020 platform month, uses `recorded_` exposure
names, and carries current-inventory denominators only in explicitly named
fields. Its metadata preserves zero semantics, source checksums, audit totals,
and the denominator limitation.

## Claim boundary

Foundation outputs describe what is present in the source data. They do not
estimate heat effects, hydrological mechanisms, equity impacts, or economic
benefits.
