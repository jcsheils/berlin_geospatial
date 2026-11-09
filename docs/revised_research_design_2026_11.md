# Revised purpose and research questions

*Gieß den Kiez citizen tree watering in Berlin · revision of the October 2026 proposal, adopted 9 November 2026*

The October 2026 proposal treats logged watering as the outcome: it asks when and where citizens water and how that record could inform municipal priorities. This revision widens the purpose from describing a behaviour to evaluating it as part of the city's tree care. It keeps the four-question structure, the RQ1 pipeline and the allocation scenarios, and adds the two missing links: the public levers that steer citizen care, and the tree outcomes that would give it value. The [active analysis plan](analysis_plan.md) adopted this revision on 9 November 2026.

Figures come from the [policy-relevance memo](policy_feedback_2026_11.md) and from the `design_feasibility` section of `output/feedback_benchmarks/benchmarks.json`, rebuilt by `python analysis/build_feedback_benchmarks.py`. The feasibility counts cover trees and treated units only. Outcomes of the new designs have not been examined.

## 1. Purpose

The thesis evaluates citizen tree watering as **co-produced climate adaptation**: a public service that residents and the city deliver together (Ostrom, 1996). In case studies, stewardship was essential to whether young urban trees establish (Roman et al., 2015), and urban tree mortality is highest in the first years after planting (Hilbert et al., 2019).

- **Outcome.** The outcome moves closer to a healthy city: the survival and condition of young street trees, and through them future canopy, shade and cooling where residents are most exposed to heat.
- **Treatments.** The treatments move closer to policy: conditions the city controls, such as pump maintenance and how long districts water young trees.
- **Questions.** The thesis asks how much care citizens add relative to tree water need and municipal watering, and how that care responds to drought and to public levers. It also asks whether the care reaches the trees that need it, and whether it goes with better survival and condition.
- **Use.** The answers feed scenarios for scaling, targeting and funding the platform.

**Fundamental question.** *To what extent does citizen watering help Berlin's street trees through heat and drought, which trees and neighbourhoods does it reach, and which levers under public control could make it more effective and more equitable?*

The October version asked how citizen watering responses can complement conventional vulnerability assessments, identify unmet adaptation needs and inform a more equitable allocation of municipal irrigation. Allocation remains one of the policy scenarios. Effectiveness and levers become the centre.

**Title.** The main title stays and only the subtitle changes, to *Spatiotemporal Modeling of Citizen Tree Watering for Equitable Climate Adaptation in Berlin: Drought Response, Public Levers and Tree Outcomes*. The October subtitle was *Climate Responses and Municipal Irrigation Priorities*.

## 2. What the October design cannot answer

- **It measures a behaviour, not a benefit.** Logged events and litres show where people act, not whether trees or residents gain. Part III's allocation rule needs a factor that turns logged litres into effective care, and nothing in the design estimates it.
- **Clear statistical effects are small in practice.** A 5 °C warmer day adds about 1,900 logged litres citywide, roughly 0.3% of the daily guidance need of street trees aged 15 or younger. The median watered tree receives 60 L per season, while guidance for a young tree is 1,400–2,600 L.
- **Care is episodic, concentrated and mostly given to older trees.**
  - Half of watered tree-seasons have only one logged day, and 78% of watered trees appear in a single season.
  - 10% of watered trees receive 58% of logged litres.
  - 60% of watered tree-seasons involve trees older than 20. Only 16% involve trees aged 11–20, which in most districts no longer receive municipal watering.
  - Any effect on trees should therefore come from the minority that receive sustained care.
- **Area-level greenness cannot test effects.** A median of 0.14% of an area's street trees is watered per season. An area NDVI analysis could therefore detect only per-tree effects of 0.08–0.25 NDVI.
- **The city's levers appear only as covariates.** Pump maintenance, the age at which municipal care ends, watering appeals and platform funding are all policy choices. The October design includes pump access as an association and leaves the other levers out.

## 3. Logic model

```text
Public levers ───► Citizen care ────► Water a tree ─────► Tree survival ───► Canopy, shade
(pumps, municipal   (reach, timing,     receives           and condition      and cooling
 care age limits,    dose, persistence) (logged, unlogged,                    (decades)
 appeals, funding)                       municipal, rain)
      RQ2              RQ1, RQ2                                RQ3              RQ4, Part I
```

RQ1 and RQ2 cover the links into citizen care, RQ3 the link to tree outcomes, and RQ4 the chain as a whole. In the scenarios, Part I's drought cooling-loss estimates supply the last link.

## 4. Revised research questions

