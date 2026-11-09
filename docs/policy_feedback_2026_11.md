# Policy relevance: first numbers and design options

*Gieß den Kiez citizen tree watering in Berlin · discussion draft · November 2026*

Ideally, the design pairs **an outcome tied to a healthy city with treatment variables the city can control**. This note sets out the policy questions that follow from that aim, gives first order-of-magnitude answers from data already in the repository and compares design options. The [active analysis plan](analysis_plan.md) stays unchanged until a framing is chosen.

Numbers come from [`analysis/build_feedback_benchmarks.py`](../analysis/build_feedback_benchmarks.py) and are written to `output/feedback_benchmarks/benchmarks.json`. To rebuild, run `python tools/restore_tree_inventory.py`, then `python analysis/build_feedback_benchmarks.py`. Figures attributed to districts are taken from parliamentary answers and serve as illustrations, not a citywide audit. Logs record platform activity only, and the current inventory is not a historical stock.

## Summary

1. **A healthy-city outcome reverses the direction of the design.** At present, logged care is the outcome. In the ideal design, a city lever changes the water trees receive, and tree condition is the outcome. RQ1 remains useful as the first stage: it describes when logged care happens.
2. **Logged watering is small in every comparison.** Since 2020, 1.2% of catalogued trees have been watered at least once, and 0.1–0.45% per season. The median watered tree receives 60 L per season, about 1% of the rain falling on its own crown. A single district's young-tree programme delivers 3–36 times the platform's citywide volume. Platform water is below 0.0004% of public supply.
3. **Area-level greenness analyses cannot detect plausible effects.** In a typical planning area, 0.14% of street trees are watered in a season. A per-tree effect would therefore have to be 0.08–0.25 NDVI to show at area level. Tree-level designs have enough trees; their binding constraints are pixel size for young trees and selection of watered trees.
4. **Street pumps are the most promising city lever.** Location and repair history are under city control, and a pump → tree-condition design captures logged and unlogged pump water together.
5. **City-wide green cover is the wrong scale-up outcome.** Street trees aged 15 or younger hold about 2% of recorded street-tree crown area. Scaling participation would pay off through young-tree survival and later canopy growth, so a survival or vitality dose-response is the missing link.

## 1. How the design changes

```text
City levers ──► water a tree receives ──────────────► tree condition ──► canopy, cooling
(pumps, municipal    (logged platform + unlogged         (vitality, greenness,   (decades)
 watering, aids,      + municipal + rain/groundwater)     survival)
 campaigns, funding,
 planting)
```

The refined proposal covers the arrow into *logged* watering (RQ1–RQ2) and simulated allocation (RQ4). It has no tree-condition outcome, and Appendix A rules out only the satellite-cooling version of that question.

## 2. First numbers

### Reach: what share of Berlin's trees does the platform reach?

| Measure | Value |
| --- | --- |
| Distinct trees with a linked log, May 2020–Dec 2025 | 11,127 = **1.2%** of 956,347 catalogued trees |
| Street trees / catalogued green-space trees | 10,299 = 2.4% of 433,176 / 828 = 0.16% of 523,171 |
| Trees watered per April–September season | 1,018 (2024) to 4,343 (2020): 0.1–0.45% of catalogued, 0.2–0.9% of street trees |
| Street trees aged ≤ 15 reached per season | 0.8–1.9% |
| Watered trees logged in only one season | 78% |
| Litres received by the top 10% of watered trees | 58% |
| Planning-area seasons (≥ 50 street trees) with no watered street tree | 44%; median reach 0.14%, 90th percentile 2.2% |
| Cumulative street-tree reach by district | Friedrichshain-Kreuzberg 8.4%, Mitte 5.9%, Tempelhof-Schöneberg 3.9% … Spandau 0.5%, Marzahn-Hellersdorf 0.3% |

Forest covers 15,800 ha, 17.7% of Berlin's 89,112 ha (end of 2025). Forest trees are absent from the catalogue and from the platform, and the green-space layer is incomplete. Counting every tree in the city, the platform reaches far less than 1% of trees. Recorded crowns sum to 16.7 km² for street trees and 19.8 km² for catalogued green-space trees; crown diameter is missing for 28% of street trees and 35% of green-space trees. Street trees aged ≤ 15 account for 0.29 km².

### Dose: what does a watered tree receive?

- The median watered tree-season receives **60 L** (mean 148 L, 90th percentile 350 L). Half of watered tree-seasons have only one logged day.
- Trees aged ≤ 15 receive a median of 90 L, and 8% reach 500 L.
- District guidance is 70–100 L per young tree per week (Charlottenburg-Wilmersdorf, Drucksache 19/16001), or 1,400–2,600 L over a 20–26-week season.
- Municipal programmes give 6–13 waterings of 80–200 L each, about 500–2,600 L per tree per season. Pankow, Neukölln, Treptow-Köpenick, Lichtenberg and Reinickendorf water young trees to the 10th year after planting. Friedrichshain-Kreuzberg and Tempelhof-Schöneberg water to 12 years, and Steglitz-Zehlendorf waters poor sites to 15 years.
- 24% of watered tree-seasons involve trees ≤ 10 years old, which are within municipal-care age; 16% are aged 11–20 and 60% are older than 20.

