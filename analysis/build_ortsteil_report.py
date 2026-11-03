"""Readable source audit and provisional local LST section for the main report."""
from __future__ import annotations

import base64
import calendar
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from berlin_heat.ortsteil_lst import build_ortsteil_extension, METRICS

TIMING_LABELS = {
    "previous_LST_current_watering": "Previous LST → watering",
    "same_month": "Same month",
    "watering_next_LST": "Watering → next LST",
}
METRIC_LABELS = {
    "recorded_watering_events_per_ha": "Events / ha",
    "recorded_litres_per_ha": "Litres / ha",
    "recorded_watered_trees_per_ha": "Distinct trees / ha",
}


def build_ortsteil_section(root: Path):
    result = build_ortsteil_extension(root)
    tables, meta = result["tables"], result["metadata"]
    output = root / "output/watering_response/ortsteil"
    figures = output / "figures"
    figures.mkdir(exist_ok=True)
    availability = tables["source_monthly_availability"]
    grid = availability.pivot(index="year", columns="month", values="valid_lst_pct")
    fig, ax = plt.subplots(figsize=(11.2, 4.5))
    im = ax.imshow(grid, cmap="YlGnBu", vmin=0, vmax=100, aspect="auto")
    ax.set_xticks(range(12), list(calendar.month_abbr)[1:])
    ax.set_yticks(range(8), grid.index)
    for i in range(8):
        for j in range(12):
            value = grid.iloc[i, j]
            ax.text(j, i, f"{value:.0f}", ha="center", va="center", fontsize=8,
                    color="white" if value > 65 else "#253541")
    fig.colorbar(im, ax=ax, label="Source rows with LST (%)", shrink=.85, pad=.025)
    ax.set_title("Temperature availability varies sharply by month", fontweight="bold", pad=18)
    fig.text(.09, .035, "97 source rows per month, including two Buckow entries. Missing LST is retained as missing.", fontsize=9)
    fig.subplots_adjust(left=.09, right=.97, top=.83, bottom=.15)
    fig.savefig(figures / "01_lst_availability.png", dpi=160)
    plt.close(fig)

    corr = tables["provisional_pooled_correlations"]
    core = corr[(corr["sample"] == "April-September_2021-2025") & corr.screen.eq("all_available_LST")].copy()
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.8), sharex=True, sharey=True)
    for ax, (relationship, title) in zip(axes, TIMING_LABELS.items()):
        subset = core[core.relationship.eq(relationship)].set_index("exposure")
        for i, metric in enumerate(METRIC_LABELS):
            row = subset.loc[metric]
            raw, residual = row.raw_pearson_log1p_exposure, row.area_and_yearmonth_residual_correlation
            ax.plot([raw, residual], [2-i, 2-i], color="#c8cfd2", lw=2)
            ax.plot(raw, 2-i, "o", color="#788792", label="Unadjusted" if i == 0 else None)
            ax.plot(residual, 2-i, "o", color="#bb622c", label="Area + year-month residuals" if i == 0 else None)
        ax.axvline(0, color="#adb7bd", lw=1)
        ax.set_title(title, fontsize=11, fontweight="bold")
        ax.set_xlim(-.15, .55)
        ax.set_ylim(-.5, 2.5)
        ax.set_xlabel("Pearson correlation")
        ax.grid(axis="x", alpha=.15)
    axes[0].set_yticks([2, 1, 0], ["Events / ha", "Litres / ha", "Distinct trees / ha"])
    handles, labels = axes[-1].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(.55, .035))
    fig.suptitle("Local LST comparisons are much weaker after area and date adjustment", x=.14, ha="left", fontsize=14, fontweight="bold")
    fig.text(.14, .87, "April–September 2021–2025 · 93 provisionally aligned areas · exposure is log(1 + recorded amount per hectare)", fontsize=9)
    fig.subplots_adjust(left=.14, right=.98, top=.75, bottom=.22, wspace=.16)
    fig.savefig(figures / "02_provisional_correlations.png", dpi=160)
    plt.close(fig)

    def img(name, alt):
        encoded = base64.b64encode((figures / name).read_bytes()).decode()
        return f'<img src="data:image/png;base64,{encoded}" alt="{alt}">'
    display = core[["relationship", "exposure", "n_area_months", "raw_spearman_rho",
                    "raw_pearson_log1p_exposure", "area_and_yearmonth_residual_correlation"]].copy()
    display.relationship = display.relationship.map(TIMING_LABELS)
    display.exposure = display.exposure.map(METRIC_LABELS)
    display = display.rename(columns={"relationship": "Alignment", "exposure": "Recorded exposure",
                                      "n_area_months": "Area-months", "raw_spearman_rho": "Raw Spearman ρ",
                                      "raw_pearson_log1p_exposure": "Raw Pearson r (log exposure)",
                                      "area_and_yearmonth_residual_correlation": "Residual Pearson r"})
    all_grid = corr[["sample", "relationship", "screen", "exposure", "n_area_months",
                     "area_and_yearmonth_residual_correlation"]].copy()
    all_grid.relationship = all_grid.relationship.map(TIMING_LABELS)
    all_grid.exposure = all_grid.exposure.map(METRIC_LABELS)
    all_grid = all_grid.rename(columns={"sample":"Watering months", "relationship":"Alignment",
                                      "screen":"Count screen", "exposure":"Exposure", "n_area_months":"Area-months",
                                      "area_and_yearmonth_residual_correlation":"Residual r"})
    summary = meta["source_audit"]
    section = f'''<h2>5. Supplied monthly Landsat file: audit and provisional comparison</h2>
<p>The supplied CSV is now incorporated. It contains <strong>{summary['rows']:,} rows for 2018–2025</strong>, covering 96 distinct Ortsteil names. There are {summary['missing_lst_rows']:,} missing LST values ({summary['missing_lst_pct']:.1f}% of source rows). Missing temperatures are never replaced with zero.</p>
<p><strong>Two source issues require explicit exclusions.</strong> Buckow has two different observations every month, without component IDs; neither is selected or averaged. Schlachtensee is absent. Berlin's <a href="{meta['boundary_change_reference']}">official 2020 boundary change</a> created Schlachtensee from parts of Nikolassee and Zehlendorf, so the latter two are excluded until the extraction geography is clarified.</p>
<p>Tree-inventory points were assigned directly to <a href="{meta['boundary_catalogue']}">official ALKIS Ortsteil polygons</a>. All 57,786 linked events and 2,249,502 litres reconcile without loss or district disagreements. The new table has <strong>6,596 Ortsteil-months</strong>, including events, litres and monthly distinct trees for all 97 official areas. Temperature comparisons use <strong>93 provisional areas</strong>; matching names and districts does not confirm identical source polygons.</p>
{img('01_lst_availability.png', 'Monthly percentage of source rows containing LST')}
<p><strong>LST_C_count remains undefined.</strong> Positive values range from 1 to 64,360 and are often repeated at an area's maximum, suggesting a spatial count. This is not enough to identify its exact meaning. The file also omits acquisition dates, sensor/product details, cloud masks, compositing rules and rainfall provenance. No count is interpreted as an independent satellite observation or used as an inferential weight.</p>
<h3>What the preliminary correlations show</h3>
<p>The main description uses April–September watering months in 2021–2025, including recorded zeros. There are 2,639 usable same-month area-months out of 2,790 eligible combinations. Previous- and next-month temperatures are joined by exact calendar date before selecting the season. Three exposures are evaluated separately: events, litres and distinct trees per hectare.</p>
{img('02_provisional_correlations.png', 'Raw and area/date residual Pearson correlations for three temporal alignments')}
<div class="scroll">{display.to_html(index=False,border=0,float_format=lambda x:f'{x:.3f}')}</div>
<p>For litres per hectare, the raw same-month Spearman correlation is +0.299, while the correlation between residual LST and residual log(1 + litres/ha), after removing Ortsteil and actual year-month means, is only +0.025. The two columns use different correlation definitions; the figure compares Pearson correlations using the same log exposure on both sides.</p>
<p>The next-month residual correlation for litres is −0.024, and becomes +0.005 when 2022 is excluded. Across all calendar months, that next-month correlation is +0.075. Thus the data do not provide a stable descriptive cooling pattern across these specifications. This is neither an estimated cooling effect nor evidence that watering has no physiological or local microclimatic benefit.</p>
<p>The previous-LST/current-watering residual correlation for litres is +0.057 in the main season. These local residual descriptions ask a different question from the Berlin-wide DWD response analysis: actual year-month adjustment removes shared city-wide temporal variation, including common heat episodes. They cannot disprove a city-wide heat response.</p>
<details><summary>All 54 local descriptive comparisons, including season, year and count sensitivities</summary><div class="scroll">{all_grid.to_html(index=False,border=0,float_format=lambda x:f'{x:.3f}')}</div></details>
<p class="sub">The relative-count screen retains LST counts at least half the area's observed maximum. It is a diagnostic restriction, not validated cloud coverage. No p-values, confidence intervals or causal effect estimates are reported for this provisional extension. Reported rainfall is preserved under an explicitly unverified source label and is not used as a physical adjustment variable.</p>
<h3>What is needed to strengthen the interpretation</h3>
<p>The next input is the extraction script or metadata defining the original polygons, both Buckow components, Landsat processing, LST_C_count and rainfall. These details determine whether the geographic alignment and temperature summaries can become substantive thesis evidence. The three research questions remain provisional; a weak association alone does not justify changing them.</p>'''
    markdown = '''## Supplied monthly LST: new results

The supplied CSV is now incorporated. A new **6,596-row Ortsteil-month panel** contains events, litres and distinct trees for 97 current official areas. All linked watering events reconcile. Temperature comparisons use **93 provisionally aligned areas**.

- **Source audit:** 9,312 rows, 96 distinct names, and 19.4% missing LST. Buckow has two different rows per month. Schlachtensee is absent; Nikolassee and Zehlendorf are excluded because the original boundary version is unknown.
- **Count definition is missing:** `LST_C_count` ranges up to 64,360 and must not be treated as the number of satellite images. Acquisition dates, cloud filtering, compositing and rainfall provenance are also unspecified.
- **Main seasonal comparison:** for litres/ha, same-month raw Spearman correlation is +0.299; area-and-year-month residual Pearson correlation with log(1 + litres/ha) is +0.025. These are different statistics; the full report also supplies a matched Pearson comparison.
- **Next-month temperatures:** the residual correlation with litres/ha is −0.024, changes to +0.005 without 2022, and is +0.075 using all calendar months. This is not a stable descriptive cooling pattern and is not an estimate of a causal effect.
- **Next input:** the extraction script or source metadata is needed to confirm geography, the Buckow components, count semantics, Landsat processing and rainfall.

The DWD results below remain separate evidence about shared Berlin-wide air-temperature variation. The local residual comparisons remove that common monthly variation and cannot disprove a city-wide heat response.

'''
    workbook = {
        "ortsteil_panel": json.loads(tables["ortsteil_month_watering_lst_2020_2025"].to_json(orient="records",date_format="iso")),
        "ortsteil_correlations": json.loads(corr.to_json(orient="records")),
        "ortsteil_audit": meta,
    }
    (output / "workbook_data.json").write_text(json.dumps(workbook,ensure_ascii=False))
    return section, markdown
