# Repository Architecture

## Purpose and scope authority

The repository supports the feedback-incorporated three-part thesis design
revised on 12 August 2026:

1. urban heat, vegetation, and drought;
2. a detectability-gated citizen-watering/LST association analysis;
3. the guaranteed spatial-equity and vulnerability core.

The existing descriptive notebooks and outputs remain valid baseline artifacts
while reusable code is introduced incrementally. The earlier five-pillar plan
is not the current thesis chapter structure.

## Ownership model

The repository separates five concerns:

- `config/` contains machine-readable dataset and workstream declarations;
- `pillars/` retains narrative workstream notes and their mapping to Parts I–III;
- `src/berlin_heat/` contains reusable, testable implementation;
- `data/` contains inputs and analysis-ready processed datasets;
- `output/` contains figures, maps, tables, notebooks, and reports for people.

A downstream analysis must not consume a file from `output/` as its long-term
data interface. During migration, `config/datasets.toml` may point to an
existing output artifact so current work remains runnable. The eventual
replacement is a declared processed dataset with the same tested contract.

## Current part-to-folder mapping

The folder names under `pillars/` predate the three-part proposal. They are
retained temporarily to avoid a disruptive rename:

    pillars/00_foundation/                    shared by all parts
    pillars/01_heat_dynamics/                 Part I heat/LST support
    pillars/02_canopy_cooling_drought/        Part I greenness/drought support
    pillars/03_citizen_water_intervention/    Part II
    pillars/04_spatial_justice_vulnerability/ Part III — guaranteed core
    pillars/05_policy_economics/              future extension, out of scope
    pillars/99_synthesis/                     three-part synthesis and atlas

The machine-readable workstream IDs in `config/project.toml` are authoritative:

- `00_foundation`;
- `01_urban_heat_vegetation_drought`;
- `02_citizen_watering_thermal_association`;
- `03_spatial_equity_vulnerability`;
- `99_synthesis`.

## Shared data contracts

All analysis-ready datasets must declare:

- a logical dataset ID and source snapshot;
- a single observational grain;
- stable spatial and temporal keys;
- source and analysis coordinate reference systems;
- missingness and zero-value semantics;
- input and output checksums;
- the command and configuration used to create the artifact.

Canonical spatial rules:

- `tree_id` is derived from the cadastre `pitid` field;
- `plr_id` is text and refers to the declared LOR vintage;
- district joins use stable codes rather than display names where available;
- analysis geometry uses EPSG:25833;
- EPSG:4326 is reserved for web display and interchange where required.

Canonical temporal rules:

- source timestamps remain UTC;
- local calendar variables use `Europe/Berlin`;
- incomplete observation windows are explicit;
- every panel declares day, week, month, season, or year as its time grain;
- May 2020 is a partial platform month and complete calendar years are
  2021–2025;
- Part II aligns recorded exposure with imagery in 2021–2024, while Part III
  may describe recorded care through 2025.

Canonical terminology:

- new variables describing the platform begin with `recorded_watering`;
- a zero means no recorded platform activity in an observed period;
- it never means that no municipal, private, or unlogged watering occurred;
- Sentinel-2 NDVI is called vegetation greenness, not canopy cover;
- Landsat product-grid values are not called individual-tree temperatures.

## Required analysis grains

No single table should mix these grains:

- recorded-watering event or tree-event;
- event-positive recorded-tree-day for audited local watering dates;
- tree-month for exposure histories;
- LOR-month for neighbourhood integration;
- Planungsraum-calendar-month climatology for complete-year atlas summaries;
- Landsat product-grid-cell/overpass for Part I;
- justified imagery-supported unit/overpass for Part II;
- Planungsraum, Bezirksregion, or district for Part III sensitivity analyses.

Tree events may create exposures for an imagery-supported unit. A resampled
Landsat cell must not be treated as an independent individual-tree temperature
outcome. District observations must not be copied to LOR rows and then analysed
as neighbourhood observations.

## Decision-gate products

Part II has a required pre-outcome product rather than an informal judgement:

    output/02_citizen_watering_thermal_association/detectability/