### Water budget: rainfall, municipal watering and public supply

Per watered tree, April–September (Tempelhof station):

| Quantity | Value |
| --- | --- |
| Logged platform water (median) | 60 L; 90 L for trees ≤ 15 |
| Rain on a 6 m² tree pit | 1,300–1,800 L (221–295 mm in 2020–2025; 1991–2020 mean 315 mm) |
| Logged water as share of rain on the tree's own crown footprint | 1.1% (median; median crown 28 m², or 7 m² for trees ≤ 15) |
| Climatic deficit, reference ET₀ minus rain | 230–480 mm depending on year and method; logged water ≈ 0.6% of the Hargreaves deficit over the crown, ≈ 3% for trees ≤ 15 (higher with Turc–Wendling) |
| Municipal young-tree dose | ≈ 500–2,600 L |

Citywide, per season:

| Quantity | Litres |
| --- | --- |
| All platform logs | 0.16–0.76 million |
| One district's young-tree programme (Lichtenberg, Tempelhof-Schöneberg 2023, Reinickendorf 2021; derived from stated trees, rounds and volumes) | 2.6–5.8 million each |
| Guidance need of all 50,180 street trees aged ≤ 15 | 70–130 million |
| Water sold by Berliner Wasserbetriebe, 2021 | 215,000 million; platform logs ≈ 0.0001–0.0004% of this |

If all twelve districts ran programmes of this size, platform logs would equal roughly 0.2–2.5% of municipal young-tree watering. District watering records are needed to replace this extrapolation.

ET₀ uses Turc–Wendling with sunshine duration where available (2020–2022) and Hargreaves otherwise. Hargreaves overstates ET₀ in humid climates and serves as an upper bound.

### Costs: should the city fund such initiatives?

- Contracted watering costs about **€7–12 per tree-watering**. Lichtenberg paid €101,000 for 1,093 trees × 13 rounds; Reinickendorf €240,120 for 25,764 waterings in 2021; Tempelhof-Schöneberg states €9–12. At 80–150 L per watering, that is ≈ €0.05–0.15 per litre.
- At these rates, logged volunteer water was worth **€38k–115k in 2022** and €8k–25k in 2024–2025. This is an upper bound, because small doses may be worth less per litre.
- A new street tree with about three years of establishment care costs **≈ €3,000** (Stadtbaumkampagne, autumn 2022 tender). Each young-tree loss avoided therefore saves at least this amount.
- The funding question becomes a break-even comparison: platform and campaign costs against the water's replacement value, avoided losses × €3,000 and non-water benefits such as damage reports. The thesis can estimate the first two benefit terms with uncertainty. Platform costs must come from CityLAB.

### Statistical significance versus practical relevance

In the RQ1 pilot, logged litres rise by 0.645 log1p units per +5 °C (95% interval 0.53–0.76), which is statistically clear. At the season mean of about 2,100 logged L per day, a 5 °C warmer day adds roughly **1,900 L citywide**. That is about 0.3% of the daily guidance need of street trees aged ≤ 15 (0.50–0.72 million L). Proposal: report every effect in policy units (litres, trees reached, share of need, euros). Also pre-specify a smallest effect of interest for each question, and use equivalence bounds so that a null result states which effects it rules out.

### Population density

| Density quintile (median residents/km²) | Watered trees per 100 street trees, 2020–2025 (median) |
| --- | ---: |
| Q1 (1,600) | 0.38 |
| Q2 (4,400) | 1.06 |
| Q3 (9,000) | 1.25 |
| Q4 (13,900) | 2.74 |
| Q5 (20,900) | 7.71 |

Across 531 planning areas, Spearman correlations with this reach measure are 0.56 for density, 0.36 for residents per street tree and 0.01 for the MSS status index. These are descriptive and confounded with inner-city location.

## 3. How large must an effect be to be detected?

All minimum detectable effects (MDE) below assume 80% power at α = 0.05. The standard deviations are placeholders to be replaced by pre-2020 Sentinel-2 estimates.

