# Spatiotemporal Modeling of Citizen Tree Watering in Berlin

**Weather Responses and Neighborhood Variation**
Joseph Carpenter Sheils · Saarland University · M.Sc. Data Science and Artificial Intelligence

This repository supports a thesis on logged citizen tree watering, climate responses, vulnerability and municipal irrigation priorities in Berlin. 

**latest update — 2 November 2026:** [Project status](docs/project_update_2026_11_02.md) · [Earth Engine demo atlas](earth_engine/README.md) · [RQ1 daily results](output/rq1_daily/report.md) · [active analysis plan](docs/analysis_plan.md).

The initial daily event study contains **569,642 planning-area-days**, covering **55,634 linked April–September events** across 2020–2025. Citywide exploratory models find positive temperature/dry-spell associations and negative rainfall associations after calendar adjustment. Initial exploration includes linear regression analysis of log(1+watering_events) to weather and calender features.

Rebuild the initial daily event study using the existing environment:

```bash
MPLCONFIGDIR=/tmp/berlin-rq1-mpl PYTHONPATH=src python pipelines/08_build_rq1_daily.py
PYTHONPATH=src python -m unittest tests.test_rq1_daily -v
```


## Interactive Earth Engine demo

Open the [launch guide](earth_engine/README.md), copy the complete [generated script](earth_engine/berlin_atlas_demo.js) into the [Earth Engine Code Editor](https://code.earthengine.google.com/), and press **Run** with an Earth Engine enabled account and Cloud project. The script embeds the project aggregates so only a copy-paste lets you see the atlas + layer.

Explore monthly watering across 542 neighbourhoods, click for area histories, compare social context, and inspect live Landsat surface temperature alongside valid-scene coverage. A separate daily RQ1 chart shows citywide events and station air temperature. 

## Start here

| Material | Open |
| --- | --- |
| Proposal | [Refined October 2026 proposal](docs/proposal/Proposal_Refined_October_2026.pdf) · [version notes](docs/proposal/README.md) |
| Plan and methods | [Active analysis plan](docs/analysis_plan.md) · [RQ1 daily protocol](docs/rq1_daily_exploratory_protocol.md) · [literature context](docs/related_literature.md) |
| Latest results | [RQ1 daily results](output/rq1_daily/report.md) · [project status, 2 November 2026](docs/project_update_2026_11_02.md) |
| Earlier exploratory results | [Monthly weather report](output/watering_response/report.html) · [map catalogue with previews](examination/atlas/README.md) · [interactive LOR map](output/spatial/maps/lor_watering_interactive.html) |
| Data and provenance | [Data guide](data/README.md) · [checksummed inventory](examination/data_inventory.csv) · [dictionary](examination/data_dictionary.md) |
| Reproduction | [Reproduction guide](examination/reproducibility.md) · [validation record](examination/validation.md) |
| Seminar examination, October 2026 | [Seminar package](examination/README.md): proposal, slides, plan, brief, atlas and preliminary results |

Download HTML files to view their rendered reports. The interactive map also requires internet access for its web resources. PDFs, PNGs, tables and the workbook provide static review routes.

## Current scope

The **[refined October 2026 proposal](docs/proposal/Proposal_Refined_October_2026.pdf)** governs active work. **Part II is the core study**: RQ1 climate response, RQ2 vulnerability/resource inequality and RQ3 additional spatial information. Part I supplies environmental context. Part III examines RQ4 allocation consequences. The [seminar package](examination/README.md) keeps the earlier proposal and its RQ numbering.

Implemented work is at a preliminary and descriptive stage. The canonical all-month May 2020–December 2025 panel has **57,786 linked events, 11,127 distinct trees and 2,249,502 recorded litres**, covering **542 Berlin planning areas and 68 months**. The daily RQ1 initial study uses an April–September subset. Existing results demonstrate seasonality, spatial clustering, social/environmental differences and exploratory monthly and daily weather associations. They do not establish causal cooling, daily neighbourhood response slopes, or a validated allocation model.

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

- `docs/`: refined proposal, active analysis plan, protocols and literature context.
- `examination/`: the October 2026 seminar package (proposal, slides, plan, brief, atlas, preliminary results), plus the data inventories and validation record.
- `data/`: available source snapshots and processed shared panels.
- `output/`: executed notebooks, figures, tables, geospatial products and reports.
- `src/berlin_heat/`, `pipelines/`, `analysis/`: reusable analysis code and builders.
- `earth_engine/`: self-contained demo script, editable UI, data builder and launch guide.
- `config/`, `tests/`: declared data contracts, research readiness and verification.

