# Master's Seminar examination package

**Joseph Carpenter Sheils · Saarland University · M.Sc. Data Science and Artificial Intelligence**
**Prepared 17 October 2026 · Preliminary evidence for project approval**

The proposed thesis is **Spatiotemporal Modeling of Citizen Tree Watering in Berlin: Weather Responses and Neighborhood Variation**. Its core study asks how logged watering responds to daily heat and dryness and how that response varies between neighbourhoods. The repository establishes access to the data, a working spatial and temporal foundation, and preliminary findings that motivate the daily study. The planned daily models, vegetation cooling-loss analysis, and allocation comparison have not yet been completed.

## Suggested reading order

| Material | Purpose |
| --- | --- |
| [Examination brief](../output/pdf/Berlin_Examination_Brief_October_2026.pdf) | A short overview of the research, evidence, feasibility, and remaining work |
| [October proposal](proposal/Proposal_October_2026.pdf) and [version notes](proposal/README.md) | The governing research design, with count reconciliation and qualifications |
| [October seminar slides](proposal/Seminar_Slides_October_2026.pdf) | The presentation accompanying the revised proposal |
| [Preliminary results](preliminary_results.md) | Findings linked directly to tables, figures, and analysis code |
| [Map atlas](../output/pdf/Berlin_Map_Atlas_October_2026.pdf) and [online catalogue](atlas/README.md) | Twelve existing map plates, periods, definitions, methods, and limitations |
| [Data guide](../data/README.md), [file inventory](data_inventory.csv), and [dictionary](data_dictionary.md) | Available inputs and products, source attribution, checksums, units, and missingness |
| [Reproduction guide](reproducibility.md) and [readiness assessment](readiness.md) | How to verify the package and what remains before final thesis inference |

The [monthly weather report](../output/watering_response/report.html) and [workbook](results/Berlin_watering_monthly_exploration.xlsx) provide detailed exploratory results, including the provisional Ortsteil LST extension. Download HTML files and open them locally; GitHub displays their source. The [interactive LOR map](../output/spatial/maps/lor_watering_interactive.html) additionally uses external web map resources.

## Scope and claim boundary

The October proposal supersedes the August design. Part II is the core **behavioural response** study; Part I concerns drought-related vegetation cooling loss; Part III is an exploratory allocation comparison. Existing equity maps support context and feasibility; they are not the completed October Part III. Existing directory names such as `output/03_spatial_equity_vulnerability/` are retained so analysis links remain stable.

The records describe **logged citizen care**, not total irrigation, volunteer identities, municipal service provision, or causal cooling. Surface temperature and station air temperature remain separate measurements. Missing logs do not demonstrate absence of watering. Current-inventory denominators are not historical eligible-tree populations.

The submission demonstrates preliminary feasibility, not completion of the proposed thesis or a guarantee of examination approval. Institutional submission requirements and approval remain with the seminar examiners.
