# Frozen Berlin tree inventory

`Berlin_trees.gpkg.gz` is a lossless compressed copy of the exact inventory used by the existing analyses. It restores the 335 MB GeoPackage without downloading a changing live dataset. The archive is about 61 MB (58.5 MiB), below GitHub's 100 MiB single-file limit; Git may display a large-file warning.

```bash
python tools/restore_tree_inventory.py
```

The command verifies SHA-256 before and after decompression, writes atomically, and refuses to replace a different existing inventory. The exact sizes and hashes are in [snapshot.json](snapshot.json). The original uncompressed path remains ignored by Git to avoid duplicating the archive.

- Source: [Berlin Open Data — Baumbestand Berlin](https://daten.berlin.de/datensaetze/baumbestand-berlin-wfs-48ad3a23).
- Provider: Senatsverwaltung für Mobilität, Verkehr, Klimaschutz und Umwelt Berlin.
- Source licence: Datenlizenz Deutschland – Zero – Version 2.0, checked 17 October 2026.
- Official service: <https://gdi.berlin.de/services/wfs/baumbestand>.
- Existing snapshot: 962,545 rows; 956,347 distinct non-null `pitid` values; layer `Berlin_trees`.
- Provenance limitation: the original acquisition date and export procedure are not recorded. The stored `source_layer` values identify `baumbestand:strassenbaeume` and `baumbestand:anlagenbaeume`. This archive preserves the existing project input; it does not claim to be a fresh official export.

**CRS warning:** the file declares EPSG:4326 but stores metre coordinates consistent with EPSG:25833. The analysis explicitly validates the coordinate range and overrides the CRS metadata before spatial joins. The archived source bytes are unchanged.

The source includes street trees and only part of the green-space tree population. A current catalogue is not a historical monthly population or complete canopy inventory.
