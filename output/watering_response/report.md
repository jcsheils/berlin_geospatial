# Berlin watering patterns and weather

Exploratory results · 29 September 2026

The monthly summaries are complete for the available recorded-care data: **816 district-months and 36,856 LOR neighbourhood-months**, with separate event, litre and distinct-tree counts. The self-contained HTML report includes figures, source notes and the full model results.

## Supplied monthly LST: new results

The supplied CSV is now incorporated. A new **6,596-row Ortsteil-month panel** contains events, litres and distinct trees for 97 current official areas. All linked watering events reconcile. Temperature comparisons use **93 provisionally aligned areas**.

- **Source audit:** 9,312 rows, 96 distinct names, and 19.4% missing LST. Buckow has two different rows per month. Schlachtensee is absent; Nikolassee and Zehlendorf are excluded because the original boundary version is unknown.
- **Count definition is missing:** `LST_C_count` ranges up to 64,360 and must not be treated as the number of satellite images. Acquisition dates, cloud filtering, compositing and rainfall provenance are also unspecified.
- **Main seasonal comparison:** for litres/ha, same-month raw Spearman correlation is +0.299; area-and-year-month residual Pearson correlation with log(1 + litres/ha) is +0.025. These are different statistics; the full report also supplies a matched Pearson comparison.
- **Next-month temperatures:** the residual correlation with litres/ha is −0.024, changes to +0.005 without 2022, and is +0.075 using all calendar months. This is not a stable descriptive cooling pattern and is not an estimate of a causal effect.
- **Next input:** the extraction script or source metadata is needed to confirm geography, the Buckow components, count semantics, Landsat processing and rainfall.

The DWD results below remain separate evidence about shared Berlin-wide air-temperature variation. The local residual comparisons remove that common monthly variation and cannot disprove a city-wide heat response.

## Berlin-wide DWD findings

- **2022 is not a universal activity peak.** It has the largest annual event and litre totals, but June–September 2020 has 13,838 events versus 12,660 in 2022, and more distinct trees. 2022 has more litres in that comparison.
- **Same-month temperature aligns with events and distinct-tree counts** after calendar-month and year adjustment. The event slope is 0.817 log(1 + events) units per 5 °C, with approximate 95% interval 0.142 to 1.492.
- **Previous-month temperature is much less informative:** event slope 0.103, interval −0.515 to 0.722. This does not rule out a response over days. Rainfall estimates are also imprecise.
- **The same-month pattern persists without 2022.** This is an exploratory association, not proof of motivation or causation.
- **Social status does not show a simple rich-to-poor gradient.** Middle-status neighbourhoods have the highest mean monthly inventory-normalised event rate. Status is a static end-2024 contextual measure.

## Interpretation and limits

Weather is from DWD Berlin-Tempelhof, station 00433. It supplies shared Berlin temporal context, not neighbourhood weather or Landsat LST. Of 60 complete calendar months in 2021–2025, 58 enter each joint temperature/rainfall model because precipitation is incomplete in June and October 2023. Three-month HAC uncertainty preserves calendar gaps. Multiple exploratory intervals are not multiplicity-adjusted.

The watering panel contains linked platform records only. Missing logs are not proof of no irrigation, and denominators use the current tree inventory. May 2020 is partial; January–April are unavailable. Monthly distinct counts cannot be summed into annual distinct counts.

The supervisor's monthly Ortsteil CSV has been incorporated in a provisional extension, with explicit geographical exclusions and source-quality limitations. No causal cooling effect, vulnerability-by-weather interaction or optimal municipal allocation has been estimated.

## Next input

Provide the extraction script or accompanying source notes to confirm the original boundaries, the two Buckow components, Landsat processing, count definition and rainfall provenance.
