import fs from 'node:fs/promises';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';

// Use the bundled dependency location returned by load_workspace_dependencies.
const bundleNodeModules=process.env.WATERING_ARTIFACT_NODE_MODULES || path.join(root, 'node_modules');
const bundledRequire=createRequire(path.join(bundleNodeModules,'__watering_loader__.cjs'));
const { Workbook, SpreadsheetFile }=await import(pathToFileURL(bundledRequire.resolve('@oai/artifact-tool')).href);

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const dest = path.join(root, 'outputs/watering-response-01a0ed3b');
const data = JSON.parse(await fs.readFile(path.join(root,'output/watering_response/workbook_data.json'),'utf8'));
await fs.mkdir(dest,{recursive:true});
const wb=Workbook.create();
const names=['Read me','Berlin monthly','District monthly','Annual comparisons','Social context','Associations'];
const sheets=Object.fromEntries(names.map(name=>[name,wb.worksheets.add(name)]));
const font='Helvetica Neue';
const label={recorded_watering_events:'Events',recorded_litres:'Litres',recorded_watered_trees:'Distinct trees'};

// Sheet names/table names are explicit to avoid relying on inferred objects.
function table(sheet,headers,rows,widths,tableName){
  const count=rows.length+1, cols=headers.length;
  const range=sheet.getRangeByIndexes(0,0,count,cols);
  range.values=[headers,...rows];
  range.format.font={name:font,size:11,color:'#253541'};
  range.format.rowHeight=22;
  const head=sheet.getRangeByIndexes(0,0,1,cols);
  head.format={fill:'#344b5b',font:{name:font,size:11,bold:true,color:'#ffffff'},wrapText:true,rowHeight:44,verticalAlignment:'center'};
  widths.forEach((width,i)=>sheet.getRangeByIndexes(0,i,count,1).format.columnWidth=width);
  sheet.freezePanes.freezeRows(1);
  sheet.showGridLines=false;
  sheet.tables.add(range,true,tableName);
  return count;
}
const notes=[
 ['Purpose','Agreed exploratory stage: monthly recorded care, weather alignment, social context and cooling feasibility.'],
 ['Coverage','May 2020–December 2025. May 2020 is partial; January–April 2020 are unavailable.'],
 ['Watering sample','57,786 assigned platform events, 2,249,502 litres and 11,127 distinct trees across the observed period.'],
 ['Geography','12 Bezirke and 542 LOR Planungsräume. The separate LOR CSV contains 36,856 neighbourhood-months. Ortsteile require a verified mapping.'],
 ['Weather','DWD Berlin-Tempelhof station 00433: shared temporal context for Berlin. Air temperature is not Landsat LST or district-specific temperature.'],
 ['Missing rain','June and October 2023 are missing precipitation days. Monthly rainfall is blank unless all days are valid. No zero substitution.'],
 ['Models','OLS of log(1 + activity), separate same-month and previous-month specifications, jointly adjusted for temperature, rain, calendar month and year.'],
 ['Uncertainty','Approximate 95% HAC(3) intervals preserve actual calendar gaps; not adjusted for multiple comparisons. Coefficients are not exact percentages.'],
 ['Main result','Same-month temperature aligns positively with events and distinct trees after broad seasonal adjustment. Previous-month estimates are much less precise.'],
 ['2022 comparison','2022 has the most annual events and litres, but June–September 2020 has more events and distinct trees than June–September 2022.'],
 ['Social context','MSS 2025 classification refers to end-2024 neighbourhood conditions. It is not historical income or individual volunteer status.'],
 ['Distinct trees','Computed from tree IDs within each period. Do not add monthly distinct-tree counts to estimate annual distinct counts.'],
 ['Denominators','Rates use current inventory trees. These are not historical irrigation-coverage rates.'],
 ['Recording','No platform log does not imply no municipal, private or unlogged watering. 688 unassigned events are excluded from this geographical panel.'],
 ['Pending input','Supervisor Ortsteil LST/rain CSV received; extraction metadata and original boundaries remain unverified. Run the Ortsteil workbook extension after this base builder. No causal cooling or optimal allocation estimate is supplied.'],
 ['DWD source',data.metadata.source_urls.dwd_archive],
 ['DWD documentation',data.metadata.source_urls.dwd_description],
 ['DWD quality','Climate quality code 9 throughout: not all parameters corrected. Original archive metadata retained. CC BY 4.0. Downloaded 29 September 2026.'],
 ['Social source','https://gdi.berlin.de/services/wfs/mss_2025'],
 ['Watering source','Gieß den Kiez source snapshot and the project’s validated tree-day and LOR-month products.'],
 ['Editable calculations','Rate columns are formulas. Statistical model results are fixed analytical outputs and must be rerun if inputs change.'],
];
const readme=sheets['Read me'];
table(readme,['Item','Definition / finding'],notes,[25,112],'ReadMeNotes');
readme.getRange(`B2:B${notes.length+1}`).format.wrapText=true;
readme.getRange(`A2:B${notes.length+1}`).format.rowHeight=44;
readme.getRange('B17:B18').format.rowHeight=65;

