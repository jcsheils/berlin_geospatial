# Reproduction guide

This guide rebuilds the saved analyses from frozen source snapshots. Verify the frozen files **before** you rebuild: a rebuild can change timestamps or GeoPackage container bytes even when the scientific values agree. Planned models are not part of this route.

## Build flow

1. Source logs, the restored tree inventory and LOR geometry feed `pipelines/03_build_lor_month_panel.py`, which writes the foundation panel and the tree-to-LOR crosswalk.
2. The foundation panel feeds the temporal atlas (`04`). Raw logs plus the crosswalk feed the positive tree-day product (`05`).
3. The exploratory, spatial and equity notebooks produce audits, descriptive tables, static maps, enriched GeoPackages and the interactive map.
4. Foundation, tree-day, equity and DWD products feed the monthly weather report (`06`). The supplied monthly LST file adds the Ortsteil extension (`07`).
5. The RQ1 pilot (`08`) builds the daily panel and citywide fits from the logs, crosswalk, tree-day product and DWD archive.
6. `tools/build_examination.py` assembled the October atlas, brief and inventories from saved results. `tools/verify_examination.py` checks links and frozen-file checksums.

## Conventions

- Resolve every path from the repository root, and never modify source files.
- Work in EPSG:25833 for area and distance, convert to EPSG:4326 for web display, and use Europe/Berlin dates.
- Read identifiers as strings.
- Each analytical table states its grain, period, zero semantics, denominator and claim limit.
- `examination/data_inventory.csv` records files, sizes, hashes and row counts; `config/datasets.toml` records logical datasets and planned inputs. Never label a planned input available just because a related aggregate exists.
- `output/03_spatial_equity_vulnerability/` keeps an older name. It holds valid descriptive temporal products and does not mean the allocation study is done.
- Do not refresh source snapshots to reproduce a release, because live services change.

## 1. Environment and frozen inputs

