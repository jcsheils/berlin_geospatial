> **October 2026 scope update:** historical design context is retained below. The active design is the October proposal: Part II civic heat response (core), Part I vegetation cooling loss (supporting), and Part III allocation (exploratory). See `docs/analysis_plan.md` and `examination/README.md`. Existing descriptive products remain valid within their stated limits.

# Related Literature and Project Differentiation

## Scope used for this review

This memo now follows the feedback-incorporated three-part thesis design while
distinguishing it from work that is already implemented. The current design is:

- Part I: Landsat LST, Sentinel-2 vegetation greenness, built form, and
  temporal drought;
- Part II: a detectability-gated cumulative recorded-watering/LST association;
- Part III: the guaranteed multi-scale spatial-equity and vulnerability core.

The repository currently implements:

- 58,474 deduplicated citizen-watering events from May 2020-December 2025;
- tree-level linkage to Berlin's tree cadastre;
- inventory-normalized watering reach and intensity;
- analysis at 542 LOR Planungsräume rather than only 12 districts;
- global and local Moran analysis of watering reach;
- comparison with MSS 2025 social indicators and the Berlin Environmental
  Justice Atlas 2023/24;
- identification of neighbourhoods with high need relative to recorded
  watering.

The implemented analysis is descriptive. Part II, if adequately powered, is
planned as a qualified observational association rather than a promised causal
effect. The project does not observe municipal or unlogged private watering.

## Five must-cites plus Egerer

1. **Schwaab et al. (2021),**
   https://doi.org/10.1038/s41467-021-26768-w — the core European
   urban-tree/LST baseline for Part I.
2. **Gobatti et al. (2025),**
   https://doi.org/10.1038/s42949-025-00220-0 — the soil-moisture and
   irrigation mechanism that motivates the drought and water hypotheses.
3. **Baró et al. (2019),**
   https://doi.org/10.1016/j.envsci.2019.08.016 — the distributional-
   environmental-justice anchor for street-tree benefits; Part III shifts the
   outcome from benefit stocks to recorded care flows.
4. **Moskell et al. (2016),** https://doi.org/10.48044/jauf.2016.027 — the
   closest empirical precedent on resident street-tree watering and
   participation selection.
5. **Lachmund (2022),** https://doi.org/10.1177/23996544211070204 — the key
   Berlin-specific account of civic stewardship and citizenship around tree
   pits, grounding Part III's interpretation of recorded care.

Egerer et al. (2024) is the sixth retained reference and the strongest
platform-specific source
because it explicitly identifies Gieß den Kiez as a Berlin coordination
example. Roberts et al. (2017) and Openshaw (1984) are methodological
must-cites for spatial cross-validation and MAUP, respectively.

## Most relevant literature

### Berlin heat exposure and vulnerability

1. **Scherer, D., Fehrenbach, U., Lakes, T., Lauf, S., Meier, F., and
   Schuster, C. (2014).** Quantification of heat-stress related mortality
   hazard, vulnerability and risk in Berlin, Germany. *DIE ERDE*, 144(3-4),
   238-259. https://doi.org/10.12854/erde-144-17

   This paper combines Berlin heat hazard, population vulnerability, and
   mortality risk. It establishes the need for spatially targeted adaptation,
   but it does not examine tree care, volunteer behaviour, or the distribution
   of an adaptation intervention.

2. **Schuster, C., Burkart, K., and Lakes, T. (2014).** Heat mortality in
   Berlin - Spatial variability at the neighborhood scale. *Urban Climate*,
   10, 134-147. https://doi.org/10.1016/j.uclim.2014.10.008

   This is the closest Berlin precedent for neighbourhood-scale heat
   vulnerability. Its outcome is heat-related mortality, whereas this project
   studies the spatial distribution of citizen watering as an adaptive action.

3. **Westerholt, R., and Klopfer, F. (2024).** Studying the spatial structure
   of urban heat exposure in Berlin utilising Moran drop plots and seismograms.
   *AGILE GIScience Series*, 5, 52.
   https://doi.org/10.5194/agile-giss-5-52-2024

   This work applies spatial-autocorrelation methods to Berlin heat exposure.
   The present project applies Moran statistics to a different object:
   inventory-normalized volunteer watering reach, including local high-high and
   low-low activity clusters.

