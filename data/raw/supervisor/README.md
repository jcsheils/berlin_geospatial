# Monthly Ortsteil surface temperature and rainfall

`berlin_ortsteile_LST_rain_2018_2025_LNDSAT.csv` reached the project on 29 September 2026 as a local file. It is stored unchanged. No extraction script, product metadata or licence came with it.

SHA-256: `6a61abf0bbd46231a7db7c5c334e69d6fce4d3c7b5b32b345f0de76baddb2756`

## Contents

9,312 rows for January 2018–December 2025, with columns `ortsteil`, `bezirk`, `year`, `month`, `LST_C_mean`, `LST_C_count` and `rain_mm_mean`.

- **Buckow:** 96 distinct names but 97 rows per month, because Buckow has two different rows per month with no component ID. Never average them, pick one, or join them to duplicated watering totals.
- **Missing values:** 1,811 temperature values, each with count zero.
- **Schlachtensee:** absent, although the official geography has included it since it was formed from parts of Nikolassee and Zehlendorf in December 2020.

Buckow, Nikolassee and Zehlendorf stay out of temperature comparisons until resolved, and Schlachtensee has no source values. The other 93 areas align only provisionally, by name and district.

## Missing metadata

The original boundary file and its date; Landsat sensor and product; acquisition dates and scene counts; cloud and shadow filtering; compositing method; the meaning of `LST_C_count`; rainfall source, units and aggregation. Positive counts are not assumed to be independent scenes or valid coverage. Source rainfall stays flagged as unverified and is not a model adjustment.

## Use

Run `pipelines/07_build_ortsteil_lst.py` for the audit and panel alone, or `analysis/build_watering_response_report.py` for the combined report. Audits, exclusions, crosswalks, monthly counts, correlations and hashes go to `output/watering_response/ortsteil/`.
