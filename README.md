# Spatiotemporal Modeling of Citizen Tree Watering in Berlin

**Weather Responses and Neighborhood Variation**
Joseph Carpenter Sheils · Saarland University · M.Sc. Data Science and Artificial Intelligence

This repository supports a thesis on logged citizen tree watering, climate responses, vulnerability and municipal irrigation priorities in Berlin. The refined proposal of 26 October 2026 governs new work; the earlier seminar package remains a frozen record of preliminary evidence.

**Latest update — 2 November 2026:** [Project status](docs/project_update_2026_11_02.md) · [Earth Engine demo atlas](earth_engine/README.md) · [RQ1 daily results](output/rq1_daily/report.md) · [active analysis plan](docs/analysis_plan.md).

The first daily pilot contains **569,642 planning-area-days**, covering **55,634 linked April–September events** across 2020–2025. Citywide exploratory models find positive temperature/dry-spell associations and negative rainfall associations after calendar adjustment. These are log1p OLS descriptions, not the planned hierarchical count and volume models or causal effects.

Rebuild the daily pilot using the existing environment:

```bash
MPLCONFIGDIR=/tmp/berlin-rq1-mpl PYTHONPATH=src python pipelines/08_build_rq1_daily.py
PYTHONPATH=src python -m unittest tests.test_rq1_daily -v
```

No new downloads or dependencies are required. Known unavailable platform dates can be supplied through `--unavailable-dates dates.csv`; see the protocol.

## Interactive Earth Engine demo

Open the [launch guide](earth_engine/README.md), copy the complete [generated script](earth_engine/berlin_atlas_demo.js) into the [Earth Engine Code Editor](https://code.earthengine.google.com/), and press **Run** with an Earth Engine enabled account and Cloud project. The script embeds the project aggregates; no private asset upload is required.

Explore monthly watering across 542 neighbourhoods, click for area histories, compare social context, and inspect live Landsat surface temperature alongside valid-scene coverage. A separate daily RQ1 chart shows citywide events and station air temperature. Data totals and JavaScript syntax are checked; authenticated Earth Engine execution and App publication remain pending. The atlas is descriptive and does not estimate neighbourhood response slopes or allocation priorities.

## Start here

**[Examination reading guide](examination/README.md)** · **[Examination brief](output/pdf/Berlin_Examination_Brief_October_2026.pdf)**

| Material | Open |
| --- | --- |
| Active refined proposal | [Refined October proposal PDF](docs/proposal/Proposal_Refined_October_2026.pdf) · [version notes](docs/proposal/README.md) |
| Seminar proposal and qualifications | [October proposal PDF](examination/proposal/Proposal_October_2026.pdf) · [version and count notes](examination/proposal/README.md) |
| Seminar presentation | [Slides PDF](examination/proposal/Seminar_Slides_October_2026.pdf) · [editable Keynote](examination/proposal/Seminar_Slides_October_2026.key) |
| Preliminary evidence | [Results and sample reconciliation](examination/preliminary_results.md) · [detailed HTML report](output/watering_response/report.html) · [workbook](examination/results/Berlin_watering_monthly_exploration.xlsx) |
| Maps produced so far | [Twelve-plate PDF atlas](output/pdf/Berlin_Map_Atlas_October_2026.pdf) · [map catalogue with previews](examination/atlas/README.md) · [interactive LOR map](output/spatial/maps/lor_watering_interactive.html) |
| Data and provenance | [Data guide](data/README.md) · [checksummed inventory](examination/data_inventory.csv) · [dictionary](examination/data_dictionary.md) |
| Methods and feasibility | [Current analysis plan](docs/analysis_plan.md) · [readiness and next decisions](examination/readiness.md) · [literature context](docs/related_literature.md) |
| Reproduction | [Reproduction guide](examination/reproducibility.md) · [validation record](examination/validation.md) |

Download HTML files to view their rendered reports. The interactive map also requires internet access for its web resources. PDFs, PNGs, tables and the workbook provide static review routes.

## Current scope

The **[refined October 2026 proposal](docs/proposal/Proposal_Refined_October_2026.pdf)** governs active work. **Part II is the core study**: RQ1 climate response, RQ2 vulnerability/resource inequality and RQ3 additional spatial information. Part I supplies environmental context; Part III examines RQ4 allocation consequences. The examination documents retain the earlier proposal and numbering. The August conditional satellite test of watering-induced cooling is no longer the active design.

Implemented work is **preliminary and descriptive**. The canonical all-month May 2020–December 2025 panel has **57,786 linked events, 11,127 distinct trees and 2,249,502 recorded litres**, covering **542 planning areas and 68 months**. The daily RQ1 pilot uses the April–September subset. Existing results show seasonality, spatial clustering, social/environmental differences and exploratory monthly and daily weather associations. They do not establish causal cooling, daily neighbourhood response slopes, or a validated allocation model.

## Verify a checkout

Use Python 3.12. The large inventory is included as a lossless compressed snapshot; no separately supplied tree file is needed.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-spatial.txt
python tools/restore_tree_inventory.py
PYTHONPATH=src python -m berlin_heat status
PYTHONPATH=src python -m berlin_heat validate
PYTHONPATH=src python -m unittest discover -s tests -v
python tools/verify_examination.py
```

See the [reproduction guide](examination/reproducibility.md) for the ordered rebuild, optional PDF dependencies and exact scope of verification. Data sources retain their individual licences and caveats; the supplied monthly LST file and legacy district aggregates have unresolved provenance. Read [data/README.md](data/README.md) before reuse.

## Repository layout

- `examination/`: examiner guide, proposal, presentation, results, atlas catalogue, inventories and validation.
- `data/`: available source snapshots and processed shared panels.
- `output/`: executed notebooks, figures, tables, geospatial products, reports and examination PDFs.
- `src/berlin_heat/`, `pipelines/`, `analysis/`: reusable analysis code and builders.
- `earth_engine/`: self-contained demo script, editable UI, data builder and launch guide.
- `config/`, `tests/`: declared data contracts, research readiness and verification.
- `docs/archive/`, `pillars/`: historical design material, explicitly superseded where applicable.

**Interpretation:** logs record platform activity, not all irrigation. Current inventory counts are not historical risk sets. LST is surface temperature, not felt heat. Screening candidates are places for further validation, not recommendations to withdraw or redirect municipal care.
