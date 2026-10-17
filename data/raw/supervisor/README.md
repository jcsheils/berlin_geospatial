# Supplied monthly Ortsteil temperature and rainfall

The user supplied `berlin_ortsteile_LST_rain_2018_2025_LNDSAT.csv` on
29 September 2026 from their Downloads folder. This is an unchanged local
copy; no extraction script, product metadata or licence statement accompanied it.

SHA-256: `6a61abf0bbd46231a7db7c5c334e69d6fce4d3c7b5b32b345f0de76baddb2756`.

The CSV contains 9,312 rows over January 2018–December 2025, with columns
`ortsteil`, `bezirk`, `year`, `month`, `LST_C_mean`, `LST_C_count`, and
`rain_mm_mean`. There are 96 distinct names but 97 rows per month: Buckow
has two different rows per month without component identifiers. These must
not be silently averaged, selected, or joined to duplicated watering totals.
There are 1,811 missing temperature values, all accompanied by count zero.

Schlachtensee is absent, while the current official geography includes it
following its creation from parts of Nikolassee and Zehlendorf in December
2020. Buckow, Nikolassee and Zehlendorf temperature outcomes are excluded
until resolved; current Schlachtensee has no source outcome. The remaining
93 areas are only provisionally aligned by names and district.

Pending metadata: original boundary file and date; Landsat sensor/product;
acquisition dates and scene counts; cloud/shadow filtering; monthly composite
method; definition of `LST_C_count`; rainfall source, units and aggregation.
Positive counts are not assumed to represent independent scenes or valid
coverage. Source rainfall is retained as unverified and is not used as a
model adjustment.

Run `pipelines/07_build_ortsteil_lst.py` for the standalone audit and panel,
or `analysis/build_watering_response_report.py` for the combined report.
Audited rows, exclusions, geographical crosswalks, monthly counts, descriptive
correlations and input/output hashes are under
`output/watering_response/ortsteil/`.
