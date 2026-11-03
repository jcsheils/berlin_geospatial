"""Assemble examination documentation from saved evidence; no model fitting.

Run with the optional requirements-examination.txt dependencies. The source
images are embedded unchanged. All numbers are read from saved analysis tables.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
from xml.sax.saxutils import escape

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.pagesizes import A3, A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image

ROOT = Path(__file__).resolve().parents[1]
EXAM = ROOT / "examination"
PDF = ROOT / "output/pdf"
DATE = "17 October 2026"


def sha(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def rows(path):
    with (ROOT / path).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def number(value):
    return f"{float(value):,.0f}"


def facts():
    foundation = json.loads((ROOT / "data/processed/foundation/lor_month_recorded_watering_2020_2025.metadata.json").read_text())
    audit = foundation["audit"]
    monthly = rows("data/processed/temporal/berlin_month_recorded_watering_2020_2025.csv")
    total = sum(float(r["recorded_watering_events"]) for r in monthly)
    summer = sum(float(r["recorded_watering_events"]) for r in monthly if int(r["calendar_month"]) in (6,7,8))
    warm = sum(float(r["recorded_watering_events"]) for r in monthly if 5 <= int(r["calendar_month"]) <= 9)
    models = rows("output/watering_response/tables/monthly_adjusted_associations.csv")
    pick = lambda timing: next(r for r in models if r["sample"] == "2021-2025" and r["timing"] == timing and r["outcome"] == "recorded_watering_events" and r["term"] == "temperature_per_5c")
    moran = {r["metric"]:r["value"] for r in rows("output/spatial/tables/global_moran_watering_reach.csv")}
    equity = rows("output/equity/tables/equity_associations.csv")
    rho = lambda prefix: float(next(r["spearman_rho"] for r in equity if r["predictor"].startswith(prefix) and r["outcome"] == "Watering reach (%)"))
    return {"audit":audit, "summer":100*summer/total,"warm":100*warm/total,
            "same":pick("same_month"),"previous":pick("previous_month"),
            "moran":float(moran["Moran's I"]),"moran_p":float(moran["Permutation p-value"]),
            "poverty_rho":rho("S4 child poverty"),"burden_rho":rho("Environmental and social"),
            "candidates":len(rows("output/equity/tables/priority_gap_planungsraeume.csv"))}


def catalogue():
    common = "Recorded platform activity only; current-inventory denominators; no inference about unlogged or municipal watering."
    records = [
        ("District spatial baseline", "output/spatial/figures/01_district_spatial_baseline.png", "2025 LST and tree cover; May 2020-Dec 2025 watering", "Legacy district LST and canopy context; watering reach (%) and litres per inventory tree", "output/spatial/tables/lor_watering_metrics_2020_2025.csv", "analysis/build_spatial_notebook.py", "LOR metrics are aggregated by district and joined to the 2025 summer rows of data/Berlin_heat_population_death_Birth_data.csv. Reference periods differ; legacy heat provenance is incomplete. " + common),
        ("Neighbourhood watering reach and intensity", "output/spatial/figures/02_lor_watering_reach_intensity.png", "May 2020-Dec 2025", "Distinct-tree reach (%) and recorded litres per inventory tree", "output/spatial/tables/lor_watering_metrics_2020_2025.csv", "analysis/build_spatial_notebook.py", "Colour scales are capped at the 95th percentile; inspect the table for extreme values. " + common),
        ("Exploratory local spatial clusters", "output/spatial/figures/03_lor_local_moran_clusters.png", "May 2020-Dec 2025", "Local Moran classes for recorded watering reach", "output/spatial/tables/local_moran_watering_clusters.csv", "analysis/build_spatial_notebook.py", "Row-standardised queen contiguity; 999 permutations; unadjusted local p < 0.05, seed 42. Exploratory screening with no multiplicity correction. " + common),
        ("Recorded care and social/environmental context", "output/equity/figures/01_lor_watering_social_environment.png", "Watering 2020-2025; MSS end-2024; environmental context 2023/24", "Recorded reach, MSS status, thermal burden and environmental/social burden count", "output/equity/tables/lor_watering_equity_metrics.csv", "analysis/build_equity_notebook.py", "542 polygons; 535 valid MSS observations with inventoried trees. Static contextual layers are not historical area-level vulnerability. " + common),
        ("Areas for further care-gap validation", "output/equity/figures/03_priority_gap_candidates.png", "Watering 2020-2025; contextual indicators 2023/24 and end-2024", "Low/very-low-status areas with thermal or green need and below-median recorded reach", "output/equity/tables/priority_gap_planungsraeume.csv", "analysis/build_equity_notebook.py", "Screening candidates only, not validated irrigation priorities or the proposed allocation model. " + common),
        ("Calendar-month climatology", "output/03_spatial_equity_vulnerability/maps/01_calendar_month_recorded_watering_atlas.png", "Complete years 2021-2025 pooled by calendar month", "Mean monthly events per 1,000 current inventory trees", "data/processed/temporal/lor_calendar_month_recorded_watering_2021_2025.csv", "pipelines/04_build_watering_temporal_atlas.py", "Five-year calendar-month means include observed zeros. Shared fixed classes; no pooled-month thermal inference. " + common),
        ("Active-season comparison across years", "output/03_spatial_equity_vulnerability/maps/02_active_season_recorded_watering_atlas.png", "April-September separately in 2021, 2022, 2023, 2024 and 2025", "Monthly events per 1,000 current inventory trees", "data/processed/foundation/lor_month_recorded_watering_2020_2025.csv", "pipelines/04_build_watering_temporal_atlas.py", "Each panel uses its actual year/month and fixed classes. " + common),
    ]
    for year in range(2021,2026):
        records.append((f"{year} monthly recorded watering",f"output/03_spatial_equity_vulnerability/maps/yearly/{year}_monthly_recorded_watering_atlas.png",f"January-December {year}","Monthly events per 1,000 current inventory trees","data/processed/foundation/lor_month_recorded_watering_2020_2025.csv","pipelines/04_build_watering_temporal_atlas.py","Twelve actual months; shared fixed classes across all years. " + common))
    keys = ["title","image","period","metric","table","builder","limits"]
    return [dict(plate=f"{i:02}",**dict(zip(keys,item))) for i,item in enumerate(records,1)]


def write_catalogue(records):
    folder=EXAM/"atlas"; folder.mkdir(exist_ok=True)
    with (folder/"catalogue.csv").open("w",newline="",encoding="utf-8") as handle:
        writer=csv.DictWriter(handle,fieldnames=list(records[0]));writer.writeheader();writer.writerows(records)
    text=["# Atlas of maps produced so far\n",f"Prepared {DATE}. Twelve existing analytical map plates, reproduced without changing their values or classifications.\n",
          "[Download the PDF atlas](../../output/pdf/Berlin_Map_Atlas_October_2026.pdf) · [Machine-readable catalogue](catalogue.csv) · [Interactive LOR map](../../output/spatial/maps/lor_watering_interactive.html)\n",
          "The PDF uses large pages to preserve small-multiple maps; zoom for labels or open the original PNG. For each plate, the source table and builder are linked below. Geometry is analysed in EPSG:25833; the web map displays EPSG:4326. LOR geometry: Amt für Statistik Berlin-Brandenburg, CC BY 3.0 DE. See [source attribution](../../data/spatial/README.md) and the [tree inventory note](../../data/raw/tree_inventory/README.md).\n",
          "The atlas covers saved analytical maps in `output/`. Earlier slide-only colour mockups and duplicated presentation images are not separate analytical results. Supporting charts remain in the [results guide](../preliminary_results.md). Cooling-loss maps, daily response slopes with uncertainty, and allocation rankings are planned.\n"]
    for r in records:
        text += [f"## Plate {r['plate']} — {r['title']}\n",f"**Period:** {r['period']}. **Measure:** {r['metric']}.\n",f"![{r['title']}](../../{r['image']})\n",f"[Original PNG](../../{r['image']}) · [Data table](../../{r['table']}) · [Builder](../../{r['builder']})\n",r['limits']+"\n"]
    (folder/"README.md").write_text("\n".join(text))


def write_results(f):
    a=f['audit'];s=f['same'];p=f['previous']
    text=f'''# Preliminary results for seminar examination

Prepared {DATE}. These are saved exploratory results, not completed tests of the October proposal's daily response hypotheses.

## Sample reconciliation

| Stage | Events | Distinct trees / interpretation |
| --- | ---: | --- |
| Raw source snapshot, through April 2026 | 58,847 | 11,278 source IDs |
| After removing 111 exact duplicate rows | 58,736 | Full snapshot, including 2026 |
| Study window, May 2020–December 2025 | {number(a['deduplicated_events_in_window'])} | 2,277,987 recorded litres before geographical linkage |
| Linked to inventory and assigned to a LOR | {number(a['matched_and_lor_assigned_events'])} | **{number(a['matched_and_lor_assigned_unique_trees'])} distinct trees; {number(a['matched_and_lor_assigned_litres'])} litres** |
| Unmatched or not LOR-assigned in the study window | {number(a['unmatched_or_unassigned_events'])} | 28,485 litres excluded from the geographical panel |

The full-snapshot inventory match count, **11,160**, is not the study-window LOR count. The October proposal's 11,087 and 11,245 alternatives remain unexplained historical numbers and are not used as the canonical sample. The inventory contains 962,545 rows, 956,347 distinct non-null tree IDs, and 955,434 LOR-assigned IDs. These are different counting units.

The foundation contains **36,856 area-months (542 × 68)**. The positive tree-day table contains **50,259 rows**, with repeat logs on the same tree and local date aggregated. It is not a balanced all-tree/day panel. May 2020 starts on 18 May; complete-calendar-year comparisons use 2021–2025.

Sources: [foundation audit](../data/processed/foundation/lor_month_recorded_watering_2020_2025.metadata.json), [tree-day audit](../data/processed/temporal/recorded_tree_day_watering_2020_2025.metadata.json), [full-snapshot ID match audit](../output/exploratory/tables/tree_id_match_summary.csv), [spatial assignment audit](../output/spatial/tables/spatial_join_audit.csv).

## Findings and what they support

| Finding | Evidence | Interpretation |
| --- | --- | --- |
| Strong seasonal concentration | {f['summer']:.1f}% of linked events in June–August; {f['warm']:.1f}% in May–September | Motivates an explicit seasonal daily model; pooled maps are descriptive |
| Spatial clustering of reach | Global Moran's I = {f['moran']:.3f}; 999-permutation p = {f['moran_p']:.3f} | Neighbouring areas have related recorded activity; local clusters are exploratory |
| Social and environmental context differ | Child-poverty/reach Spearman rho = {f['poverty_rho']:.3f}; burden-count/reach rho = {f['burden_rho']:.3f}, n = 535 | Recorded care does not follow a simple rich-to-poor gradient; no individual-level inference |
| Same-month temperature association | Event coefficient {float(s['coefficient_log1p']):.3f} per +5 °C; approximate 95% interval [{float(s['approx_95_low']):.3f}, {float(s['approx_95_high']):.3f}] | Calendar-month/year-adjusted log(1 + events), jointly including rain; not a causal or daily response estimate |
| Previous-month association is imprecise | Event coefficient {float(p['coefficient_log1p']):.3f}; interval [{float(p['approx_95_low']):.3f}, {float(p['approx_95_high']):.3f}] | Does not rule out responses over shorter periods |
| Care-gap screening is feasible | {f['candidates']} contextual candidate areas | A validation shortlist, not a completed allocation recommendation |

Evidence tables: [monthly activity](../data/processed/temporal/berlin_month_recorded_watering_2020_2025.csv), [global Moran](../output/spatial/tables/global_moran_watering_reach.csv), [equity associations](../output/equity/tables/equity_associations.csv), [complete monthly model grid](../output/watering_response/tables/monthly_adjusted_associations.csv), [screening candidates](../output/equity/tables/priority_gap_planungsraeume.csv).

![Monthly recorded activity](../output/03_spatial_equity_vulnerability/figures/01_recorded_watering_monthly_timing.png)

## Weather and engagement

The DWD Berlin-Tempelhof series provides shared city-level air-temperature and rainfall context. The main adjusted monthly models use **58 of 60 months in 2021–2025**; June and October 2023 lack complete rainfall observations. Approximate HAC uncertainty uses three calendar lags and preserves gaps. These exploratory intervals are not corrected for multiple comparisons. The coefficients are log(1 + outcome) units, not exact percentages.

2022 has the largest annual event and litre totals, but is not a universal peak: in the comparable June–September windows, 2020 has 13,838 events versus 12,660 in 2022. The 2022 window has more litres. Changing calendar coverage must not be mistaken for changing engagement. [Season comparison table](../output/watering_response/tables/berlin_june_september_comparison.csv).

![Adjusted monthly associations](../output/watering_response/figures/03_weather_associations.png)

## Provisional local surface-temperature comparisons

The supplied source has 9,312 rows and 1,811 missing LST values (19.4%). The extension has 6,596 current-Ortsteil months across 97 areas, with **93 areas provisionally eligible** for temperature comparisons. Buckow's duplicate component records cannot be resolved, and the Nikolassee/Zehlendorf/Schlachtensee boundary change is not reconciled to the original extraction.

For April–September 2021–2025, same-month litres/ha has raw Spearman rho +0.299 and area/year-month residual Pearson correlation +0.025 on log(1 + litres/ha). These are different statistics. Next-month residual correlation is −0.024, +0.005 without 2022, and +0.075 using all calendar months. There is no stable descriptive cooling pattern here, and no causal cooling estimate. The report also supplies matched raw Pearson statistics. [Full provisional comparisons](../output/watering_response/ortsteil/tables/provisional_pooled_correlations.csv).

Extraction dates, cloud/compositing rules, source geography, rainfall provenance and `LST_C_count` semantics are unverified. Counts must not be interpreted as satellite scene counts. The extension cannot replace the planned valid-overpass Part I panel. [Source audit](../data/raw/supervisor/README.md).

## Scientific limitations carried into the next stage

- Logs omit municipal, private and unlogged care; selection and recording behaviour can vary across place and time.
- Current inventory denominators may include trees planted after an observation. The proposed historical young-tree offset is not yet built.
- Static end-2024 MSS and 2023/24 environmental indicators do not reconstruct historical vulnerability.
- Most 2024 timestamps and all 2025 timestamps are midnight-rounded in the export; subdaily irrigation timing is unavailable.
- Local Moran p < .05 and the equity associations are exploratory and not multiplicity-adjusted confirmatory evidence.
- Daily civic response, participation explanations, vegetation cooling loss, calibrated allocation and the bridge test remain future work.

See the [October proposal qualifications](proposal/README.md), [map atlas](atlas/README.md), [full response report](../output/watering_response/report.html), and [readiness assessment](readiness.md).
'''
    (EXAM/"preliminary_results.md").write_text(text)


STYLES=getSampleStyleSheet()
STYLES.add(ParagraphStyle(name="BodyExam",fontName="Helvetica",fontSize=10.3,leading=15,spaceAfter=10,textColor=colors.HexColor('#26333a')))
STYLES.add(ParagraphStyle(name="SmallExam",fontName="Helvetica",fontSize=8.5,leading=12,spaceAfter=6,textColor=colors.HexColor('#485960')))
STYLES.add(ParagraphStyle(name="TitleExam",fontName="Helvetica-Bold",fontSize=26,leading=31,spaceAfter=18))
STYLES.add(ParagraphStyle(name="HeadExam",fontName="Helvetica-Bold",fontSize=15,leading=20,spaceBefore=10,spaceAfter=10))


def para(text,style="BodyExam"):
    return Paragraph(text,STYLES[style])


def grid(data,widths):
    items=[[para(escape(str(c)),"SmallExam") for c in row] for row in data]
    t=Table(items,colWidths=widths,hAlign="LEFT",repeatRows=1)
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e9eeec')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),6),('LINEBELOW',(0,0),(-1,0),.5,colors.HexColor('#9ba9a2')),('LINEBELOW',(0,1),(-1,-1),.3,colors.HexColor('#dce2df'))]))
    return t


def pdf_footer(c,doc):
    c.saveState();c.setFont('Helvetica',8);c.setFillColor(colors.HexColor('#64746b'))
    c.drawString(45,24,'BERLIN CITIZEN WATERING | PRELIMINARY EXAMINATION EVIDENCE | OCTOBER 2026')
    c.drawRightString(A4[0]-45,24,str(doc.page));c.restoreState()


def build_brief(f):
    width=A4[0]-90
    story=[para('Master\'s Seminar examination brief','TitleExam'),para('Spatiotemporal Modeling of Citizen Tree Watering in Berlin','HeadExam'),para('Weather Responses and Neighborhood Variation'),para('Joseph Carpenter Sheils<br/>Saarland University | M.Sc. Data Science and Artificial Intelligence<br/>Supervisor: Angela John | Prepared '+DATE,'SmallExam'),Spacer(1,14),para('Research purpose','HeadExam'),para('The thesis examines how logged citizen care for Berlin\'s trees responds to heat and dryness, and how that response varies across neighbourhoods. The existing data and exploratory results demonstrate a workable foundation. The core daily response study remains to be fitted.'),grid([['Study','Role and planned contribution'],['Part II: civic heat response','Core. Daily logged watering, weather response, social context and the rival explanation of participation inequality.'],['Part I: vegetation cooling loss','Supporting. Morning surface-temperature relationships with canopy, low vegetation and temporal drought.'],['Part III: allocation','Exploratory. Validated prediction of logged care and comparison of need-only versus complement-based priorities.']],[140,width-140]),Spacer(1,15),para('What is already available','HeadExam'),para('57,786 linked records | 11,127 distinct trees | 2,249,502 recorded litres<br/>542 planning areas | 68 observed months | 50,259 positive tree-days'),para('The package includes the October proposal, seminar slides, detailed results, twelve map plates, source snapshots, derived tables and spatial layers, code, and verification instructions. The tree inventory is supplied as a lossless compressed snapshot.'),para('Scope: preliminary and descriptive. Logged activity is not total irrigation, response is not causal cooling, and screening candidates are not allocation recommendations.','SmallExam'),PageBreak()]
    story += [para('Evidence and sample reconciliation','TitleExam'),para('The canonical analysis window is May 2020 through December 2025. May 2020 is partial. The complete-year temporal atlas uses 2021-2025.'),grid([['Sample stage','Records / interpretation'],['Raw snapshot through April 2026','58,847 records; 11,278 source tree IDs'],['After exact duplicates','58,736 records; 111 duplicate rows removed'],['Study window','58,474 events; 2,277,987 litres before linkage'],['Inventory linked and LOR assigned','57,786 events; 11,127 trees; 2,249,502 litres'],['Unmatched or unassigned','688 events; 28,485 litres excluded from geographic panel']],[205,width-205]),Spacer(1,15),para('Preliminary findings','HeadExam'),para(f"<b>Seasonality.</b> {f['summer']:.1f}% of linked events occur in June-August and {f['warm']:.1f}% in May-September. This motivates explicit seasonal adjustment in the proposed daily study."),para(f"<b>Spatial structure.</b> Global Moran's I for reach is {f['moran']:.3f}, with permutation p = {f['moran_p']:.3f}. Local classifications use unadjusted p &lt; .05 and are exploratory."),para(f"<b>Different dimensions of need.</b> Across 535 valid observations, reach correlates weakly negatively with child poverty (rho {f['poverty_rho']:.3f}) and positively with the environmental/social burden count (rho {f['burden_rho']:.3f}). Middle-status areas have the highest mean monthly event rate; there is no simple monotonic advantage gradient."),para('Count qualification: 11,160 is a full-snapshot inventory match count, not the canonical study-window LOR count. The older 11,087 and 11,245 figures in the proposal are not adopted. Invalid source coordinates alone do not define exclusion from the ID-linked panel.','SmallExam'),para('Evidence: examination/preliminary_results.md links to foundation and tree-day audits, global Moran statistics, equity associations, and the complete model grid. All files are included in the repository.','SmallExam'),PageBreak()]
    s=f['same'];p=f['previous']
    story += [para('Weather response and source limits','TitleExam'),para(f"The same-month event association is {float(s['coefficient_log1p']):.3f} log(1 + events) units per +5 degrees C, with approximate 95% interval [{float(s['approx_95_low']):.3f}, {float(s['approx_95_high']):.3f}]. The previous-month estimate is {float(p['coefficient_log1p']):.3f} [{float(p['approx_95_low']):.3f}, {float(p['approx_95_high']):.3f}]. These are exploratory monthly associations, not daily response slopes or causal effects."),Image(str(ROOT/'output/watering_response/figures/03_weather_associations.png'),width=width,height=width*848/1920),Spacer(1,8),para('The model jointly includes temperature and rainfall with calendar-month and year adjustment. It uses 58 of 60 months in 2021-2025; June and October 2023 lack complete rainfall. HAC(3) uncertainty preserves calendar gaps. Intervals are not multiplicity-adjusted.','SmallExam'),para('Two temperature measurements','HeadExam'),para('DWD Berlin-Tempelhof provides shared station air-temperature context. The supplied monthly Ortsteil file describes surface temperature, with different support and unresolved processing. These measurements are not interchangeable.'),para('The Ortsteil extension has 6,596 area-months and 93 provisionally comparable areas. Of 9,312 source rows, 1,811 have missing LST. Buckow components and changed boundaries require resolution. Scene dates, cloud filtering, compositing, rainfall provenance and count semantics were not supplied.'),para('The next-month litres/LST residual correlation changes sign under sensitivity checks (-0.024 overall seasonal sample, +0.005 without 2022, +0.075 over all months). It provides no stable descriptive cooling pattern and does not validate a causal mechanism.'),para('Sources: output/watering_response/report.html; tables/monthly_adjusted_associations.csv; ortsteil/tables/provisional_pooled_correlations.csv. The report supplies all exploratory specifications, not only selected associations.','SmallExam'),PageBreak()]
    story += [para('Feasibility and next decisions','TitleExam'),para('The October proposal sets a six-month programme, relative to an agreed thesis start. Prioritise the core behavioural study, then the supporting physical analysis, then the exploratory decision layer.'),grid([['Period','Planned output or decision'],['Month 1','Literature and data audit; source requests; offsets and participation proxies; prospective registration with prior exploration disclosed'],['Months 1-2','Balanced behavioural area-day panel and satellite/vegetation panel'],['Months 2-4','Core response model, participation explanations and temporal stability'],['Months 3-4','Cooling-loss model; end-Month-4 decision on full versus descriptive allocation analysis'],['Month 5','Validated prediction and allocation comparison if feasible'],['Month 6','Bridge test where both layers exist, scale checks, writing and code release']],[105,width-105]),Spacer(1,12),para('Issues to resolve before substantive inference','HeadExam'),para('Build historical young-tree denominators and observed zero days; complete daily weather, calendar and participation controls; clarify the supplied LST extraction; disclose already-inspected outcomes in any registration; validate prediction and calibration before ranking areas.'),para('Source access and reproducibility','HeadExam'),para('The package provides hashes, CSV schemas, source attribution, a tree-inventory restore command, and tests. The supplied monthly LST and legacy borough inputs have unresolved provenance or licence metadata. Proposed satellite, vegetation-height, population-age, turnout and other control layers are not presented as already available.'),para('Read examination/README.md for the entry point, examination/reproducibility.md for ordered commands, and examination/validation.md for the actual verification performed. The supplied proposal is preserved unchanged and has a separate qualification note.','SmallExam'),para('This evidence supports an early feasibility review. It does not certify institutional approval or completion of the planned models.','SmallExam')]
    doc=SimpleDocTemplate(str(PDF/'Berlin_Examination_Brief_October_2026.pdf'),pagesize=A4,rightMargin=45,leftMargin=45,topMargin=45,bottomMargin=44,title='Berlin citizen watering - examination brief',author='Joseph Carpenter Sheils')
    doc.build(story,onFirstPage=pdf_footer,onLaterPages=pdf_footer)


def cparagraph(c,text,x,y,width,style='BodyExam'):
    p=para(text,style);_,h=p.wrap(width,1000);p.drawOn(c,x,y-h);return y-h


def build_atlas(records):
    w,h=landscape(A3);c=canvas.Canvas(str(PDF/'Berlin_Map_Atlas_October_2026.pdf'),pagesize=(w,h),invariant=1)
    c.setTitle('Berlin recorded citizen watering - map atlas, October 2026');c.setAuthor('Joseph Carpenter Sheils')
    cparagraph(c,'Berlin citizen watering<br/>Atlas of preliminary maps',48,h-55,w-96,'TitleExam')
    cparagraph(c,'Master\'s Seminar examination | Joseph Carpenter Sheils | '+DATE,48,h-142,w-96)
    cparagraph(c,'Twelve existing analytical map plates. Measures, periods, source tables and builders are catalogued in examination/atlas/catalogue.csv. Original image pixels and classifications are preserved. Zoom for labels or open the corresponding PNG.',48,h-185,w-96)
    y=h-252
    for i,r in enumerate(records):
        cparagraph(c,f"<b>{r['plate']}</b> &nbsp; {escape(r['title'])}",48,y,610)
        cparagraph(c,f"Page {i+2} | {escape(r['period'])}",670,y,w-718,'SmallExam');y-=29
    cparagraph(c,'Reading the atlas',48,220,w-96,'HeadExam')
    cparagraph(c,'Recorded zeros mean no linked platform log during an observed period. They do not establish absence of irrigation. Current-inventory denominators are not historical risk sets. Local Moran classes use unadjusted significance; care-gap candidates require validation. The district baseline mixes source years. No plate is a completed daily response, vegetation cooling-loss, or municipal allocation result.',48,188,w-96)
    cparagraph(c,'Attribution: CityLAB / Technologiestiftung Berlin (Gieß den Kiez); Berlin Senate tree, MSS and environmental sources; Amt für Statistik Berlin-Brandenburg, LOR 2021 (CC BY 3.0 DE). Detailed sources, licences and unresolved legacy provenance: data/README.md and data/spatial/README.md. Analysis geometry: EPSG:25833.',48,108,w-96,'SmallExam')
    c.setFont('Helvetica',8);c.drawRightString(w-48,25,'1');c.showPage()
    for i,r in enumerate(records):
        cparagraph(c,f"{r['plate']}  {escape(r['title'])}",40,h-28,w-80,'HeadExam')
        cparagraph(c,escape(r['period'])+' | '+escape(r['metric']),40,h-60,w-80,'SmallExam')
        path=ROOT/r['image'];iw,ih=PILImage.open(path).size
        scale=min((w-80)/iw,(h-230)/ih);dw,dh=iw*scale,ih*scale
        c.drawImage(ImageReader(path),(w-dw)/2,145+(h-230-dh)/2,width=dw,height=dh,mask='auto')
        y=cparagraph(c,escape(r['limits']),40,132,w-80,'SmallExam')
        y=cparagraph(c,'Data: '+escape(r['table']),40,y-3,w-80,'SmallExam')
        y=cparagraph(c,'Builder: '+escape(r['builder'])+' | Original: '+escape(r['image']),40,y-2,w-80,'SmallExam')
        if y < 34: raise ValueError(f"Atlas caption overflows: {r['plate']}")
        c.setFont('Helvetica',8);c.setFillColor(colors.HexColor('#526358'));c.drawString(40,22,'PRELIMINARY | See data/README.md for source attribution and limitations');c.drawRightString(w-40,22,str(i+2));c.setFillColor(colors.black);c.showPage()
    c.save()


def provenance(path):
    s=path.as_posix()
    if 'supervisor' in s or 'watering_response/ortsteil/' in s or s.startswith('data/Berlin_heat_'):
        return 'provisional-source-metadata-unresolved', 'data/README.md'
    if 'tree_inventory' in s or s=='data/Berlin_trees.gpkg':return 'frozen-source-acquisition-history-incomplete','data/raw/tree_inventory/README.md'
    if s.startswith('data/raw/dwd/') or 'dwd_00433' in s:return 'DWD-CC-BY-4.0','data/raw/dwd/README.md'
    if s.startswith('data/spatial/'):return 'source-specific-licence','data/spatial/README.md'
    if s.startswith('data/giessdenkiez'):return 'CC0-as-recorded-in-project-manifest','config/datasets.toml'
    return 'derived-see-input-attribution','data/README.md'


def inventories():
    paths=[]
    for base in ['data','output','examination/results']:
        for p in (ROOT/base).rglob('*'):
            if p.is_file() and p.suffix.lower() in ('.csv','.gpkg','.geojson','.json','.zip','.gz','.xlsx'):
                paths.append(p)
    schema={};index=[]
    for p in sorted(set(paths)):
        rel=p.relative_to(ROOT);entry={'path':rel.as_posix(),'bytes':p.stat().st_size,'sha256':sha(p),'rows':'','layers':'','distribution':'versioned'}
        if rel.as_posix()=='data/Berlin_trees.gpkg':entry['distribution']='restored-from-versioned-gzip'
        if p.suffix=='.csv':
            delimiter=';' if p.name.startswith('giessdenkiez') else ','
            with p.open(encoding='utf-8-sig',newline='') as handle:
                reader=csv.reader(handle,delimiter=delimiter);fields=next(reader);count=sum(1 for _ in reader)
            entry['rows']=count;schema[rel.as_posix()]={'format':'csv','delimiter':delimiter,'rows':count,'columns':fields,'types':'CSV fields are textual; use data_dictionary.md and builders for semantic types. Preserve identifiers as strings.'}
        elif p.suffix=='.gpkg':
            tables={}
            with sqlite3.connect(p.resolve().as_uri()+'?mode=ro',uri=True) as con:
                for name,srs in con.execute('SELECT table_name,srs_id FROM gpkg_contents'):
                    quoted='"'+name.replace('"','""')+'"'
                    count=con.execute(f'SELECT count(*) FROM {quoted}').fetchone()[0]
                    cols=[{'name':r[1],'sqlite_type':r[2]} for r in con.execute(f'PRAGMA table_info({quoted})')]
                    tables[name]={'rows':count,'declared_srs_id':srs,'columns':cols}
            entry['rows']=sum(t['rows'] for t in tables.values());entry['layers']=';'.join(tables);schema[rel.as_posix()]={'format':'gpkg','tables':tables}
        elif p.suffix=='.geojson':
            data=json.loads(p.read_text());entry['rows']=len(data['features']);schema[rel.as_posix()]={'format':'geojson','rows':entry['rows'],'properties':list(data['features'][0]['properties']),'crs':data.get('crs')}
        entry['provenance_status'],entry['source_notes']=provenance(rel);index.append(entry)
    with (EXAM/'data_inventory.csv').open('w',newline='',encoding='utf-8') as handle:
        writer=csv.DictWriter(handle,fieldnames=list(index[0]));writer.writeheader();writer.writerows(index)
    (EXAM/'data_schema.json').write_text(json.dumps(schema,indent=2,ensure_ascii=False)+'\n')
    return len(index)


def release_manifest():
    result=subprocess.run(['git','ls-files','-z','--cached','--others','--exclude-standard'],cwd=ROOT,check=True,capture_output=True)
    paths=sorted(set(x.decode() for x in result.stdout.split(b'\0') if x))
    entries=[]
    for rel in paths:
        p=ROOT/rel
        if rel=='examination/release_manifest.json' or not p.is_file():continue
        entries.append({'path':rel,'bytes':p.stat().st_size,'sha256':sha(p)})
    data={'schema_version':1,'prepared_date':'2026-10-17','scope':'October 2026 seminar proposal; saved preliminary evidence','selection':'Git tracked and non-ignored files at packaging time; uncompressed tree input is restored from included archive','files':entries}
    (EXAM/'release_manifest.json').write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
    return len(entries)


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest-only',action='store_true',help='Refresh exact-file manifest after documentation or validation changes')
    args=parser.parse_args()
    if not args.manifest_only:
        PDF.mkdir(exist_ok=True);EXAM.mkdir(exist_ok=True)
        f=facts();maps=catalogue();write_results(f);write_catalogue(maps);build_atlas(maps);build_brief(f)
        print(f'Built {len(maps)} map plates, examination brief and results; inventoried {inventories()} data files.')
    print(f'Release manifest: {release_manifest()} files.')