const city=data.berlin_month_weather_watering;
const cityRows=city.map(r=>[new Date(r.month),r.recorded_watering_events,r.recorded_litres,r.recorded_watered_trees,r.air_temperature_mean_c,r.rainfall_mm,r.previous_month_air_temperature_mean_c,r.previous_month_rainfall_mm,r.valid_rainfall_days,r.expected_days,r.platform_month_status]);
const citySheet=sheets['Berlin monthly'];
const cityN=table(citySheet,['Month','Events','Litres','Distinct trees','Mean air temp (°C)','Rainfall (mm)','Previous month temp (°C)','Previous month rain (mm)','Valid rain days','Days in month','Platform month'],cityRows,[14,13,15,16,18,16,22,23,16,16,28],'BerlinMonthly');
citySheet.getRange(`A2:A${cityN}`).setNumberFormat('mmm yyyy');
citySheet.getRange(`B2:D${cityN}`).setNumberFormat('#,##0');
citySheet.getRange(`E2:H${cityN}`).setNumberFormat('0.0');

const district=data.district_month_watering;
const districtRows=district.map(r=>[new Date(r.month),r.district,r.recorded_watering_events,r.recorded_litres,r.recorded_watered_trees,r.current_inventory_trees,null,null,null,r.platform_month_status]);
const distSheet=sheets['District monthly'];
const distN=table(distSheet,['Month','District (Bezirk)','Events','Litres','Distinct trees','Current inventory trees','Events / 1,000 trees','Litres / inventory tree','Monthly reach (%)','Platform month'],districtRows,[14,32,13,15,16,22,21,22,20,28],'DistrictMonthly');
distSheet.getRange(`A2:A${distN}`).setNumberFormat('mmm yyyy');
distSheet.getRange(`C2:F${distN}`).setNumberFormat('#,##0');
distSheet.getRange('G2:I2').formulas=[['=IF(F2>0,1000*C2/F2,"")','=IF(F2>0,D2/F2,"")','=IF(F2>0,100*E2/F2,"")']];
distSheet.getRange(`G2:I${distN}`).fillDown();
distSheet.getRange(`G2:I${distN}`).setNumberFormat('0.000');

const ann=sheets['Annual comparisons'];
const annRows=data.berlin_year_watering.map(r=>[r.year,r.recorded_watering_events,r.recorded_litres,r.recorded_watered_trees,r.period]);
table(ann,['Year','Events','Litres','Distinct trees','Observed period'],annRows,[14,16,18,18,42],'AnnualCounts');
ann.getRange('B2:D7').setNumberFormat('#,##0');
const seasonRows=data.berlin_june_september_comparison.map(r=>[r.year,r.recorded_watering_events,r.recorded_litres,r.recorded_watered_trees,r.mean_air_temperature_c,r.rainfall_mm,r.hot_days_ge_30c]);
ann.getRange('A10').values=[['June–September: same observed window in all six years']];
ann.getRange('A10').format.font={name:font,size:12,bold:true};
ann.getRange('A12:G18').values=[['Year','Events','Litres','Distinct trees','Mean air temp (°C)','Rainfall (mm)','Days ≥30 °C'],...seasonRows];
ann.getRange('A12:G18').format.font={name:font,size:11};
ann.getRange('A12:G12').format={fill:'#344b5b',font:{name:font,size:11,bold:true,color:'#ffffff'},wrapText:true,rowHeight:44};
ann.getRange('F12:G18').format.columnWidth=19;
ann.getRange('B13:D18').setNumberFormat('#,##0');
ann.getRange('E13:F18').setNumberFormat('0.0');
ann.getRange('G13:G18').setNumberFormat('0');
ann.getRange('A20').values=[['Blank 2023 rainfall means incomplete observations. Annual distinct trees are counted from IDs.']];
ann.getRange('A20').format.font={name:font,size:10,color:'#617079'};
ann.tables.add('A12:G18',true,'ComparableSeasons');
const chart=ann.charts.add('line',[ann.getRange('A12:A18'),ann.getRange('B12:B18')]);
chart.setPosition('A23','H39');
chart.title='Recorded events, June–September';
chart.titleTextStyle.typeface=font;
chart.titleTextStyle.fontSize=14;
chart.hasLegend=false;
chart.xAxis={axisType:'textAxis',textStyle:{typeface:font,fontSize:11}};
chart.yAxis={numberFormatCode:'#,##0',numberFormatSourceLinked:false,textStyle:{typeface:font,fontSize:11}};
chart.series.items[0].fill='#bb622c';