- **Planning areas (542).** An area-mean NDVI change dilutes a per-tree effect by the watered share, which has a median of 0.14%. For one season, the MDE per watered tree is **0.08, 0.17 or 0.25 NDVI** for area-level residual SDs of 0.01, 0.02 or 0.03. Pooling six seasons lowers this by at most √6. Young crowns cover about 7% of a 10 m pixel (IQR 3–14%), so the required crown-level effect would exceed 1 NDVI. Area-level greenness regressions can only produce uninformative nulls or spurious associations, so they should not be run.
- **Single trees, Sentinel-2.** With 1,000–4,000 watered trees per season and five matched controls each, the MDE in pixel NDVI change is about **0.0015–0.013** (SD 0.03–0.08; design effect 1–3 for clustering by street or volunteer). Mature crowns roughly fill a pixel and this precision suffices, but their median seasonal dose of 50–60 L is negligible against their water use. For young trees, the crown-level MDE is about 0.02–0.2, so finer imagery is needed. Options are 20 cm RGBI orthophotos, whose flight dates must be checked (catalogue entries found so far: 22 February 2021 and 22 April 2023, both before full leaf-out), PlanetScope at 3 m, or the Senate's summer colour-infrared flights. At tree level, the binding problem is selection of watered trees, not sample size.
- **Senate vitality survey.** The colour-infrared survey covers inner-city street trees planted before 1990, in 2020 and 2025, with about 5,000 trees reported. If 2–5% of surveyed trees were watered, the MDE for a difference in the share whose vitality declined is about **7–13 percentage points**. The survey covers mature trees only, and tree-level data would have to be requested.

Cross-sectional comparisons ("higher NDVI where more is watered") are not interpretable. Volunteers may favour visibly stressed trees, which biases the comparison negatively. They may also favour well-kept streets, which biases it positively. Watering also comes bundled with other care.

## 4. Question by question

| Question | Answer now | What a full answer needs | Where it fits |
| --- | --- | --- | --- |
| Knobs the city can tune | Municipal young-tree watering (rounds, dose, age cut-off of 10, 12 or 15 years); street pumps (about 2,100; 1,614 of 2,079 working in 2022); watering bags and rings; species and pit volume; district appeals; platform funding; water source (wells, rainwater) | Pump status history (OSM edits, BWB register), dated district appeals, district watering lists | RQ2 reframed around levers |
| Does the initiative affect urban greening? | Not identifiable at area level (Section 3) | Tree-level designs: staggered before/after first watering against matched unwatered trees (Sentinel-2 2017–2025); dry-season contrast (2022 against 2021/2023); pump-access reduced form | New tree-condition RQ |
| Should the city fund it? | Break-even framing (Section 2) | Platform costs; survival effect | Scenario RQ |
| Scaling to 100k participants | Per-person volume is unknown (no user IDs). At 100, 500 or 2,000 L per person and season, total logs would be 10, 50 or 200 million L: 8–14%, 38–71% or over 150% of young street trees' guidance need, and 0.005%, 0.02% or 0.09% of public supply. Today trees aged ≤ 20 account for only 40% of watered tree-seasons and 45% of logged litres. | User-ID distribution; targeting assumptions; survival dose-response to turn water into canopy | Scenario RQ |
| Share of water compared with public services, rain and municipal watering | Section 2: ≈ 1% of rain on the crown, 0.2–2.5% of plausible municipal volume, < 0.0004% of public supply | District watering records | Descriptive chapter |
| Statistical significance against practical relevance | Section 2: heat response is significant but equals ≈ 0.3% of young-tree daily need | Smallest effects of interest and equivalence bounds in the registered plan | All RQs |
| How watering matters for tree health | Districts water young trees for about 10 years because they depend on it. Older trees should mostly supply themselves. Logged doses are mostly far below guidance, so effects should concentrate in ages 4–20 in dry seasons. | Literature review on establishment, irrigation and mortality; QTrees and district moisture-sensor data | Background and tree-condition RQ |
| Tree health as outcome; effect size given sample size | Section 3 | Pre-2020 Sentinel-2 extraction to fix the noise SD and clustering | Tree-condition RQ |
| Share of trees reached | Section 2: 1.2% of catalogued trees cumulatively, 0.1–0.45% per season | — | Descriptive chapter |
| Most trees are in forests and parks | Forest is 17.7% of the city's area and uncatalogued; the green-space layer is incomplete | Express effects relative to street trees in dense areas, not city green cover | Framing |
| Drinking-water trade-off at scale | Annual volumes are negligible against supply. Binding constraints are likely heat-wave peak demand, pump availability (street pumps draw groundwater), groundwater in dry years and volunteer time. | BWB peak-demand and groundwater context | Scenario RQ |
| Overlay voting areas in Earth Engine | Feasible. Build the precinct-to-LOR crosswalk in Python (area- or population-weighted) and embed the results as LOR attributes in the existing atlas. Postal votes are counted in larger postal districts, so polling-station turnout alone misstates local turnout. | Precinct and postal-district geometries and results, 2021, 2023, 2025 | RQ2 covariates; atlas layer |
| Population density and voting in regressions | Density is already an area covariate in Appendix B. Add residents per street tree, and turnout (environmental-party share as a sensitivity). Check collinearity with MSS status; interpret at area level only. | Crosswalk above | RQ1–RQ2 models |
| Low signal-to-noise; unlogged, private and municipal watering; groundwater and lakes | Model behaviour at Bezirksregion scale. Keep tree outcomes at tree level in high-signal strata (dry seasons, ages 4–20, high-dose trees). The pump reduced form covers unlogged pump water. Municipal confounding is concentrated at ages ≤ 10–12, so compare within age bands. Bound unlogged watering in sensitivity analyses; add distance to water bodies and depth to groundwater as covariates. | District lists; groundwater layer (Umweltatlas) | All RQs |

