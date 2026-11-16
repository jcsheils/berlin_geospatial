# Berlin tree inventory snapshot

`Berlin_trees.gpkg.gz` is a lossless compressed copy of the exact inventory the analyses use. It restores the 335 MB GeoPackage without downloading the live dataset, which changes over time. At about 61 MB (58.5 MiB) it stays under GitHub's 100 MiB file limit, though Git may warn about its size.

```bash
python tools/restore_tree_inventory.py
```

The script checks SHA-256 before and after decompression, writes atomically and refuses to overwrite a different inventory. [snapshot.json](snapshot.json) records sizes and hashes. Git ignores the uncompressed file to avoid storing it twice.

- **Source:** [Berlin Open Data, Baumbestand Berlin](https://daten.berlin.de/datensaetze/baumbestand-berlin-wfs-48ad3a23)
- **Provider:** Senatsverwaltung für Mobilität, Verkehr, Klimaschutz und Umwelt Berlin
- **Licence:** Datenlizenz Deutschland – Zero – Version 2.0 (checked 17 October 2026)
- **Service:** <https://gdi.berlin.de/services/wfs/baumbestand>
- **Snapshot:** 962,545 rows; 956,347 distinct non-null `pitid` values; layer `Berlin_trees`
- **Provenance gap:** the acquisition date and export procedure are unrecorded. The `source_layer` values show `baumbestand:strassenbaeume` and `baumbestand:anlagenbaeume`. This is the project's existing input, not a fresh official export.

**CRS warning:** the file declares EPSG:4326 but stores metre coordinates that match EPSG:25833. The analysis validates the coordinate range and overrides the CRS before spatial joins; the archived bytes stay unchanged.

The inventory covers street trees and only part of the green-space trees. It is a current catalogue, not a historical monthly population or a complete canopy inventory.
