# Spatiotemporal Modeling of Citizen Tree Watering in Berlin

**Weather Responses and Neighborhood Variation**
Joseph Carpenter Sheils · Saarland University · M.Sc. Data Science and Artificial Intelligence

This repository supports a thesis on Gieß den Kiez, Berlin's citizen tree-watering platform, as co-produced climate adaptation. The thesis asks how citizen watering responds to drought, which public levers steer it, which trees and neighbourhoods it reaches, and what it does for young street trees.

## Start here

| Topic | Documents |
| --- | --- |
| Research design | [Analysis plan](docs/analysis_plan.md) · [revised research questions](docs/revised_research_design_2026_11.md) · [refined proposal](docs/proposal/Proposal_Refined_October_2026.pdf) ([version notes](docs/proposal/README.md)) |
| Evidence so far | [Policy-relevance benchmarks](docs/policy_feedback_2026_11.md) · [RQ1 daily results](output/rq1_daily/report.md) · [monthly weather report](output/watering_response/report.html) · [map atlas](examination/atlas/README.md) |
| Methods and literature | [RQ1 daily protocol](docs/rq1_daily_exploratory_protocol.md) · [temporal protocol](docs/temporal_analysis_protocol.md) · [monthly response protocol](docs/watering_response_exploratory_protocol.md) · [related literature](docs/related_literature.md) |
| Data | [Data guide](data/README.md) · [dictionary](examination/data_dictionary.md) · [checksummed inventory](examination/data_inventory.csv) |
| Reproduction | [Reproduction guide](examination/reproducibility.md) · [validation record](examination/validation.md) |
| Interactive maps | [Earth Engine atlas](earth_engine/README.md) · [LOR web map](output/spatial/maps/lor_watering_interactive.html) |
| Seminar, October 2026 | [Examination package](examination/README.md) (earlier proposal, slides, brief and atlas) |

GitHub shows HTML files as source code, so download them to view the reports. The LOR web map also loads tiles from the internet.

## Research questions

The [analysis plan](docs/analysis_plan.md) governs current work. It applies the refined October 2026 proposal as amended by the [November 2026 revision](docs/revised_research_design_2026_11.md):

- **RQ1, drought response:** how logged watering responds to heat, rain and dry spells;
- **RQ2, levers and reach:** how street pumps and municipal-care age limits shift citizen watering, and whom it reaches;
- **RQ3, tree outcomes:** survival and condition of young street trees;
- **RQ4, scenarios:** scaling, targeting and funding the platform.

Part I's vegetation cooling estimates feed the RQ4 scenarios. The seminar package keeps its own earlier RQ numbering.

## Current results

All results so far are descriptive. The canonical panel covers May 2020 to December 2025: **57,786 linked events, 11,127 distinct trees and 2,249,502 litres** across **542 planning areas and 68 months**.

The RQ1 daily pilot uses an April–September subset of **569,642 planning-area-days** and **55,634 events**. After calendar adjustment, logged watering rises with temperature and dry spells and falls with rain. The pilot fits citywide OLS models of log(1 + daily totals), not the hierarchical models the plan calls for.

The repository also documents seasonality, spatial clustering, social and environmental differences, and monthly weather associations. It does not yet estimate causal cooling, effects on tree survival, neighbourhood response slopes or an allocation model.

## Quick start

You need Python 3.12. The tree inventory ships as a compressed snapshot, so you need no extra downloads.

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

To rebuild the RQ1 pilot:

```bash
MPLCONFIGDIR=/tmp/berlin-rq1-mpl PYTHONPATH=src python pipelines/08_build_rq1_daily.py
```

The [reproduction guide](examination/reproducibility.md) gives the full build order. Each data source keeps its own licence. The supplied monthly LST file and the legacy district aggregates have unresolved provenance, so read the [data guide](data/README.md) before reusing them.

## Layout

| Folder | Contents |
| --- | --- |
| `docs/` | Analysis plan, revised design, benchmarks memo, protocols, literature, refined proposal |
| `src/berlin_heat/` | Package: data contracts, panel builders, RQ1 pilot, CLI |
| `pipelines/` | Numbered build scripts (03–08) for the shared panels and RQ1 |
| `analysis/` | Notebook, report and benchmark builders |
| `data/` | Frozen source snapshots and processed panels |
| `output/` | Executed notebooks, figures, tables, maps and reports |
| `earth_engine/` | Earth Engine atlas script, its UI source and builder |
| `examination/` | October 2026 seminar package, data inventory, dictionary and validation record |
| `config/`, `tests/`, `tools/` | Dataset contracts, tests, inventory restore and package verification |