4. **Klopfer, F., and Pfeiffer, A. (2023).** Determining spatial disparities
   and similarities regarding heat exposure, green provision, and social
   structure of urban areas - A study on the city district level in the Ruhr
   area, Germany. *Heliyon*, 9(6), e16185.
   https://doi.org/10.1016/j.heliyon.2023.e16185

   This paper is methodologically close to the project's equity join because it
   combines heat, green provision, and social structure. It measures
   environmental conditions, not the distribution of citizen maintenance
   effort.

### Tree cooling, soil moisture, and irrigation

5. **Schwaab, J., Meier, R., Mussetti, G., Seneviratne, S. I., Bürgi, C., and
   Davin, E. L. (2021).** The role of urban trees in reducing land surface
   temperatures in European cities. *Nature Communications*, 12, 6763.
   https://doi.org/10.1038/s41467-021-26768-w

   This large comparative study establishes the cooling value of trees across
   European cities. It does not observe who maintains trees or whether
   maintenance effort is equitably distributed.

6. **Gobatti, L., Bach, P. M., Maurer, M., et al. (2025).** Impact of soil
   moisture content on urban tree evaporative cooling and human thermal
   comfort. *npj Urban Sustainability*, 5, 26.
   https://doi.org/10.1038/s42949-025-00220-0

   This is a strong reference for the proposed soil-moisture and irrigation
   mechanism. It models irrigation scenarios in Zurich. The planned extension
   of this project would instead use observed, tree-linked watering events in
   Berlin. The current repository does not yet perform that causal thermal
   analysis.

7. **Cuthbert, M. O., Rau, G. C., Ekström, M., O'Carroll, D. M., and Bates,
   A. J. (2022).** Global climate-driven trade-offs between the water retention
   and cooling benefits of urban greening. *Nature Communications*, 13, 518.
   https://doi.org/10.1038/s41467-022-28160-8

   This paper frames the hydrological trade-off behind irrigation-based
   cooling. It is global and model-based; this project contributes local,
   behavioural evidence about where supplemental water is actually logged.

8. **McDonald, R. I., Chakraborty, T. C., Endreny, T. A., Parsons, L. A.,
   Marsagishvili, M., and Esperon-Rodriguez, M. (2026).** Trees halve urban
   heat island effect globally but unequal benefits only modestly mitigate
   climate-change warming. *Nature Communications*, 17.
   https://doi.org/10.1038/s41467-026-71825-x

   This global study shows that tree cooling benefits are uneven and often
   greater in already cooler or wealthier settings. The Berlin project examines
   a potential mechanism behind unequal realized benefits: the geography of
   volunteer maintenance effort.

### New Part I method paper

**Su, Y., Makowski, D., Zhang, X., et al. (2026).** A remote sensing-based
assessment of the cooling effects of urban trees in European cities.
*npj Urban Sustainability*, 6, 96.
https://doi.org/10.1038/s42949-026-00399-w

This new paper analyses mixed 100 m by 100 m urban units rather than only
homogeneous tree-covered and impervious surfaces. Its support-aware LST design
is particularly relevant to Part I and to the Part II dilution calculation,
although it does not study citizen watering or Berlin specifically.

### Distributional environmental justice

9. **Gerrish, E., and Watkins, S. L. (2018).** The relationship between urban
   forests and income: A meta-analysis. *Landscape and Urban Planning*, 170,
   293-308. https://doi.org/10.1016/j.landurbplan.2017.09.005

   This establishes the broad association between income and urban forest
   provision. The present project shifts the outcome from the stock of urban
   forest to the flow of care directed toward that stock.

10. **Baró, F., Calderón-Argelich, A., Langemeyer, J., and Connolly, J. J. T.
    (2019).** Under one canopy? Assessing the distributional environmental
    justice implications of street tree benefits in Barcelona.
    *Environmental Science & Policy*, 102, 54-64.
    https://doi.org/10.1016/j.envsci.2019.08.016

    This paper assesses the distribution of street-tree ecosystem services.
    The Berlin project instead evaluates whether recorded watering effort is
    distributed according to social and environmental need.

