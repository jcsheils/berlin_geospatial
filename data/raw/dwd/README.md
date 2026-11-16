# DWD Berlin-Tempelhof daily weather

- **Station:** Berlin-Tempelhof, 00433
- **File:** `tageswerte_KL_00433_19480101_20251231_hist.zip`
- **Source:** https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/daily/kl/historical/tageswerte_KL_00433_19480101_20251231_hist.zip
- **Documentation:** https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/daily/kl/DESCRIPTION_obsgermany-climate-daily-kl_en.pdf
- **Provider:** Deutscher Wetterdienst, Climate Data Center
- **Licence:** CC BY 4.0 (dataset description v24.3)
- **Retrieved:** 29 September 2026, unchanged, with station, instrument, quality and missing-data metadata. `output/watering_response/metadata.json` records its SHA-256.

To reacquire, download the archive from the source URL into this folder. If DWD revises it, compare checksums and rerun the measurement audit.

## Variables

The extraction covers 2020–2025. TMK is mean air temperature (°C), TXK maximum air temperature (°C) and RSK daily precipitation (mm). Code −999 becomes missing, not zero, and monthly values require every daily observation. Ten precipitation days are missing, in June and October 2023. Quality code QN_4 is 9 throughout, meaning DWD has not corrected every parameter. Station position and instrument history are in the archive's metadata.

The station gives citywide temporal context only. It is not district weather, Landsat LST, a drought map or a cooling outcome.