The go/no-go record must contain actual valid-overpass counts, the observed
continuous 30-day dose distribution, exposure density, residual variance,
spatial correlation, effective sample size, simulated minimum detectable
effect, and power at the locked SESOI of -0.03 K per additional 1,000 recorded
L/ha/30 days (about -0.10 K per 3,500 L/ha). The variance source is an
outcome-only nuisance model fitted without recorded-watering exposure.
Confirmatory H2 requires at least 80% simulated power at two-sided alpha = 0.05
and an MDE no larger in magnitude than the SESOI. The target is a design
threshold, not an assumed effect.

## Output and provenance

New outputs follow the active workstream IDs:

    output/01_urban_heat_vegetation_drought/{figures,tables,models,maps}/
    output/02_citizen_watering_thermal_association/{detectability,figures,tables,models}/
    output/03_spatial_equity_vulnerability/{figures,tables,maps}/
    output/99_synthesis/{figures,tables,maps}/

Each scientific pipeline will eventually write a run manifest recording:

- Git revision and whether the worktree was clean;
- input dataset IDs and checksums;
- source reference periods;
- configuration and random seeds;
- Python and R package versions;
- output paths, schemas, row counts, and CRS values.

Figures are presentations of results, not the only stored results. Every model
figure must be backed by a machine-readable table containing estimates and
diagnostics.

## Current-to-target mapping

- `analysis/build_exploratory_notebook.py` spans the foundation and descriptive
  precursors to Parts II and III.
- `analysis/build_spatial_notebook.py` is foundation work: tree-to-LOR
  assignment and spatial recorded-watering metrics.
- `analysis/build_equity_notebook.py` is the current Part III baseline.
- `analysis/download_equity_data.py` acquires Part III sources and stages a
  complete replacement before changing an existing processed file.
- `pipelines/03_build_lor_month_panel.py` produces the shared recorded-watering
  exposure foundation.
- `pipelines/04_build_watering_temporal_atlas.py` consumes the persisted
  Planungsraum-month panel and LOR boundaries to produce complete-year monthly
  climatologies, five separate January-December annual plates (2021-2025),
  an annual exposure-availability summary, and fixed-scale comparison plates
  without reopening the local tree inventory. Annual maps use the original
  dated panel, never the pooled calendar-month climatology.
- `pipelines/05_build_recorded_tree_day.py` converts matched events to Berlin
  local dates, aggregates repeat same-tree/same-day logs, and produces
  descriptive age- and genus-timing profiles.
- `output/spatial/lor_watering_metrics_2020_2025.gpkg` currently acts as both an
  output and a downstream dependency. This is tolerated only during migration.

## Migration sequence

1. Preserve and validate the current baseline.
2. Lock the three-part scope and machine-readable workstream declarations.
3. Complete stable crosswalks, denominator audits, and run manifests.
4. Finish the Part III population-age, MAUP, registry-coverage, and care-gap
   analyses.
5. Publish the descriptive monthly temporal atlas and tree-day exposure audit.
6. Build the minimal Landsat panel and fit the blinded outcome-only nuisance
   model without recorded-watering exposure.
7. Run the Part II detectability gate at the end of Month 2, before examining
   H2, then complete the Part I Landsat/Sentinel/weather panel and thermal layer.
8. Run qualified Part II association models only if the gate passes.
9. Produce the final atlas and synthesis from published upstream outputs.

No large workflow framework is required at this stage. The standard-library
status and validation commands remain the stable entry point while contracts
and decision-gate products mature.

## Current checkpoint — 25 August 2026

- all three baseline notebooks execute without stored errors;
- current dataset and result invariants are covered by automated tests;
- the balanced 542-Planungsraum by 68-month recorded-watering panel exists;
- the positive-exposure tree-day audit and fixed-scale 2021-2025 monthly atlas
  exist;
- the LOR social/environmental-justice baseline exists;
- the repository configuration now reflects the three-part scope;
- Part III robustness and the Part II detectability audit are the next
  priority deliverables;
- Part I satellite and weather inputs remain planned.
