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

## 2025 inventory

`trees_2025_gbif.csv.gz` holds one row for each of the 927,914 trees in an archive of the 2025 inventory: identifier, district, genus, planting year and EPSG:25833 position. `analysis/build_feedback_benchmarks.py` compares its identifiers with the 2026 snapshot above. [snapshot_2025.json](snapshot_2025.json) records hashes, counts and the source archive.

```bash
python tools/extract_tree_inventory_2025.py
```

The script downloads the archive, checks its SHA-256 and rebuilds the extract byte for byte. Pass `--archive` to use a local copy. The extract is versioned, so analyses do not need the download.

- **Source:** [Straßen- und Anlagenbaumbestand Berlin](https://doi.org/10.15468/75ssj5) on GBIF, published 19 December 2025
- **Licence:** CC0 1.0; the underlying cadastre is under Datenlizenz Deutschland – Zero – Version 2.0
- **Identifier:** `tree_id` equals `id` in the 2026 snapshot, for example `strassenbaeume.00008100_0012abcd`. Replace the layer prefix and the underscore to get the `pitid` used by the watering logs (`00008100:0012abcd`).
- **Vintage:** the archive holds 67 street trees planted in 2025 and the 2026 snapshot 2,714, so it describes the cadastre before the 2025 watering season.
- **Coverage gap:** the archive is a third-party export, not an official release. It holds about 39,500 fewer trees than the platform's own 2025 import, and 4,446 street trees planted in 2022 or earlier appear in 2026 under identifiers it lacks.
- **Format quirk:** the archive writes missing attributes as `None`. The script reads them as missing; a strict JSON parser would silently drop the planting year of about 77,000 trees.