11. **Locke, D. H., Hall, B., Grove, J. M., et al. (2021).** Residential
    housing segregation and urban tree canopy in 37 US cities.
    *npj Urban Sustainability*, 1, 15.
    https://doi.org/10.1038/s42949-021-00022-0

    This demonstrates how historical social structure shapes present canopy.
    It provides a useful environmental-justice framing, but its exposure is
    canopy cover rather than contemporary civic adaptation behaviour.

### Civic stewardship and citizen tree care

12. **Conway, T. M., Shakeel, T., and Atallah, J. (2011).** Community groups
    and urban forestry activity: Drivers of uneven canopy cover?
    *Landscape and Urban Planning*, 101(4), 321-329.
    https://doi.org/10.1016/j.landurbplan.2011.02.037

    This paper directly links local civic organisations with uneven urban
    forestry activity. It motivates treating stewardship as a possible source
    of spatial inequality. The Berlin project adds complete platform logs,
    tree-cadastre denominators, and formal spatial clustering.

13. **Moskell, C., Bassuk, N., Allred, S., and MacRae, P. (2016).** Engaging
    residents in street tree stewardship: Results of a tree watering outreach
    intervention. *Arboriculture & Urban Forestry*, 42(5), 301-317.
    https://doi.org/10.48044/jauf.2016.027

    This evaluates whether outreach changes resident watering. It is
    intervention-focused and based on participating residents; the Berlin work
    maps the observed spatial distribution of logged watering across an entire
    city and tests alignment with neighbourhood need.

14. **Elton, A. J., Harper, R. W., Bullard, L. F., Griffith, E. E., and Weil,
    B. S. (2023).** Volunteer engagement in urban forestry in the United
    States: Reviewing the literature. *Arboricultural Journal*, 45(2), 96-117.
    https://doi.org/10.1080/03071375.2022.2030620

    The review reports that urban-forestry volunteers may not represent the
    communities they serve and identifies participation barriers as an open
    research problem. This gives a theoretical basis for the project's
    distinction between environmental-need alignment and social equity.

15. **Lachmund, J. (2022).** Stewardship practice and the performance of
    citizenship: Greening tree-pits in the streets of Berlin.
    *Environment and Planning C: Politics and Space*, 40(6), 1290-1306.
    https://doi.org/10.1177/23996544211070204

    This is a key Berlin-specific stewardship reference. It provides a
    qualitative account of civic care and citizenship around tree pits. The
    current project complements it with quantitative, citywide, multi-year
    watering records.

16. **Egerer, M., Schmack, J. M., Vega, K., Ordóñez Barona, C., and Raum, S.
    (2024).** The challenges of urban street trees and how to overcome them.
    *Frontiers in Sustainable Cities*, 6, 1394056.
    https://doi.org/10.3389/frsc.2024.1394056

    This perspective discusses urban-tree management challenges and identifies
    Gieß den Kiez as a digital coordination example. It does not quantitatively
    evaluate the platform's watering logs or their equity.

17. **Ferrari, E. (2026).** Making time for street gardens. *Urban Studies*,
    OnlineFirst. https://doi.org/10.1177/00420980261432084

    This recent Berlin study examines everyday care of roadside plots through
    qualitative and citizen-science methods. It is relevant to the politics of
    care, but it does not provide the citywide, inventory-normalized
    distributional analysis performed here.

## Official sources to cite in the data and methods sections

18. **CityLAB Berlin / Technologiestiftung Berlin.** Gieß den Kiez -
    Nutzungsdaten. Berlin Open Data.
    https://daten.berlin.de/datensaetze/gdk-nutzungsdaten

19. **Berlin Senate Department for Urban Mobility, Transport, Climate Action
    and the Environment.** Umweltgerechtigkeit Berlin 2023/2024: Methode.
    https://www.berlin.de/umweltatlas/mensch/umweltgerechtigkeit/2024/methode/

20. **Amt für Statistik Berlin-Brandenburg.** Monitoring Soziale
    Stadtentwicklung 2025 and Lebensweltlich orientierte Räume 2021. The exact
    WFS endpoints and access dates are documented in
    `data/spatial/README.md`.

