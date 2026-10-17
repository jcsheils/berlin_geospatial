"""Create reviewable figures, a self-contained report and workbook input."""
from __future__ import annotations

import base64
import calendar
import html
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("MPLCONFIGDIR", "/tmp/berlin-watering-response-mpl")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator, StrMethodFormatter
import numpy as np
import pandas as pd

from berlin_heat.watering_response import DWD_URL, DWD_DESCRIPTION, METRICS, build_response_tables

OUT = ROOT / "output/watering_response"
LABELS = {METRICS[0]: "Events", METRICS[1]: "Litres", METRICS[2]: "Distinct trees"}
COLORS = {2020: "#8a929a", 2021: "#4d7895", 2022: "#bb622c", 2023: "#7b709d", 2024: "#598372", 2025: "#384c61"}


def records(frame):
    return json.loads(frame.to_json(orient="records", date_format="iso"))


def build_report():
    result = build_response_tables(ROOT, OUT)
    local_section, local_markdown = "", ""
    if (ROOT / "data/raw/supervisor/berlin_ortsteile_LST_rain_2018_2025_LNDSAT.csv").exists():
        from build_ortsteil_report import build_ortsteil_section
        local_section, local_markdown = build_ortsteil_section(ROOT)
    t, metadata = result["tables"], result["metadata"]
    figures = OUT / "figures"
    figures.mkdir(exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "axes.titlelocation": "left", "axes.labelcolor": "#30404b",
                         "text.color": "#253541", "axes.edgecolor": "#bec7cb",
                         "savefig.facecolor": "white"})
    city = t["berlin_month_weather_watering"]
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    for ax, metric in zip(axes, METRICS):
        for year, data in city.groupby("year"):
            ax.plot(data.calendar_month, data[metric], label=str(year), color=COLORS[year],
                    lw=2.4 if year == 2022 else 1.5, marker="o", markersize=3)
        ax.set_title(LABELS[metric], fontweight="bold")
        ax.set_xticks(range(1, 13), list(calendar.month_abbr)[1:], rotation=45)
        ax.set_ylim(bottom=0)
        ax.yaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
        ax.grid(axis="y", alpha=.15)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=6, frameon=False, bbox_to_anchor=(.5, .015))
    fig.suptitle("Recorded watering by calendar month and year", x=.055, ha="left", fontsize=16, fontweight="bold")
    fig.text(.055, .89, "Matched platform records. May 2020 is partial; January–April 2020 are unavailable.", color="#5f6b71")
    fig.subplots_adjust(left=.055, right=.99, top=.79, bottom=.24, wspace=.28)
    fig.savefig(figures / "01_monthly_watering.png", dpi=160)
    plt.close(fig)

    summer = t["berlin_june_september_comparison"]
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.5))
    for ax, column, title in zip(axes, [METRICS[0], METRICS[1], "hot_days_ge_30c"],
                                ["Recorded events", "Recorded litres", "Hot days (maximum ≥30 °C)"]):
        ax.bar(summer.year.astype(str), summer[column], color=[COLORS[y] for y in summer.year], width=.65)
        ax.set_title(title, fontsize=10, fontweight="bold")
        ax.yaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
        ax.grid(axis="y", alpha=.15)
    axes[2].yaxis.set_major_locator(MaxNLocator(nbins=5, integer=True))
    fig.suptitle("The same June–September window gives a different comparison", x=.06, ha="left", fontsize=15, fontweight="bold")
    fig.text(.06, .86, "All six watering windows are observed. Weather is from Berlin-Tempelhof, a single DWD station.", color="#5f6b71")
    fig.subplots_adjust(left=.06, right=.99, top=.74, bottom=.13, wspace=.34)
    fig.savefig(figures / "02_comparable_seasons.png", dpi=160)
    plt.close(fig)

    coefficients = t["monthly_adjusted_associations"]
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.3))
    for ax, term, title in zip(axes, ["temperature_per_5c", "rainfall_per_10mm"],
                               ["Temperature: +5 °C", "Rainfall: +10 mm"]):
        for i, metric in enumerate(METRICS):
            for j, (timing, color) in enumerate([("same_month", "#bb622c"), ("previous_month", "#4d7895")]):
                row = coefficients[(coefficients["sample"] == "2021-2025") & (coefficients.term == term)
                                   & (coefficients.outcome == metric) & (coefficients.timing == timing)].iloc[0]
                y = 2 - i + (.12 if j == 0 else -.12)
                ax.errorbar(row.coefficient_log1p, y,
                            xerr=[[row.coefficient_log1p-row.approx_95_low], [row.approx_95_high-row.coefficient_log1p]],
                            fmt="o", color=color, capsize=3, label=timing.replace("_", " ") if i == 0 else None)
        ax.axvline(0, color="#a8b0b5", lw=1)
        ax.set_yticks([2, 1, 0], ["Events", "Litres", "Distinct trees"])
        ax.set_ylim(-.5, 2.5)
        ax.set_title(title, fontweight="bold")
        ax.set_xlabel("Association with log(1 + monthly recorded activity)")
        ax.grid(axis="x", alpha=.15)
    handles, labels = axes[1].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", bbox_to_anchor=(.5, .075), ncol=2, frameon=False)
    fig.suptitle("Same-month and previous-month weather associations", x=.08, ha="left", fontsize=15, fontweight="bold")
    fig.text(.08, .87, "2021–2025 · 58 months per model · calendar-month and year adjustment", color="#5f6b71")
    fig.text(.08, .035, "Bars: approximate 95% HAC(3) intervals, without multiplicity adjustment. Retrospective exploratory associations; no causal interpretation.", fontsize=9)
    fig.subplots_adjust(left=.11, right=.98, top=.76, bottom=.25, wspace=.30)
    fig.savefig(figures / "03_weather_associations.png", dpi=160)
    plt.close(fig)

    social = t["social_status_month_watering"]
    social_summary = social[social.year.ge(2021)].groupby("social_status_2024", as_index=False).agg(
        current_inventory_trees=("current_inventory_trees", "first"),
        mean_monthly_events_per_1000_trees=("recorded_events_per_1000_current_inventory_trees", "mean"),
        mean_monthly_litres_per_tree=("recorded_litres_per_current_inventory_tree", "mean"),
        mean_monthly_reach_pct=("recorded_reach_pct_current_inventory", "mean"))
    counts = t["lor_month_watering_social_context"].groupby("social_status_2024").plr_id.nunique().rename("neighbourhoods")
    social_summary = social_summary.merge(counts, on="social_status_2024", validate="one_to_one")
    social_summary.to_csv(OUT / "tables/social_status_summary_2021_2025.csv", index=False)
    ordered = social_summary.set_index("social_status_2024").loc[["High", "Middle", "Low", "Very low"]]
    fig, ax = plt.subplots(figsize=(8, 4.4))
    ax.bar(ordered.index, ordered.mean_monthly_events_per_1000_trees, color="#4d7895", width=.6)
    ax.set_ylabel("Events per 1,000 inventory trees\n(mean per month)")
    ax.set_title("Recorded care does not rise steadily with social advantage", fontweight="bold", pad=22)
    ax.grid(axis="y", alpha=.15)
    for i, v in enumerate(ordered.mean_monthly_events_per_1000_trees):
        ax.text(i, v + .02, f"{v:.2f}", ha="center")
    ax.set_ylim(0, 1.16)
    fig.text(.12, .025, "2021–2025 monthly average. MSS status refers to end-2024; this is a descriptive group comparison.", fontsize=8)
    fig.subplots_adjust(left=.12, right=.97, bottom=.16, top=.82)
    fig.savefig(figures / "04_social_status.png", dpi=160)
    plt.close(fig)

    annual = t["berlin_year_watering"]
    annual_html = annual.rename(columns={"year": "Year", METRICS[0]: "Events", METRICS[1]: "Litres", METRICS[2]: "Distinct trees", "period": "Observed period"}).to_html(index=False, border=0, float_format=lambda x: f"{x:,.0f}")
    seasons_html = summer[["year", *METRICS, "mean_air_temperature_c", "rainfall_mm", "hot_days_ge_30c"]].rename(columns={"year":"Year", **LABELS, "mean_air_temperature_c":"Mean air temp (°C)", "rainfall_mm":"Rain (mm)", "hot_days_ge_30c":"Days ≥30 °C"}).to_html(index=False, border=0, na_rep="Incomplete", float_format=lambda x:f"{x:,.1f}")
    model_html = coefficients.rename(columns={"coefficient_log1p":"Slope", "approx_95_low":"95% low", "approx_95_high":"95% high", "sample":"Years", "timing":"Weather timing", "outcome":"Outcome", "term":"Predictor", "n_months":"Months"})[["Years", "Weather timing", "Outcome", "Predictor", "Months", "Slope", "95% low", "95% high"]].replace({"Outcome":LABELS, "Weather timing":{"same_month":"Same month", "previous_month":"Previous month"}, "Predictor":{"temperature_per_5c":"Temperature / 5 °C", "rainfall_per_10mm":"Rainfall / 10 mm"}}).to_html(index=False, border=0, float_format=lambda x:f"{x:.3f}")
    def image_tag(name, alt):
        encoded = base64.b64encode((figures / name).read_bytes()).decode()
        return f'<img src="data:image/png;base64,{encoded}" alt="{html.escape(alt)}">'
    report = f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Berlin watering patterns and weather</title><style>
