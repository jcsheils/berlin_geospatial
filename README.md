# Berlin Geospatial Analysis

Spatial analysis for a master's thesis on urban heat, Berlin's tree inventory,
and citizen watering activity.

The repository currently contains:

- exploratory analysis of watering activity, tree coverage, and district heat;
- LOR Planungsraum-level watering reach and intensity;
- global and local Moran statistics for spatial clustering;
- static figures, analysis tables, an interactive map, and enriched polygons;
- reproducible notebook-builder scripts.

## Main outputs

- `output/jupyter-notebook/berlin-urban-heat-exploration.ipynb`
- `output/jupyter-notebook/berlin-lor-spatial-watering.ipynb`
- `output/spatial/maps/lor_watering_interactive.html`
- `output/spatial/lor_watering_metrics_2020_2025.gpkg`

## Setup

Create an environment with Python 3.12, then install the spatial dependencies:

```bash
python -m pip install -r requirements-spatial.txt
```

Build and execute the notebooks:

```bash
python analysis/build_exploratory_notebook.py
jupyter nbconvert --to notebook --execute \
  output/jupyter-notebook/berlin-urban-heat-exploration.ipynb \
  --inplace

python analysis/build_spatial_notebook.py
jupyter nbconvert --to notebook --execute \
  output/jupyter-notebook/berlin-lor-spatial-watering.ipynb \
  --inplace
```

## Data

The official Berlin LOR Planungsraum polygons and smaller analysis datasets are
versioned in `data/`.

`data/Berlin_trees.gpkg` is intentionally excluded because it is approximately
320 MB and exceeds GitHub's file-size limit. The notebook expects that file at
that exact path. The GeoPackage's coordinates are EPSG:25833, although its
source metadata incorrectly declares EPSG:4326; the spatial notebook validates
and overrides that CRS before joining trees to LOR polygons.

The LOR boundary source and license are documented in
`data/spatial/README.md`.

## Current spatial result

For complete years 2020-2025, citizen watering reach is positively spatially
clustered across Berlin's LOR Planungsräume. The executed notebook reports
Moran's I and permutation-based local cluster classifications.

These results are descriptive. They do not estimate a causal temperature effect
of watering.