## Defensible differentiation of the current work

The literature falls into four mostly separate streams:

1. Berlin studies map heat exposure, vulnerability, or mortality.
2. urban-climate studies estimate the cooling supplied by canopy and water;
3. environmental-justice studies examine unequal canopy or ecosystem services;
4. stewardship studies examine participation, outreach, or qualitative care
   practices.

The present project connects streams 3 and 4 using a behavioural dataset. Its
main contribution is a spatially explicit analysis of **where recorded citizen
tree-watering effort occurs**, normalized by the number of inventoried trees
that could have been watered, and compared with both social vulnerability and
environmental burden.

The following preliminary, descriptive differentiators are
hypothesis-generating rather than independent confirmation of H3:

- **Observed action rather than environmental stock.** The outcome is logged
  watering behaviour, not canopy cover, greenness, or modelled ecosystem
  services.
- **Tree-linked normalization.** Watered trees, events, and litres are linked
  to the cadastre and divided by local tree inventories, avoiding the bias in
  raw counts toward neighbourhoods with more trees.
- **Fine spatial scale.** Analysis uses 542 Planungsräume, revealing
  within-district variation hidden by Berlin's 12 Bezirke.
- **Spatial dependence is explicit.** Global Moran's I for watering reach is
  0.441 with permutation p = 0.001, followed by local cluster classification.
- **Equity is multidimensional.** The analysis distinguishes social
  vulnerability from environmental burden. Recorded reach has a small negative
  association with child poverty (Spearman rho = -0.123), but a strong positive
  association with the Environmental Justice Atlas multiple-burden count
  (rho = 0.486).
- **Screening output.** The work identifies ten Planungsräume where low or very
  low social status, thermal or green need, and below-median recorded watering
  coincide. They are screening areas for validation, not proven allocation
  priorities and not evidence that no unlogged watering occurred.
- **Reproducibility.** Official open spatial services, auditable joins,
  notebook builders, tables, maps, and enriched GeoPackages are included.

## Suggested related-work positioning paragraph

Prior Berlin research has mapped neighbourhood heat exposure, vulnerability,
and heat-related mortality (Scherer et al., 2014; Schuster et al., 2014;
Westerholt and Klopfer, 2024), while broader urban-climate studies demonstrate
that tree cooling depends on canopy, urban form, and water availability
(Schwaab et al., 2021; Cuthbert et al., 2022; Gobatti et al., 2025).
Environmental-justice research has also shown that urban forest provision and
street-tree benefits are often distributed unequally (Gerrish and Watkins,
2018; Baró et al., 2019; Locke et al., 2021). A separate stewardship literature
examines how community organisations, outreach, and civic participation shape
tree care (Conway et al., 2011; Moskell et al., 2016; Lachmund, 2022). However,
these literatures rarely evaluate the distribution of observed maintenance
effort itself. This study addresses that gap by linking the May 2020-December
2025 Gieß den Kiez watering logs to Berlin's tree cadastre, normalizing recorded
watering by the local tree inventory, testing its spatial clustering across 542
Planungsräume, and comparing the resulting patterns with official social and
environmental-justice indicators.

## Claims that should be revised in the proposal

- Do not claim that the current analysis estimates the causal cooling effect of
  citizen watering. The implemented results are descriptive.
- Do not claim that watering simply favours wealthy areas. The current result
  is more nuanced: middle-status Planungsräume have the highest median reach;
  environmental burden is positively associated with watering, while child
  poverty has a smaller negative association.
- Avoid an unqualified "first use of Gieß den Kiez" claim. The platform already
  appears in published Berlin stewardship literature. A narrower claim is more
  defensible: **a citywide, multi-year, inventory-normalized spatial equity
  analysis of the public watering logs**.
- The proposal's "Yang et al. (2024)" global tree-cooling citation should be
  replaced by McDonald et al. (2026), DOI
  `10.1038/s41467-026-71825-x`.
- The Berlin heat-mortality reference should begin with Schuster, not Burkart:
  Schuster, Burkart, and Lakes (2014).