| | October 2026 | Revised question | What changes |
| --- | --- | --- | --- |
| RQ1 | Civic climate response | **Civic drought response.** How do citizen watering events and volumes respond to heat, rainfall and accumulated drought, how stable is this response, and how much of young street trees' water need does it cover? | Same models (Appendix B). Effects are also reported in litres and as a share of need, and persistence of care is added. |
| RQ2 | Vulnerability and resource inequality | **Public levers and reach.** How do conditions under public control (working street pumps, the age at which municipal watering ends, public appeals) change where and how much citizens water? Does citizen care reach the trees and neighbourhoods with the greatest need? | Pumps and municipal care become designs instead of covariates. The vulnerability and inequality comparisons continue as the reach part, with density and turnout added. |
| RQ3 | Added value over vulnerability assessments | **Tree outcomes.** Are sustained citizen watering and access to a working pump associated with higher survival and better condition of young street trees, especially in dry seasons? Which effects can the data detect or rule out? | New outcome question. The added-information comparison moves into RQ4 as a targeting input. |
| RQ4 | Municipal allocation consequences | **Policy scenarios.** What would scaling, targeting and funding citizen watering achieve for young trees' water needs and survival, compared with municipal care? What would it imply for public water supply and the fairness of care? | Need-only against citizen-informed allocation stays as one scenario, with the effective-care factor bounded by RQ3. Scale-up, retargeting and break-even funding are added. |

## 5. Designs

### RQ1: civic drought response

- **Models.** These are unchanged: hierarchical negative-binomial event models and two-part volume models on the planning-area-day panel, with matched street-tree stock (Appendix B).
- **Additions.**
  - Express responses as litres per 1,000 young street trees and as shares of daily guidance need.
  - Separate first and repeat watering of the same tree to measure persistence.
  - Report the response across long dry spells, such as summer 2022, to see whether citizen effort builds or fades as deficits accumulate.
- **Primary estimand.** The additional logged litres on a day 5 °C warmer and after 14 dry days, citywide and per 1,000 young street trees, with the share of need this covers.
- **Smallest effect of interest (proposed).** 1% of the daily guidance need of street trees aged 15 or younger, about 5,000–7,000 L citywide. The pilot heat response is a quarter to a third of that.

### RQ2: public levers and reach

