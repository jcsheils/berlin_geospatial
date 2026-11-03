# Repository architecture

The repository keeps original analysis locations stable and adds an examiner-facing entry point in `examination/`. The active research scope is defined by the October proposal and `config/project.toml`. The [August architecture](archive/repository_architecture_august_2026.md) is retained for history.

## Source and product flow

1. Frozen source logs, restored tree inventory and LOR geometry feed `pipelines/03_build_lor_month_panel.py`.
2. The foundation panel feeds the temporal atlas; raw logs plus the tree/LOR crosswalk feed the positive tree-day product.
3. The executed exploratory, spatial and equity notebooks produce audits, descriptive tables, static maps, enriched GeoPackages and an interactive map.
4. Foundation, tree-day, equity and DWD products feed the monthly response report; the separately supplied monthly LST input adds a qualified Ortsteil extension.
5. `tools/build_examination.py` assembles an atlas and brief from the saved results and creates file/schema inventories. `tools/verify_examination.py` checks the package's links and frozen-file checksums.

See [the ordered reproduction guide](../examination/reproducibility.md). The examination builder does not fit new scientific models. Do not refresh source snapshots to reproduce this release; live services can change.

## Conventions

All analysis paths resolve from the repository root. Source files remain unchanged. Work in EPSG:25833 for area and distance, convert to EPSG:4326 for web display, and use Europe/Berlin calendar dates. Preserve identifiers as strings. Each analytical table must state its grain, period, zero semantics, denominator and claim limit.

`data/raw/tree_inventory/` holds the frozen compressed input and restoration manifest. The decompressed `data/Berlin_trees.gpkg` is ignored. `examination/data_inventory.csv` records files, sizes, hashes and row counts; `config/datasets.toml` records logical datasets and prospective inputs. A missing planned input must never be labelled available merely because a related aggregate exists.

`output/03_spatial_equity_vulnerability/` and `pillars/` retain historical names. The former contains valid descriptive temporal products; it does not mean the October allocation study is complete. Earlier Office drafts and local QA renders are excluded from publication in favour of the canonical examination copies.

Existing rebuilds may change timestamps or container-level GeoPackage bytes. Reproduction should compare scientific tables and audits; the release manifest instead verifies the exact packaged snapshot before rebuilding.