From the repository root, with Python 3.12:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-spatial.txt
python tools/restore_tree_inventory.py
python tools/verify_examination.py
```

The restore script uses only the standard library, checks compressed and uncompressed hashes, and refuses to overwrite a different inventory. The restored file needs about 335 MB. SHA-256 fixes the archive's identity, although its acquisition history is incomplete. `requirements-spatial.txt` pins the analysis dependencies but is not a full system lockfile; [validation.md](validation.md) lists the tested environment.

## 2. Validate existing products

```bash
PYTHONPATH=src python -m berlin_heat status
PYTHONPATH=src python -m berlin_heat validate
PYTHONPATH=src python -m unittest discover -s tests -v
```

Warnings about the source CRS, denominators, missing historical inputs and unverified LST processing are expected. Passing contract checks does not validate a planned model.

## 3. Rebuild the descriptive notebooks

The frozen LOR and equity inputs are included. Skip the live equity downloader when reproducing the release, since it fetches a later source state. Run the notebooks in this order, because later ones read earlier outputs:

```bash
python analysis/build_exploratory_notebook.py
jupyter nbconvert --to notebook --execute output/jupyter-notebook/berlin-urban-heat-exploration.ipynb --inplace --ExecutePreprocessor.timeout=1200
python analysis/build_spatial_notebook.py
jupyter nbconvert --to notebook --execute output/jupyter-notebook/berlin-lor-spatial-watering.ipynb --inplace --ExecutePreprocessor.timeout=1200
python analysis/build_equity_notebook.py
jupyter nbconvert --to notebook --execute output/jupyter-notebook/berlin-lor-equity-environment.ipynb --inplace --ExecutePreprocessor.timeout=1200
```

Local Moran classifications use seed 42.

## 4. Rebuild temporal and weather products

```bash
python pipelines/03_build_lor_month_panel.py
python pipelines/04_build_watering_temporal_atlas.py
python pipelines/05_build_recorded_tree_day.py
python analysis/build_watering_response_report.py
```

The last command builds the monthly weather results and, when the supplied Ortsteil file is present, the provisional LST extension.

## 5. Rebuild the RQ1 daily pilot

```bash
MPLCONFIGDIR=/tmp/berlin-rq1-mpl PYTHONPATH=src python pipelines/08_build_rq1_daily.py
```

The pipeline needs no network access or extra dependencies. `output/rq1_daily/metadata.json` records the SHA-256 of every input, the code and the [protocol](../docs/rq1_daily_exploratory_protocol.md), plus Python, NumPy and pandas versions, so editing the protocol requires a rerun.

| Output | Contents |
| --- | --- |
| `data/processed/rq1/lor_day_recorded_watering_apr_sep_2020_2025.csv.gz` | 542 areas × 1,051 days: events, litres, distinct trees, coverage flag, current stock |
| `output/rq1_daily/tables/daily_weather_features.csv` | Full 2020–2025 weather calendar with strictly antecedent features; joins to area-days by `date` |
| `output/rq1_daily/tables/city_day_*.csv` | Linked baseline, exclusion of events above 500 L, all valid source logs |
| `output/rq1_daily/tables/annual_summary.csv` | Sample sizes, seasonal distinct trees, dispersion, sparsity, timestamp precision |
| `output/rq1_daily/tables/model_coefficients.csv` | 216-row coefficient grid for three outcomes, in log1p units |
| `output/rq1_daily/model_audit.json` | Dates in and out of each fit; design condition numbers |
| `output/rq1_daily/report.md` | Findings, figures, sensitivity summaries, limits |

To mask a known outage calendar, pass `--unavailable-dates path/to/dates.csv` with a unique `date` column. Outcome columns become missing on those dates while `extract_events`, `extract_litres` and `extract_distinct_trees` keep the raw counts. No outage file exists for the default build, and the pipeline never infers outages from zero logs or writes pre-launch dates as zeros.

## 6. Other builders

- **Benchmarks:** `python analysis/build_feedback_benchmarks.py` writes `output/feedback_benchmarks/benchmarks.json`. It reads the versioned 2025 inventory extract; `python tools/extract_tree_inventory_2025.py` rebuilds that extract from its pinned archive and needs network access.
- **RQ3 one-year survival test:** `python -m analysis.rq3_one_year_survival design` writes the sample and detectability without opening outcome data. The `outcome` stage needs the 2026 inventory (`--inventory`) and runs only while the [protocol](../docs/rq3_one_year_survival_protocol.md) matches its hash in `config/project.toml`.
- **RQ3 four-year projection:** `python -m analysis.rq3_four_year_projection` projects the sample and detectability of the [draft four-year plan](../docs/rq3_four_year_survival_protocol.md) from the 2025 inventory and the open log export, without opening removal data.
- **RQ3 crown-health projection:** `python -m analysis.rq3_crown_health_projection` counts the trees and detectable differences of the [draft crown-health plan](../docs/rq3_crown_health_protocol.md) without opening any aerial image.
- **RQ3 crown-health extraction:** the [workflow](../.github/workflows/rq3-crown-health.yml) runs `analysis/rq3_crown_health_extract.py` on GitHub Actions and reads each flight through Berlin's map service, keeping only per-tree circle means. It refuses to run until the plan is frozen. `python -m analysis.rq3_crown_health_extract plan` counts the request windows offline.
- **Earth Engine atlas:** `python earth_engine/build_demo.py` regenerates `earth_engine/berlin_atlas_demo.js`; see the [launch guide](../earth_engine/README.md).
- **Examination PDFs:** `python -m pip install -r requirements-examination.txt`, then `python tools/build_examination.py`. It rebuilt the October atlas, brief, results page and inventories from saved images and tables. It fits no models and leaves the proposal, slides and workbook untouched. Running it now would also rewrite the release manifest's scope, so do not use it for routine updates.

## Release manifest

`examination/release_manifest.json` lists each packaged file with its size and SHA-256, and `tools/verify_examination.py` checks them. After a deliberate edit to a listed file, refresh the changed entries in place:

```bash
python tools/verify_examination.py --refresh
```

Review the diff before committing. A hash mismatch never justifies replacing a source snapshot.

## Not reproduced

The balanced daily main model, historical young-tree eligibility, vegetation cooling loss, predictive calibration, allocation comparison and bridge test are future work. The proposal's Appendix A is design rationale, not a reproduced experiment. External basemap tiles are not frozen; use the static atlas for a stable view. The workbook is a frozen presentation copy, readable in Excel or LibreOffice, and no pipeline rebuilds it.