1. **Street pumps (primary lever).**
   - **Context.** Berlin has about 2,100 street pumps drawing groundwater; 1,614 of 2,079 worked in 2022. The platform maps pumps from OpenStreetMap, where every status change is dated.
   - **Design.** Build a pump status panel from that history and from district repair records. Then compare logged watering of trees within walking distance (for example 100–200 m) before and after a pump is repaired or fails. The comparison group is trees near pumps whose status did not change (staggered difference in differences; Callaway and Sant'Anna, 2021).
   - **Caveats.** Citywide distance gradients remain context only. Status edits may follow use, so dated repairs are preferred where available.
2. **End of municipal watering (difference in discontinuities).**
   - **Context.** Pankow, Neukölln, Treptow-Köpenick, Lichtenberg and Reinickendorf water young trees until 10 years after planting. Friedrichshain-Kreuzberg and Tempelhof-Schöneberg water them until 12 years (Drucksache 19/16001).
   - **Design.** Take the change in citizen watering between ages 9–10 and 11–12 in the 10-year districts, and subtract the same change in the 12-year districts. The result shows whether citizens step in when municipal care stops (Grembi et al., 2016). Because ages are whole years, inference follows Kolesár and Rothe (2018).
   - **Feasibility.** The cells hold 19,075 and 21,746 tree-seasons in the 10-year districts, and 4,536 and 5,519 in the 12-year districts. Seasonal watered shares are 0.81–1.9%, so the minimum detectable effect is 0.56–1.21 percentage points. That is about half to all of the baseline share, so only strong compensation is detectable.
   - **Registration.** Watering by age near the limits has not been examined, so this test can be registered before it is run.
3. **Appeals (optional).** Dated appeals from the Senate and districts enter the RQ1 daily panel as events, with weather held fixed. Identification is weak because appeals follow heat.
4. **Reach and equity.**
   - **Comparison.** Reach weighted by need (young age, sealed tree pits, heat exposure, age beyond municipal care) is compared across population density, social status, residents per street tree and turnout.
   - **Turnout data.** Turnout comes from a precinct-to-planning-area crosswalk that handles postal votes. The overlay also becomes a layer in the atlas. Inference stays at area level.
   - **Pattern so far.** Reach rises steeply with density (Spearman 0.56) and shows no association with social status (0.01). The equity analysis has to explain this pattern rather than assume a direction.

**Primary estimands.** For pumps, the change in logged litres per tree-season near a pump after it is repaired or fails. For the municipal limit, the difference in discontinuities in the share of trees watered at the 10-year limit.

### RQ3: tree outcomes

- **Primary outcome: survival.** The outcome is whether a young street tree is removed between two inventory snapshots.
  - **Why not satellite condition.** Young crowns are too small for it. The median crown covers 3% of a 10 m Sentinel-2 pixel at ages 3–8, 7% at ages 9–12 and 13% at ages 13–20.
  - **Cost.** Survival also has a direct price: a new street tree with about three years of establishment care costs about €3,000 (Drucksache 19/13426).
- **Design.**
  - **Comparison.** Young street trees with sustained logged care (for example three or more watering days, or 500 L in a season) are compared with unwatered trees in the same planning area, genus group and planting year that were alive at the same date. Both groups are followed until the latest inventory.
  - **Timing.** Exposure starts only after a snapshot that shows both groups alive, so watering cannot be credited with survival that had to happen before it. Annual snapshots allow a new cohort each season. With only two snapshots, exposure is limited to the first season after the earlier one.
  - **Extensions.** Dose-response (any log, three or more days, 500 L or more) and dry-season contrasts (2022 against 2021 and 2023) follow.
  - **Removal reasons.** Felling records with reasons separate deaths from removals for construction.
- **Lever versions.** Two versions of the design do not depend on logging at all.
  - **Pumps.** Survival by distance to a working pump captures unlogged pump water.
  - **Municipal limit.** Survival at ages 11–13 in the 10-year districts against the 12-year districts shows what two more years of municipal watering are worth.
- **Detectability.** There are 3,247 young street trees logged in April–September. With five matched controls each, four-year mortality differences of 1.8–3.0 percentage points are detectable. The baselines are 13–19%, implied by annual mortality of 3.5–5.1% (Roman and Scatena, 2011). For the 283 trees that received at least 500 L in a season, only differences of 6–10 points are detectable.
- **Smallest effect of interest (proposed).** This is the mortality reduction whose avoided replacements would cover the platform's running costs over the same period, once those costs are known. As a placeholder, 2 points over four years corresponds to about 65 avoided replacements among 3,247 trees, roughly €195,000.
- **Inference.** Results are tested for equivalence against that threshold (Lakens et al., 2018), so a null result states which effects are ruled out.
- **Secondary outcomes.**
  - Sentinel-2 condition for trees older than 20, whose median crown covers 20% of a pixel at ages 21–30.
  - The Senate's colour-infrared vitality survey for mature inner-city trees.
- **Requirement.** An earlier full inventory (2019–2021) is needed. Tree IDs in the logs that are missing from the current inventory hint at removals, but they lack a denominator.

### RQ4: policy scenarios

- **Scale-up.**
  - **Volumes.** With 100,000 participants giving 100–2,000 L each per season, logs would total 10–200 million L.
  - **Comparison.** That ranges from 8–14% to more than 150% of young street trees' guidance need, and 0.005–0.09% of public supply.
  - **Additions and inputs.** The scenarios add targeting rules, peak-day demand and pump capacity. Per-person volumes require user IDs.
- **Retargeting.** One scenario shifts part of current care from trees older than 20 to trees aged 11–20, the gap after municipal watering ends. This could work through map prompts on the platform. RQ3's dose-response bounds the gain.
- **Allocation.**
  - **Kept.** The October comparison of need-only and citizen-informed municipal priorities stays, together with its fairness safeguards.
  - **Changed.** The effective-care factor is bounded by RQ3 instead of assumed. The added-information comparison becomes a test of whether civic data change targeting.
- **Funding.** This is a break-even comparison: annual platform and campaign costs set against two benefits.
  - **Water.** The water's replacement value, €8,000–115,000 per season at €0.05–0.15 per litre.
  - **Trees.** Avoided replacements at €3,000 each.
  - **Rule of thumb.** Each €30,000 of annual cost beyond the water's value needs ten avoided young-tree losses per year.
- **Benefits.**
  - **Conversion.** Avoided losses become future canopy through growth curves, and canopy becomes cooling through Part I's drought cooling-loss estimates.
  - **Reporting.** Results are reported per tree and per resident of heat-exposed areas, as illustrative ranges.

### Part I: cooling evidence (reduced)

The drought cooling-loss estimates stay, as the conversion from canopy to cooling in RQ4. Appendix A's exclusion of a satellite test of watering-induced cooling still applies.

## 6. Principles across questions

1. **Detectability before outcomes.** For each primary estimand, compute the minimum detectable effect from design counts or pre-period data, and register a smallest effect of interest in policy units before examining outcomes. Where the minimum detectable effect exceeds that threshold, report descriptions and bounds instead of tests.
2. **Policy units.** Report litres, shares of need, trees reached, avoided replacements and euros. Standardised coefficients are secondary.
3. **Dose and persistence.** Sustained care is the primary treatment, and "any log" is a secondary contrast.
4. **Logged is not received.** Unlogged private watering, other initiatives, municipal watering, rain and groundwater all reach trees.
   - The lever designs capture all water from their source.
   - Comparing trees within age bands beyond municipal-care age limits municipal confounding.
   - Unlogged watering among controls pulls logged contrasts towards zero, so they understate the effect of care.
   - Sensitivity analyses vary the assumed share of unlogged care.
5. **Scale.** Behaviour is modelled at planning-area and Bezirksregion scale with partial pooling. Tree outcomes are analysed only at tree level.
6. **Population.** The population is catalogued street trees, especially those aged 4–20. Forest covers 17.7% of Berlin's area but lies outside both the platform and the inventory, so conclusions concern street trees.
7. **Disclosure.** The registration discloses the pilots and every summary already examined. The outcomes of the new designs have not been examined.

## 7. Contributions

1. **Effectiveness.** A tree-level test of whether citizen watering coordinated by an open platform goes with better young-tree survival, with detectability fixed in advance. A first search found no published evaluation of the platform's effect on trees, and the Month 1 review will check this. A precise null result would also be informative, because it bounds what the platform does for trees.
2. **Levers.** Estimates, in policy units, of how pump maintenance and municipal-care age limits change citizen care.
3. **Value and scale.** Need coverage, break-even and scale-up scenarios that a city can use when deciding on funding.
4. **Equity.** Whether co-produced care follows need, density or advantage. This extends distributional research from the stock of canopy to flows of care (Gerrish and Watkins, 2018).
5. **Transferability.** The platform's open-source code runs in other cities, including Leipzig since 2021 and Magdeburg since 2023. The framework therefore applies wherever an open tree register exists.

## 8. Work plan, effort and gates

| Phase | Period | Work | Decision |
| --- | --- | --- | --- |
| 1 | Month 1 | Literature on co-production, stewardship, establishment and irrigation dose; data requests; pump status panel; pre-period Sentinel-2 noise; register thresholds and designs | **Gate A:** are survival data, pump history and the history of municipal age limits usable? Fix the RQ3 primary outcome and the RQ2 designs. |
| 2 | Months 2–3 | RQ1 main models in need units; RQ2 pump design, municipal-limit test, reach and equity | — |
| 3 | Months 3–4 | RQ3 survival and condition; lever versions | **Gate B:** where the minimum detectable effect exceeds the threshold, RQ3 reports bounds and RQ4 uses ranges. |
| 4 | Month 5 | RQ4 scale-up, retargeting, allocation and funding scenarios | — |
| 5 | Month 6 | Synthesis, writing, code release | — |

Planned effort is RQ1 20%, RQ2 25%, RQ3 25%, RQ4 15%, Part I 5% and synthesis 10%. The October split was Part II 50%, Part I 25%, Part III 15% and integration 10%.

## 9. Data

| Data | Needed for | Source and status |
| --- | --- | --- |
| Earlier full tree inventory (2019–2021) | RQ3 survival; historical stock for RQ1–RQ2 | Request: the platform's tree tables (CityLAB); archived open-data releases |
| Felling records with reasons (GRIS) | Separating deaths from planned removals | Request: districts |
| Pump status history | RQ2 pumps; RQ3 lever version | Public: OpenStreetMap history; repair records on request |
| Municipal age limits by year; watering lists | RQ2 limit test; municipal confounding | Drucksache 19/16001; district requests |
| Dated watering appeals | RQ2 (optional) | Senate and district press releases |
| Sentinel-2, 2017–2025 | RQ3 secondary outcome; pre-period noise | Public (Earth Engine) |
| Colour-infrared vitality, tree level | RQ3 secondary outcome (mature trees) | Request: Senate environment department |
| Pseudonymous user IDs; adoption records | RQ1 persistence; RQ4 per-person volume | Request: CityLAB |
| Platform and campaign costs | RQ4 break-even | Request: CityLAB |
| Precinct and postal-district results and geometries | RQ2 turnout | Public: state election office |

## 10. Risks and fallbacks

| Risk | Consequence | Fallback |
| --- | --- | --- |
| No earlier inventory | No survival outcome | Sentinel-2 condition for older trees and bounds; the RQ2 lever designs on logged care continue |
| Pump status edits follow use | Mistimed events | Dated repairs where available; lagged edits; sensitivity analyses |
| Age limits applied loosely | Diluted contrast | Treat the district rule as intention to treat; check against watering lists |
| Watering chosen by visible tree condition | Biased survival contrast | Matching within planning area, genus and planting year; exposure starting after a snapshot; pre-watering negative controls; sensitivity analysis |
| Time overrun | Incomplete chapters | Drop the appeals design and keep Part I minimal |

## 11. What stays, what changes, what goes

- **Stays.** These carry over from the October design:
  - the RQ1 pipeline and models;
  - the planning-area and Bezirksregion structure;
  - the vulnerability and inequality comparisons, now in RQ2;
  - the allocation comparison and fairness safeguards, now in RQ4;
  - registration with disclosure, and the claim limits on logged care.
- **Changes.** These are new or reworked:
  - a tree-outcome question (RQ3);
  - levers analysed as designs (RQ2);
  - practical-relevance units throughout;
  - the added-information analysis folded into RQ4;
  - Part I reduced to the cooling conversion.
- **Goes.** Area-level greenness regressions are dropped. The satellite test of watering-induced cooling remains excluded (Appendix A).

## References

- Abgeordnetenhaus Berlin, [Drucksache 19/13426](https://pardok.parlament-berlin.de/starweb/adis/citat/VT/19/SchrAnfr/S19-13426.pdf) (2022) and [Drucksache 19/16001](https://pardok.parlament-berlin.de/starweb/adis/citat/VT/19/SchrAnfr/S19-16001.pdf) (2023).
- Callaway, B., and Sant'Anna, P. H. C. (2021). Difference-in-differences with multiple time periods. *Journal of Econometrics*, 225(2), 200–230. https://doi.org/10.1016/j.jeconom.2020.12.001
- CityLAB Berlin. [Gieß den Kiez two-pager](https://citylab-berlin.org/wp-content/uploads/Two-Pager-Giess_den_Kiez-0326_EN.pdf) (data sources, including pumps from OpenStreetMap; reuse in Leipzig). Interoperable Europe, [Giess den Kiez keeps trees alive during heatwaves](https://interoperable-europe.ec.europa.eu/collection/open-source-observatory-osor/news/giess-den-kiez-keeps-trees-alive-during-heatwaves) (reuse in Leipzig and Magdeburg).
- Gerrish, E., and Watkins, S. L. (2018). The relationship between urban forests and income: A meta-analysis. *Landscape and Urban Planning*, 170, 293–308. https://doi.org/10.1016/j.landurbplan.2017.09.005
- Grembi, V., Nannicini, T., and Troiano, U. (2016). Do fiscal rules matter? *American Economic Journal: Applied Economics*, 8(3), 1–30. https://doi.org/10.1257/app.20150076
- Hilbert, D. R., Roman, L. A., Koeser, A. K., Vogt, J., and van Doorn, N. S. (2019). Urban tree mortality: A literature review. *Arboriculture & Urban Forestry*, 45(5), 167–200. https://doi.org/10.48044/jauf.2019.015
- Kolesár, M., and Rothe, C. (2018). Inference in regression discontinuity designs with a discrete running variable. *American Economic Review*, 108(8), 2277–2304. https://doi.org/10.1257/aer.20160945
- Lakens, D., Scheel, A. M., and Isager, P. M. (2018). Equivalence testing for psychological research: A tutorial. *Advances in Methods and Practices in Psychological Science*, 1(2), 259–269. https://doi.org/10.1177/2515245918770963
- Ostrom, E. (1996). Crossing the great divide: Coproduction, synergy, and development. *World Development*, 24(6), 1073–1087. https://doi.org/10.1016/0305-750X(96)00023-X
- Roman, L. A., and Scatena, F. N. (2011). Street tree survival rates: Meta-analysis of previous studies and application to a field survey in Philadelphia, PA, USA. *Urban Forestry & Urban Greening*, 10(4), 269–274. https://doi.org/10.1016/j.ufug.2011.05.008
- Roman, L. A., et al. (2015). Stewardship matters: Case studies in establishment success of urban trees. *Urban Forestry & Urban Greening*, 14(4), 1174–1182. https://doi.org/10.1016/j.ufug.2015.11.001
- Further stewardship, equity and Berlin references: [related literature](related_literature.md).
