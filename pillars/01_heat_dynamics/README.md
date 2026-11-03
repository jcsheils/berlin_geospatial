> **October 2026 scope update:** historical design context is retained below. The active design is the October proposal: Part II civic heat response (core), Part I vegetation cooling loss (supporting), and Part III allocation (exploratory). See `docs/analysis_plan.md` and `examination/README.md`. Existing descriptive products remain valid within their stated limits.

# Part I Support — Urban Heat, Vegetation, and Drought

**Readiness: preliminary-only**

## Role in the current thesis

This retained folder supplies the heat/LST side of Part I. It is not a separate
daily-heat or mortality chapter.

## Primary question

How do Sentinel-2 vegetation greenness, built density, imperviousness, water
proximity, acquisition conditions, and temporal drought jointly relate to
summer Landsat LST across Berlin?

## Current evidence

The repository contains a mixed-administrative borough snapshot for 2015,
2020, and 2025. It is preliminary context only and is not the proposed
valid-overpass analytical panel.

## Required next products

- valid summer Landsat observations for descriptive mapping in 2013–2024;
- the main Sentinel-linked product-grid-cell/overpass panel for 2017–2024;
- dated built-form, imperviousness, and waterbody controls;
- ERA5 primary temporal controls: 2 m temperature, dew point/derived humidity,
  precipitation, 10 m wind, surface pressure, and 7-/14-/30-day summaries;
- ESA CCI and ERA5 drought sensitivities, plus DWD station-observed temperature,
  precipitation, humidity, wind, and sunshine for sensitivity/context only;
- clear-sky selection and spatially blocked validation audits.

If the reproducible Landsat/Sentinel panel is not analysis-ready by the end of
Month 2, freeze Part I at descriptive LST/greenness outputs and a data audit,
and activate the Environmental Justice Atlas thermal fallback for Part III.

## Claim boundary

Landsat LST is not air temperature or felt heat. The 30 m product grid derives
from coarser native thermal sampling, and clear-sky acquisitions do not
represent every summer day. No nocturnal-retention claim is planned from
daytime Landsat observations.