body{{font:16px/1.6 -apple-system,BlinkMacSystemFont,"Helvetica Neue",sans-serif;color:#253541;background:#f5f6f6;margin:0}}main{{max-width:1080px;margin:30px auto;background:white;padding:42px 48px}}h1{{font-size:34px;line-height:1.15;margin:8px 0 14px}}h2{{font-size:23px;margin-top:42px}}h3{{font-size:18px}}.sub{{color:#617079}}.lead{{font-size:19px;border-left:3px solid #bb622c;padding-left:20px}}table{{border-collapse:collapse;width:100%;font-size:13px}}th{{background:#e9eef1;text-align:left}}th,td{{padding:9px;border-bottom:1px solid #dae0e3}}td{{font-variant-numeric:tabular-nums}}img{{width:100%;height:auto;margin:12px 0}}a{{color:#27628b}}.scroll{{overflow-x:auto}}li{{margin:7px 0}}details{{margin-top:20px}}summary{{cursor:pointer;font-weight:600}}@media(max-width:700px){{main{{padding:24px;margin:0}}h1{{font-size:28px}}}}@media print{{body{{background:white}}main{{margin:0;padding:0}}details{{display:block}}}}
</style><main><p class="sub">Exploratory stage · 29 September 2026 · recorded citizen care</p>
<h1>Berlin watering patterns and weather</h1>
<p class="lead">Warmer months coincide with more recorded events and more distinct trees watered after broad seasonal and yearly adjustment. Previous-month temperature is much less informative in this initial monthly analysis. These findings do not establish the cause of the 2022 increase or a cooling effect of watering.</p>
<p>The agreed stage retains the three research questions provisionally. It describes monthly care, examines the weather-response question, and checks the feasibility of subsequent LST analysis. A null association is a valid result.</p>
<h2>1. Monthly counts are ready</h2>
<p>The panel contains <strong>816 district-months</strong> and <strong>36,856 LOR neighbourhood-months</strong> from May 2020 to December 2025. It reconciles to <strong>57,786 geographically assigned events, 2,249,502 litres and 11,127 distinct trees</strong>. Events and litres exclude 688 source events (28,485 litres) that could not be assigned through the existing tree crosswalk.</p>
<p>Counts describe platform records. A recorded zero does not establish that no municipal, private or unlogged watering occurred. Rates use the current tree inventory. Distinct trees are counted within each period and must not be added across months to obtain annual distinct counts.</p>
<div class="scroll">{annual_html}</div>
{image_tag("01_monthly_watering.png", "Monthly events, litres and distinct trees for 2020 through 2025")}
<h2>2. The 2022 peak needs a more precise explanation</h2>
<p>2022 has the largest annual event and litre totals in this linked sample. However, the comparable June–September period has <strong>13,838 events in 2020 and 12,660 in 2022</strong>. Distinct trees are also higher in that 2020 window (3,734 versus 3,354), whereas 2022 has more litres (604,930 versus 425,720). June 2021 also has more events than June 2022.</p>
<p>At Tempelhof, June–September 2022 has 21 days with maximum air temperature of at least 30 °C and less recorded rainfall than the other complete-rainfall windows shown. Its seasonal mean temperature is close to 2020 and 2021, and below 2023 and 2024. Thus a single annual count or average temperature cannot explain participation. Campaigns, platform use, repeated care and recording changes remain plausible alternatives.</p>
{image_tag("02_comparable_seasons.png", "Comparable June through September events, litres and hot days")}
<div class="scroll">{seasons_html}</div>
<p class="sub">June–September 2023 rainfall is incomplete because three June days are missing. No zero substitution or annual ranking of that missing total is made.</p>
<h2>3. Initial weather associations</h2>
<p>We downloaded the public historical archive for <a href="{DWD_URL}">DWD Berlin-Tempelhof, station 00433</a>. This provides air temperature and precipitation as shared temporal context for Berlin. It does not provide district-specific heat or Landsat land-surface temperature.</p>
<p>Separate models relate log(1 + monthly activity) to temperature and rainfall in either the same month or the preceding calendar month. Each includes calendar-month and year indicators. There are 60 eligible complete calendar months in 2021–2025; two incomplete rainfall months leave 58 observations per model. Approximate uncertainty intervals use three-month HAC errors with actual calendar gaps preserved.</p>
{image_tag("03_weather_associations.png", "Adjusted temperature and rainfall association estimates with approximate uncertainty intervals")}
<ul><li><strong>Same-month heat alignment:</strong> the event-count slope is 0.817 log(1 + events) units per 5 °C (approximate 95% interval 0.142 to 1.492). Distinct-tree counts have a similar positive estimate. The litre estimate is positive but less precise.</li>
<li><strong>Previous-month heat:</strong> the event-count slope is 0.103 (−0.515 to 0.722). All three previous-month temperature intervals cross zero. This does not rule out a response operating over days rather than a full calendar month.</li>
<li><strong>Rainfall:</strong> these specifications do not give precise adjusted evidence of a rainfall association. Rainfall is not a complete measure of soil or tree water stress.</li>
<li><strong>Excluding 2022:</strong> the positive same-month temperature alignment in events and distinct trees remains. The pattern therefore does not depend solely on retaining that year.</li></ul>
<p>These are retrospective exploratory comparisons with several outcomes and specifications. The intervals are approximate and not adjusted for multiple comparisons. The log(1 + activity) slopes are not exact percentage changes in arithmetic mean activity. Broad seasonal adjustment does not remove all confounding, platform growth or changing logging. Same-month data cannot establish whether heat preceded watering within the month.</p>
<details><summary>Full model results, including the sensitivity analysis</summary><div class="scroll">{model_html}</div></details>
<h2>4. Socioeconomic context</h2>
{image_tag("04_social_status.png", "Recorded event rates by neighbourhood social status")}
<p>Across the 60 complete months, middle-status neighbourhoods average 0.987 recorded events per 1,000 current inventory trees per month, compared with 0.369 in high-status, 0.253 in low-status and 0.454 in very-low-status neighbourhoods. This is not a monotonic rich-to-poor gradient. Differences in street/park tree composition and the denominator also matter.</p>
<p>The MSS categories refer to the end of 2024 and classify neighbourhood context, not individual volunteers or historical district income. Seven LORs are unclassified and retained separately. This first comparison does not estimate whether vulnerability modifies the heat-response slope. That requires a specified repeated-neighbourhood model with shared-weather uncertainty.</p>
{local_section}
<h2>6. What remains necessary</h2>
<ul><li><strong>Confirm the monthly LST source metadata.</strong> The CSV is now available and its provisional audit is above. The extraction script must establish rainfall provenance, count semantics, cloud handling and monthly compositing.</li>
<li><strong>Confirm the original geography.</strong> Trees have been assigned to current official Ortsteil polygons. The source polygons and Buckow component identifiers are needed to validate that alignment and resolve the excluded areas.</li>
<li><strong>Refine response timing and vulnerability.</strong> Daily watering dates support shorter antecedent-weather windows, subject to timestamp and recording audits. Assess differential response using an explicitly specified model.</li>
<li><strong>Assess cooling separately.</strong> Provisional same-month and next-month LST descriptions are now available. A causal cooling claim additionally requires a credible comparison design, exposure completeness and adequate detectability. No causal cooling estimate is produced here.</li>
<li><strong>Keep municipal priorities conditional.</strong> Care-versus-need screening can proceed with independent need measures. An allocation that maximises cooling has not been established.</li></ul>
<h2>Sources and measurement notes</h2>
<p>Watering: Gieß den Kiez snapshot and existing geographically assigned tree-day/foundation products. Spatial assignment: Berlin LOR 2021 boundaries. Social context: <a href="https://gdi.berlin.de/services/wfs/mss_2025">Berlin MSS 2025</a>, reference 31 December 2024. Weather: <a href="{DWD_DESCRIPTION}">DWD daily station observations, v24.3 documentation</a>, CC BY 4.0; historical archive downloaded 29 September 2026.</p>
<p>DWD climate quality code is 9 throughout this extraction, meaning not all parameters are corrected under the documented quality-code scheme. Missing daily precipitation occurs on ten days in June and October 2023. Monthly values require every expected daily measurement. Weather station metadata records small position updates during 2022 and 2025. Original metadata and checksums are retained with the analytical outputs.</p>
</main></html>'''
    (OUT / "report.html").write_text(report, encoding="utf-8")
    markdown = """# Berlin watering patterns and weather

Exploratory results · 29 September 2026

The monthly summaries are complete for the available recorded-care data: **816 district-months and 36,856 LOR neighbourhood-months**, with separate event, litre and distinct-tree counts. The self-contained HTML report includes figures, source notes and the full model results.

## Main findings

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
"""
    if local_markdown:
        markdown = markdown.replace("## Main findings", local_markdown + "## Berlin-wide DWD findings", 1)
    (OUT / "report.md").write_text(markdown, encoding="utf-8")
    workbook_data = {name: records(frame) for name, frame in t.items()
                     if name in ["berlin_month_weather_watering", "district_month_watering",
                                 "berlin_year_watering", "berlin_june_september_comparison",
                                 "social_status_month_watering", "monthly_adjusted_associations"]}
    workbook_data["social_status_summary"] = records(social_summary)
    workbook_data["metadata"] = metadata
    (OUT / "workbook_data.json").write_text(json.dumps(workbook_data, ensure_ascii=False), encoding="utf-8")
    print(f"Created {OUT / 'report.html'} and four figures.")


if __name__ == "__main__":
    build_report()
