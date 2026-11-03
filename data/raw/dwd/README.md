# DWD Berlin-Tempelhof daily weather

- Station: Berlin-Tempelhof, 00433.
- File: `tageswerte_KL_00433_19480101_20251231_hist.zip`.
- Source: https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/daily/kl/historical/tageswerte_KL_00433_19480101_20251231_hist.zip
- Documentation: https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/daily/kl/DESCRIPTION_obsgermany-climate-daily-kl_en.pdf
- Provider: Deutscher Wetterdienst, Climate Data Center.
- Licence: CC BY 4.0, as stated in the v24.3 dataset description.
- Retrieved: 29 September 2026. The unchanged archive includes station,
  instrument, quality and missing-data metadata. Its SHA-256 is recorded in
  `output/watering_response/metadata.json` alongside source/product checksums.

Reacquire the pinned archive from the source URL above, placing it in this
directory. If DWD changes the archive in a later revision, compare checksums
and rerun the measurement audit rather than assuming identical observations.

The exploratory extraction covers 2020–2025. TMK is mean air temperature
(degrees Celsius), TXK is maximum air temperature (degrees Celsius), and RSK
is daily precipitation (millimetres). Missing code -999 becomes missing, not
zero. Monthly values require all expected daily observations for that variable.

There are ten missing precipitation days, in June and October 2023. Climate
quality code QN_4 is 9 throughout this extraction, meaning not all parameters
are corrected under the documented quality-code scheme. Use the archive's
station metadata for position and instrument history.

This single station supplies temporal context for the exploratory watering
response question. It is not district-specific weather, Landsat LST, a
neighbourhood drought map or a measured cooling outcome of local watering.
