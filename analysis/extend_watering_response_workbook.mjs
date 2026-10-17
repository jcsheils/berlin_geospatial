import fs from 'node:fs/promises';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const bundled=process.env.WATERING_ARTIFACT_NODE_MODULES || path.join(root, 'node_modules');
const require=createRequire(path.join(bundled,'__watering_loader__.cjs'));
const {FileBlob,SpreadsheetFile}=await import(pathToFileURL(require.resolve('@oai/artifact-tool')).href);
const dest=path.join(root,'outputs/watering-response-01a0ed3b');
const filename=path.join(dest,'Berlin_watering_monthly_exploration.xlsx');
const data=JSON.parse(await fs.readFile(path.join(root,'output/watering_response/ortsteil/workbook_data.json'),'utf8'));
const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(filename));
const preserved={'Berlin monthly':'A1:K69','District monthly':'A1:J817','Annual comparisons':'A1:G20','Social context':'A1:I341','Associations':'A1:H27'};
const snapshot=()=>Object.fromEntries(Object.entries(preserved).map(([name,range])=>{
  const sheet=wb.worksheets.getItem(name), cells=sheet.getRange(range);
  return [name,JSON.stringify({values:cells.values,formulas:cells.formulas,charts:sheet.charts.items.length})];
}));
const before=snapshot();
const font='Helvetica Neue';
function table(name,headers,rows,widths,id){
  const sheet=wb.worksheets.add(name), n=rows.length+1;
  const range=sheet.getRangeByIndexes(0,0,n,headers.length);
  range.values=[headers,...rows];
  range.format.font={name:font,size:11,color:'#253541'};
  range.format.rowHeight=22;
  sheet.getRangeByIndexes(0,0,1,headers.length).format={fill:'#344b5b',font:{name:font,size:11,bold:true,color:'#ffffff'},wrapText:true,rowHeight:58,verticalAlignment:'center'};
  widths.forEach((w,i)=>sheet.getRangeByIndexes(0,i,n,1).format.columnWidth=w);
  sheet.tables.add(range,true,id);
  sheet.freezePanes.freezeRows(1); sheet.showGridLines=false;
  return [sheet,n];
}
const excelDate=iso=>(Date.parse(iso.slice(0,10)+'T00:00:00Z')-Date.UTC(1899,11,30))/86400000;
const rows=data.ortsteil_panel.map(r=>[
  excelDate(r.month_date),r.ortsteil,r.district,r.recorded_watering_events,r.recorded_litres,r.recorded_watered_trees,
  r.current_boundary_area_ha,r.current_inventory_trees,null,null,null,r.lst_c,r.previous_month_lst_c,r.next_month_lst_c,
  r.source_lst_count,r.relative_source_count,r.source_rain_mm_mean_unverified,
  r.comparison_exclusion_reason || 'Provisional; source boundaries unverified',r.platform_month_status
]);
const [panel,n]=table('Ortsteil monthly',[
  'Month','Ortsteil','District (Bezirk)','Events','Litres','Distinct trees','Current area (ha)','Current inventory trees',
  'Events / ha','Litres / ha','Distinct trees / ha','Same month LST (°C)','Previous month LST (°C)','Next month LST (°C)',
  'Source LST count: undefined','Count / area maximum','Source rain: unverified','Comparison status','Platform month'
],rows,[14,27,32,13,15,17,18,22,17,17,20,22,24,23,25,24,24,65,29],'OrtsteilMonthly');
panel.getRange(`A2:A${n}`).setNumberFormat('mmm yyyy');
panel.getRange(`D2:F${n}`).setNumberFormat('#,##0');
panel.getRange(`G2:G${n}`).setNumberFormat('#,##0.0');
panel.getRange(`H2:H${n}`).setNumberFormat('#,##0');
panel.getRange('I2:K2').formulas=[['=IF(G2>0,D2/G2,"")','=IF(G2>0,E2/G2,"")','=IF(G2>0,F2/G2,"")']];
panel.getRange(`I2:K${n}`).fillDown();
panel.getRange(`I2:K${n}`).setNumberFormat('0.000');
panel.getRange(`L2:N${n}`).setNumberFormat('0.00');
panel.getRange(`O2:O${n}`).setNumberFormat('#,##0');
panel.getRange(`P2:P${n}`).setNumberFormat('0.0%');
panel.getRange(`Q2:Q${n}`).setNumberFormat('0.00');
const timing={previous_LST_current_watering:'Prior LST / current watering',same_month:'Same month',watering_next_LST:'Watering / next LST'};
const samples={'April-September_2021-2025':'Apr–Sep 2021–2025','all_months_2021-2025':'All months 2021–2025','April-September_excluding_2022':'Apr–Sep, excluding 2022'};
const metrics={recorded_watering_events_per_ha:'Events / ha',recorded_litres_per_ha:'Litres / ha',recorded_watered_trees_per_ha:'Distinct trees / ha'};
const correlations=data.ortsteil_correlations.map(r=>[samples[r.sample],timing[r.relationship],r.screen==='all_available_LST'?'All available LST':'Count ≥50% of area maximum',metrics[r.exposure],r.n_area_months,r.n_areas,r.n_watering_months,r.raw_spearman_rho,r.raw_pearson_log1p_exposure,r.area_and_yearmonth_residual_correlation]);
const [corr,cn]=table('Local LST correlations',['Sample','Temperature / watering timing','Source count screen','Watering measure','Area-months','Areas','Watering months','Raw Spearman','Raw Pearson: log(1+rate)','Pearson after area + year-month adjustment'],correlations,[30,35,37,24,15,12,20,20,27,36],'LocalLSTCorrelations');
corr.getRange(`H2:J${cn}`).setNumberFormat('0.000');
corr.getRange(`A${cn+2}`).values=[['Descriptive correlations, not causal effects. Pearson columns use log(1 + watering per hectare). Source count semantics remain undefined.']];
corr.getRange(`A${cn+3}`).values=[['Adjustment removes Ortsteil means and actual year-month means jointly on each complete-case sample; this also removes shared city-wide heat.']];
const m=data.ortsteil_audit;
const audit=[
 ['Source','Supervisor CSV supplied by user; unchanged copy retained in data/raw/supervisor.'],
 ['Source span','January 2018–December 2025; 9,312 rows, 96 distinct Ortsteil names.'],
 ['Missing LST','1,811 rows (19.45%). Missing LST coincides with count = 0. Missing temperature is never replaced with zero.'],
 ['Buckow','Two different rows for every month (192 rows, 96 ambiguous keys). Excluded from temperature comparisons; watering totals retained.'],
 ['Boundary change','Schlachtensee absent. Nikolassee and Zehlendorf excluded until source boundary vintage is verified.'],
 ['Spatial assignment','Current official 97-Ortsteil polygons. All 57,786 linked events, 2,249,502 litres and 11,127 distinct trees reconcile; 0 district disagreements.'],
 ['Provisional sample','93 candidate Ortsteile. Matching names does not establish identical source boundaries. Main window: April–September 2021–2025.'],
 ['Monthly panel','6,596 rows = 97 current Ortsteile × 68 months, May 2020–December 2025. Partial first month; recorded zero is not absence of other watering.'],
 ['Counts','LST_C_count semantics undefined. Count / area maximum is only a sensitivity screen; it is not established scene count or coverage.'],
 ['Rain','Source rain_mm_mean retained without causal/model adjustment pending source, units and aggregation metadata.'],
 ['Timing','Previous and next temperature are joined by exact calendar month. Missing months are not skipped.'],
 ['Adjustment','Both LST and log(1 + watering per hectare) projected on Ortsteil and actual year-month effects, using identical complete cases.'],
 ['Interpretation','Weak residual local associations do not establish or disprove watering cooling or a shared city-wide watering response to heat.'],
 ['Sensitivity','All months, omission of 2022, and count ≥50% of each area maximum; see all 54 results in Local LST correlations.'],
 ['Metadata needed',m.source_audit.missing_metadata.join('; ')+'.'],
 ['Boundary catalogue',m.boundary_catalogue],
 ['Boundary licence',m.boundary_licence+'; retrieved '+m.boundary_retrieved_date+'. Areas computed from EPSG:25833 polygon geometry.'],
 ['Boundary change reference',m.boundary_change_reference],
 ['Source SHA-256',m.inputs_sha256['data/raw/supervisor/berlin_ortsteile_LST_rain_2018_2025_LNDSAT.csv']],
];
const [auditSheet,an]=table('LST source audit',['Item','Definition / finding'],audit,[30,118],'LSTSourceAudit');
auditSheet.getRange(`A2:B${an}`).format.rowHeight=52;
auditSheet.getRange(`B2:B${an}`).format.wrapText=true;
auditSheet.getRange('A16:B16').format.rowHeight=72;
auditSheet.getRange('A19:B19').format.rowHeight=72;
const readme=wb.worksheets.getItem('Read me');
readme.getRange('B5').values=[['12 Bezirke and 542 LORs; new Ortsteil panel covers 97 current areas. Local LST comparisons use 93 provisionally aligned Ortsteile; see LST source audit.']];
readme.getRange('B6').values=[['DWD Berlin-Tempelhof station 00433 supplies air-temperature context. Supplied monthly Landsat LST is a separate surface-temperature outcome; metadata remain unverified.']];
readme.getRange('B16').values=[['Supervisor CSV received and audited. Extraction script, original boundaries, cloud filtering, count definition and rain provenance remain needed. Local correlations are provisional, with no causal cooling estimate.']];
readme.getRange('A16:B16').format.rowHeight=66;
if(JSON.stringify(before)!==JSON.stringify(snapshot())) throw new Error('Existing analytical sheets changed');
for(let i=0;i<data.ortsteil_panel.length;i++){
  const expected=data.ortsteil_panel[i], actual=panel.getRange(`I${i+2}:K${i+2}`).values[0];
  ['recorded_watering_events_per_ha','recorded_litres_per_ha','recorded_watered_trees_per_ha'].forEach((key,j)=>{
    if(Math.abs(actual[j]-expected[key])>1e-7) throw new Error(`Rate mismatch row ${i+2} ${key}`);
  });
}
console.log('All 19,788 new rate formulas match analytical exports; five existing analytical sheets preserved.');
console.log((await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:20},summary:'Formula error scan',maxChars:1800})).ndjson);
for(const [name,range] of [['Read me','A13:B16'],['Ortsteil monthly','A1:K7'],['Ortsteil monthly','L1:S7'],['Local LST correlations','A1:J10'],['LST source audit','A1:B16']]){
  const preview=await wb.render({sheetName:name,range,scale:1.2,format:'png'});
  await fs.writeFile(path.join(dest,`preview-lst-${name.replaceAll(' ','-')}-${range.split(':')[0]}.png`),new Uint8Array(await preview.arrayBuffer()));
}
await fs.copyFile(filename,path.join(dest,'Berlin_watering_monthly_exploration_before_LST.xlsx'));
await (await SpreadsheetFile.exportXlsx(wb)).save(filename);
await fs.writeFile(path.join(dest,'lst_workbook_verification.json'),JSON.stringify({existingAnalyticalSheetsUnchanged:true,newFormulaCellsVerified:19788,ortsteilMonthRows:rows.length,correlationRows:correlations.length,originalSheetSnapshots:before},null,2));
console.log('Updated workbook exported with nine sheets.');
