# Spatiotemporal Modeling of Citizen Tree Watering in Berlin

**Weather Responses and Neighborhood Variation**
Joseph Carpenter Sheils · Saarland University · M.Sc. Data Science and Artificial Intelligence

This repository supports the Master's Seminar examination of a proposed thesis on logged citizen tree watering, heat, and neighbourhood differences in Berlin. It contains the October 2026 proposal, preliminary results, a map atlas, frozen input data, derived tables and spatial layers, and reproducible analysis code.

## Start here

**[Examination reading guide](examination/README.md)** · **[Examination brief](output/pdf/Berlin_Examination_Brief_October_2026.pdf)**

| Material | Open |
| --- | --- |
| Current proposal and qualifications | [October proposal PDF](examination/proposal/Proposal_October_2026.pdf) · [version and count notes](examination/proposal/README.md) |
| Seminar presentation | [Slides PDF](examination/proposal/Seminar_Slides_October_2026.pdf) · [editable Keynote](examination/proposal/Seminar_Slides_October_2026.key) |
| Preliminary evidence | [Results and sample reconciliation](examination/preliminary_results.md) · [detailed HTML report](output/watering_response/report.html) · [workbook](examination/results/Berlin_watering_monthly_exploration.xlsx) |
| Maps produced so far | [Twelve-plate PDF atlas](output/pdf/Berlin_Map_Atlas_October_2026.pdf) · [map catalogue with previews](examination/atlas/README.md) · [interactive LOR map](output/spatial/maps/lor_watering_interactive.html) |
| Data and provenance | [Data guide](data/README.md) · [checksummed inventory](examination/data_inventory.csv) · [dictionary](examination/data_dictionary.md) |
| Methods and feasibility | [Current analysis plan](docs/analysis_plan.md) · [readiness and next decisions](examination/readiness.md) · [literature context](docs/related_literature.md) |
| Reproduction | [Reproduction guide](examination/reproducibility.md) · [validation record](examination/validation.md) |

Download HTML files to view their rendered reports. The interactive map also requires internet access for its web resources. PDFs, PNGs, tables and the workbook provide static review routes.

## Current scope

The **October 2026 proposal** governs this package. **Part II is the core study**: daily civic heat response and its relationship to neighbourhood status and baseline participation. Part I investigates drought-related vegetation cooling loss; Part III explores allocation around expected logged care. The August conditional satellite test of watering-induced cooling is no longer the active design.

Implemented work is **preliminary and descriptive**. The canonical May 2020–December 2025 panel has **57,786 linked events, 11,127 distinct trees and 2,249,502 recorded litres**, covering **542 planning areas and 68 months**. Existing results show seasonal concentration, spatial clustering, social/environmental differences and exploratory monthly weather associations. They do not establish causal cooling, daily neighbourhood response slopes, or a validated allocation model.

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
- `config/`, `tests/`: declared data contracts, research readiness and verification.
- `docs/archive/`, `pillars/`: historical design material, explicitly superseded where applicable.

**Interpretation:** logs record platform activity, not all irrigation. Current inventory counts are not historical risk sets. LST is surface temperature, not felt heat. Screening candidates are places for further validation, not recommendations to withdraw or redirect municipal care.