const socialRows=data.social_status_month_watering.map(r=>[new Date(r.month),r.social_status_2024,r.recorded_watering_events,r.recorded_litres,r.recorded_watered_trees,r.current_inventory_trees,null,null,null]);
const social=sheets['Social context'];
const socialN=table(social,['Month','Social status (end-2024)','Events','Litres','Distinct trees','Current inventory trees','Events / 1,000 trees','Litres / inventory tree','Monthly reach (%)'],socialRows,[14,29,13,15,16,22,21,22,20],'SocialMonthly');
social.getRange(`A2:A${socialN}`).setNumberFormat('mmm yyyy');
social.getRange(`C2:F${socialN}`).setNumberFormat('#,##0');
social.getRange('G2:I2').formulas=[['=IF(F2>0,1000*C2/F2,"")','=IF(F2>0,D2/F2,"")','=IF(F2>0,100*E2/F2,"")']];
social.getRange(`G2:I${socialN}`).fillDown();
social.getRange(`G2:I${socialN}`).setNumberFormat('0.000');

const modelRows=data.monthly_adjusted_associations.map(r=>[r.sample,r.timing.replaceAll('_',' '),label[r.outcome],r.term==='temperature_per_5c'?'Temperature / 5 °C':'Rainfall / 10 mm',r.n_months,r.coefficient_log1p,r.approx_95_low,r.approx_95_high]);
const assoc=sheets['Associations'];
const assocN=table(assoc,['Sample','Weather timing','Outcome','Predictor','Months','Slope: log(1+y)','Approx. 95% low','Approx. 95% high'],modelRows,[22,22,20,23,12,20,20,20],'ModelAssociations');
assoc.getRange(`F2:H${assocN}`).setNumberFormat('0.000');
assoc.getRange(`A${assocN+2}`).values=[['All models include calendar-month and year indicators; HAC(3) intervals are exploratory and not multiplicity-adjusted.']];
assoc.getRange(`A${assocN+2}`).format.font={name:font,size:10,color:'#617079'};

// Compact numerical verification against independently exported analytic rates.
const expected=district[0].recorded_events_per_1000_current_inventory_trees;
const calculated=distSheet.getRange('G2').values[0][0];
if(Math.abs(calculated-expected)>1e-8) throw new Error('District rate formula mismatch');
console.log((await wb.inspect({kind:'table',range:'District monthly!A1:I4',include:'values,formulas',tableMaxRows:4,tableMaxCols:9,maxChars:2500})).ndjson);
const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:30},summary:'Final formula error scan',maxChars:1800});
console.log(errors.ndjson);
for(const name of names){
  const range=name==='Read me'?'A1:B9':name==='Annual comparisons'?'A10:H39':name==='Associations'?'A1:H10':name==='Berlin monthly'?'A1:K9':name==='District monthly'?'A1:J9':'A1:I9';
  const preview=await wb.render({sheetName:name,range,scale:1.3,format:'png'});
  await fs.writeFile(path.join(dest,`preview-${name.replaceAll(' ','-')}.png`),new Uint8Array(await preview.arrayBuffer()));
}
await (await SpreadsheetFile.exportXlsx(wb)).save(path.join(dest,'Berlin_watering_monthly_exploration.xlsx'));
console.log('Workbook exported.');
