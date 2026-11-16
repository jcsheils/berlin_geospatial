# Seminar examination package, October 2026

> This folder preserves the October 2026 seminar examination. The [refined proposal](../docs/proposal/Proposal_Refined_October_2026.pdf) and the [analysis plan](../docs/analysis_plan.md) now govern the thesis.

**Joseph Carpenter Sheils · Saarland University · M.Sc. Data Science and Artificial Intelligence**
**Prepared 17 October 2026 as preliminary evidence for project approval**

The seminar proposal, *Spatiotemporal Modeling of Citizen Tree Watering in Berlin: Weather Responses and Neighborhood Variation*, asks how logged watering responds to daily heat and dryness and how that response varies between neighbourhoods. The package shows data access, a working spatial and temporal foundation, and preliminary findings. The daily models, vegetation cooling-loss analysis and allocation comparison were not yet done.

## Reading order

| Material | Purpose |
| --- | --- |
| [Examination brief](Berlin_Examination_Brief_October_2026.pdf) | Short overview of research, evidence, feasibility and remaining work |
| [Seminar proposal](proposal/Proposal_October_2026.pdf) and [version notes](proposal/README.md) | The seminar design, with count reconciliation and qualifications |
| [Slides](proposal/Seminar_Slides_October_2026.pdf) and [Keynote source](proposal/Seminar_Slides_October_2026.key) | The seminar presentation |
| [Seminar analysis plan](analysis_plan_october_2026.md) | The plan that accompanied the proposal |
| [Preliminary results](preliminary_results.md) | Findings linked to tables, figures and code |
| [Map atlas](atlas/Berlin_Map_Atlas_October_2026.pdf) and [catalogue](atlas/README.md) | Twelve map plates with periods, definitions, methods and limits |
| [Data guide](../data/README.md), [file inventory](data_inventory.csv) and [dictionary](data_dictionary.md) | Inputs and products, attribution, checksums, units and missingness |
| [Reproduction guide](reproducibility.md), [validation record](validation.md) and [readiness assessment](readiness.md) | How to verify the package and what remained before final inference |

The [monthly weather report](../output/watering_response/report.html) and [workbook](results/Berlin_watering_monthly_exploration.xlsx) hold detailed exploratory results, including the provisional Ortsteil LST extension. Download HTML files to view them; the [interactive LOR map](../output/spatial/maps/lor_watering_interactive.html) also loads external map resources.

## Scope

In the seminar proposal, Part II is the core **behavioural response** study, Part I covers drought-related vegetation cooling loss, and Part III is an exploratory allocation comparison. The equity maps give context and show feasibility; they are not the October Part III. Folder names such as `output/03_spatial_equity_vulnerability/` stay unchanged so links keep working.

The records describe **logged citizen care**: not total irrigation, volunteer identities, municipal service or causal cooling. Surface and station air temperature are separate measurements, missing logs do not show an absence of watering, and current-inventory denominators are not historical populations.

The package demonstrates preliminary feasibility. Approval rests with the seminar examiners.
