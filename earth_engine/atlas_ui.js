/* Berlin citizen tree-watering atlas. Native Google Earth Engine UI.
 * DATA is injected by build_demo.py; no private EE assets required.
 */
var regions = ee.FeatureCollection(DATA.features);
var region = regions.geometry();
var map = ui.Map();
map.setCenter(13.405, 52.52, 10);
map.setOptions('ROADMAP');
map.style().set('cursor', 'crosshair');
var panel = ui.Panel({style: {width: '390px', padding: '16px'}});
ui.root.clear();
ui.root.add(panel);
ui.root.add(map);
panel.add(ui.Label('BERLIN | Recorded care atlas', {fontSize: '23px', fontWeight: 'bold', color: '#164c45'}));
panel.add(ui.Label('Explore logged citizen watering, neighbourhood context and satellite surface temperature. Preliminary descriptive evidence.'));
panel.add(ui.Label('Logs ≠ all irrigation. Current tree stock ≠ historical stock. Low logged care ≠ unmet need.', {color: '#9c4326'}));
var month = ui.Select({items: DATA.months, value: '2025-07', style: {stretch: 'horizontal'}});
var choices = ['Monthly events / 1,000 inventory trees', 'Monthly recorded litres', 'Monthly recorded events', 'Pooled recorded reach (%)', 'Social status (end-2024)', 'Landsat monthly surface temperature', 'Landsat valid scene count'];
var metric = ui.Select({items: choices, value: choices[0], style: {stretch: 'horizontal'}});
panel.add(ui.Label('Month (May 2020 is partial)')).add(month);
panel.add(ui.Label('Map layer')).add(metric);
var legend = ui.Panel();
var note = ui.Label();
var detail = ui.Panel();
panel.add(legend).add(note).add(detail);
panel.add(ui.Label('LOR boundaries: Amt für Statistik Berlin-Brandenburg, CC BY 3.0 DE; display simplified by 20 m. Watering: Giess den Kiez snapshot. Social/environmental context: MSS / environmental justice 2023–24. Satellite: USGS Landsat 8/9.'));
var selected = null;
var requestId = 0;
var palette = ['#f7fcf0','#ccebc5','#7bccc4','#2b8cbe','#084081'];
function getValue(f, index, mode) {
  var p = f.properties, row = DATA.series[p.plr_id][index];
  if (mode === choices[0]) return p.inventory_trees > 0 ? 1000 * row[0] / p.inventory_trees : null;
  if (mode === choices[1]) return row[1];
  if (mode === choices[2]) return row[0];
  if (mode === choices[3]) return p.watering_reach_pct;
  return p.social_status_score;
}
function showDetails() {
  detail.clear();
  if (!selected) { detail.add(ui.Label('Click a neighbourhood to inspect its history.')); return; }
  var f = DATA.features.filter(function(x) { return x.properties.plr_id === selected; })[0];
  var p = f.properties, index = DATA.months.indexOf(month.getValue());
  var row = DATA.series[selected][index];
  detail.add(ui.Label(p.plr_name + ' · ' + p.District, {fontWeight: 'bold', fontSize: '17px'}));
  detail.add(ui.Label(month.getValue() + ': ' + row[0] + ' logged events · ' + row[1] + ' L'));
  detail.add(ui.Label('Current inventory: ' + p.inventory_trees + ' trees. Thermal burden: ' + (p.thermal_burden || 'missing') + '; green provision: ' + (p.green_provision || 'missing') + '.'));
  var rows = [['Month', 'Logged events']];
  DATA.months.forEach(function(m, i) { rows.push([m, DATA.series[selected][i][0]]); });
  detail.add(ui.Chart(rows).setChartType('LineChart').setOptions({title: 'Monthly logged events · May 2020–Dec 2025', legend: {position: 'none'}, height: 210, colors: ['#16796f'], hAxis: {showTextEvery: 12}, vAxis: {minValue: 0}}));
  detail.add(ui.Label('Zeros assume platform availability. May 2020 begins on 18 May. No neighbourhood response slopes have been estimated.'));
}
function landsat(start, end) {
  var raw = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
    .merge(ee.ImageCollection('LANDSAT/LC09/C02/T1_L2'))
    .filterBounds(region).filterDate(start, end)
    .filter(ee.Filter.eq('PROCESSING_LEVEL', 'L2SP'));
  return raw.map(function(img) {
    var valid = img.select('QA_PIXEL').bitwiseAnd(63).eq(0)
      .and(img.select('QA_RADSAT').eq(0));
    return img.select('ST_B10').multiply(0.00341802).add(149).subtract(273.15)
      .rename('lst').updateMask(valid);
  });
}
function draw() {
  map.layers().reset([]);
  legend.clear();
  var index = DATA.months.indexOf(month.getValue()), mode = metric.getValue();
  if (mode.indexOf('Landsat') === 0) {
    var start = ee.Date(month.getValue() + '-01');
    var col = landsat(start, start.advance(1, 'month'));
    // A fully masked fallback keeps empty collections safe without adding observations.
    col = col.merge(ee.ImageCollection([ee.Image.constant(0).rename('lst').updateMask(ee.Image.constant(0))]));
    var count = col.count().unmask(0).clip(region);
    var isCount = mode === choices[6];
    map.addLayer(isCount ? count : col.median().clip(region), {min: isCount ? 0 : 15, max: isCount ? 10 : 45, palette: isCount ? palette : ['313695','74add1','ffffbf','f46d43','a50026']}, mode);
    legend.add(ui.Label(isCount ? 'Valid scene count: 0 → 10+ (overlapping scenes may share a date)' : 'Monthly median clear-sky LST: 15 → 45+ °C'));
    note.setValue('Satellite overpass surface temperature, not air temperature or a watering effect. Missing pixels are not zero heat. Clear-sky sampling and emissivity gaps affect coverage.');
  } else {
    var limits = mode === choices[0] ? [0,1,5,20] : mode === choices[1] ? [0,100,500,2000] : mode === choices[2] ? [0,5,20,100] : [0,1,5,10];
    var categorical = mode === choices[4];
    var styled = DATA.features.map(function(f) {
      var v = getValue(f, index, mode), bin = 0;
      limits.forEach(function(t) { if (v > t) bin++; });
      if (categorical) bin = v - 1;
      return ee.Feature(f).set('style', {color: 'ffffff', width: 0.4, fillColor: v === null ? '999999' : palette[bin].replace('#','')});
    });
    map.addLayer(ee.FeatureCollection(styled).style({styleProperty: 'style'}), {}, mode);
    var labels = categorical ? ['1 high','2 medium','3 low','4 very low'] : ['0','>0–' + limits[1], '>' + limits[1] + '–' + limits[2], '>' + limits[2] + '–' + limits[3], '>' + limits[3]];
    labels.forEach(function(label, i) { legend.add(ui.Label('■ ' + label, {color: palette[i], backgroundColor: '#eeeeee'})); });
    legend.add(ui.Label('Grey: missing / no denominator. Fixed classes across months.'));
    note.setValue(categorical ? 'Static MSS end-2024 context; month selector does not change this layer.' : mode === choices[3] ? 'Distinct trees logged at least once / current inventory, May 2020–Dec 2025. Month selector does not change pooled reach.' : 'All linked tree types. Monthly platform activity; current inventory denominators.');
  }
  map.addLayer(regions.style({color: '555555', fillColor: '00000000', width: 0.5}), {}, 'Neighbourhood boundaries');
  if (selected) map.addLayer(regions.filter(ee.Filter.eq('plr_id', selected)).style({color: 'ff00ff', fillColor: '00000000', width: 3}), {}, 'Selected neighbourhood');
  showDetails();
}
map.onClick(function(coords) {
  var ticket = ++requestId;
  regions.filterBounds(ee.Geometry.Point([coords.lon, coords.lat])).aggregate_array('plr_id').evaluate(function(ids, error) {
    if (ticket !== requestId) return;
    if (error) { detail.clear(); detail.add(ui.Label('Selection failed; retry. ' + error)); return; }
    selected = ids && ids.length ? ids[0] : null;
    draw();
  });
});
month.onChange(draw);
metric.onChange(draw);
panel.add(ui.Label('RQ1 | Daily citywide exploration', {fontWeight: 'bold', fontSize: '17px'}));
var year = ui.Select({items: ['2020','2021','2022','2023','2024','2025'], value: '2025'});
var dailyPanel = ui.Panel();
panel.add(year).add(dailyPanel);
function dailyChart() {
  dailyPanel.clear();
  var rows = [['Date', 'Logged events', 'Max air temperature (°C)']];
  DATA.daily.filter(function(r) { return r.date.slice(0,4) === year.getValue(); }).forEach(function(r) {
    rows.push([r.date, r.events, r.air_temperature_max_c]);
  });
  dailyPanel.add(ui.Chart(rows).setChartType('LineChart').setOptions({title: 'April–September · DWD station 00433', height: 230, series: {0: {targetAxisIndex: 0, color: '#16796f'}, 1: {targetAxisIndex: 1, color: '#d95f0e'}}, vAxes: {0: {title: 'Events'}, 1: {title: 'Air °C'}}, hAxis: {showTextEvery: 45}, legend: {position: 'bottom'}}));
  dailyPanel.add(ui.Label('Descriptive co-variation, not the adjusted model or a causal effect. Separate axes can visually exaggerate agreement. 2020 starts 18 May.'));
}
year.onChange(dailyChart);
dailyChart();
draw();