## 5. Design options

| Option | Content | Risk |
| --- | --- | --- |
| A. Keep the design and add a policy chapter | Sections 2–3, extended and sourced | Low; still no healthy-city outcome |
| **B. Reframe (recommended)** | RQ1 unchanged (first stage, pilot done). RQ2: levers and access (pumps, municipal-care age, density and participation context). RQ3: tree condition at tree level with registered detectability. RQ4: scale-up and funding scenarios, with need-only against citizen-informed allocation as one scenario. Part I cooling loss shrinks to context. | Medium; depends on imagery and data access |
| C. Full pivot | Tree condition as the only outcome; RQ1 becomes background | High; selection, imagery access and likely nulls |

Under option B, a go/no-go decision would follow two steps: the pre-period Sentinel-2 extraction, which sets the MDE, and the replies to the data requests below.

## 6. Data requests

- **CityLAB / Technologiestiftung:** pseudonymous user IDs, adoption records, historical tree tables (removals give survival), platform running costs.
- **District street and green-space offices:** municipal watering lists for 2020–2025 (tree or street, dates, rounds, volumes); GRIS felling records with dates and reasons. The Senate keeps no statistic on young trees that dried out (Drucksache 19/13426).
- **Senate environment department:** tree-level colour-infrared vitality data for 2020 and 2025; moisture-sensor series.
- **BWB and districts:** street-pump status history and repair dates.
- **State election office / Statistik Berlin-Brandenburg:** precinct and postal-district geometries and results.

## 7. Next steps

1. Choose a design option (Section 5).
2. Extract 2017–2025 Sentinel-2 NDVI for watered trees and matched controls in Earth Engine. Estimate noise and clustering, then replace the placeholder MDEs.
3. Build a pump layer (OSM, BWB) with status history and describe logged watering against distance to a working pump.
4. Crosswalk turnout to planning areas, handling postal votes.
5. Review the literature on irrigation dose-response for young urban trees.
6. Specify a smallest effect of interest for each RQ in the registered plan.

## Sources

- Abgeordnetenhaus Berlin, [Drucksache 19/13426](https://pardok.parlament-berlin.de/starweb/adis/citat/VT/19/SchrAnfr/S19-13426.pdf) (answer of 12 October 2022): district watering costs and rounds, €3,000 per new street tree, no statistic on failed plantings.
- Abgeordnetenhaus Berlin, [Drucksache 19/16001](https://pardok.parlament-berlin.de/starweb/adis/citat/VT/19/SchrAnfr/S19-16001.pdf) (answer of 14 July 2023): young-tree watering practice, volumes per watering, age limits, 70–100 L per week guidance.
- Amt für Statistik Berlin-Brandenburg, [Flächenerhebung 2025](https://www.statistik-berlin-brandenburg.de/presse/2026/132-flaechenerhebung-berlin-2025): city and forest area.
- Senate environment department: [Daten und Fakten: Stadtbäume](https://www.berlin.de/-ii1098262) (439,348 street trees at the end of 2025); [Zustand der Straßenbäume](https://www.berlin.de/sen/uvk/natur-und-gruen/stadtgruen/stadtbaeume/strassen-und-parkbaeume/zustand-der-strassenbaeume/) (colour-infrared vitality reports); [Wässern von Stadtbäumen](https://www.berlin.de/sen/uvk/natur-und-gruen/stadtgruen/stadtbaeume/waessern-von-stadtbaeumen/).
- ZfK, [20 April 2022](https://www.zfk.de/unternehmen/nachrichten/berliner-wasserbetriebe-gute-bilanz-schrumpfender-gewinn): Berliner Wasserbetriebe sold 215 million m³ of water in 2021.
- Berliner Mieterverein, [street pumps](https://www.berliner-mieterverein.de/magazin/online/hintergrund/berliner-wasserpumpen-trinkwasser-per-muskelkraft-042024.htm): 2,079 street pumps, 1,614 working (status 2022), as reported.
- Berlin geodata catalogue ([gdi.berlin.de](https://gdi.berlin.de)): DOP20RGBI orthophoto records; flight dates to be confirmed per year.
