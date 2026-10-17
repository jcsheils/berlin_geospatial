# Validation record

Verified 17 October 2026 against the packaged local files. This records checks performed, not a guarantee of scientific validity or an institutional approval.

| Check | Result |
| --- | --- |
| Portable automated suite | **46 tests passed** in the working repository and in a separate clean copy containing only release files |
| Dataset contracts | **0 errors**, 10 documented limitation warnings, 25 informational results |
| Source inventory recovery | Compressed tree snapshot restored in the clean copy; uncompressed SHA-256 exactly matched the original analysis input |
| Foundation rebuild from frozen sources | **36,856 monthly rows** and **11,127 crosswalk rows** reproduced; table parity checked at numerical tolerance 1e-10 |
| Sample reconciliation | Rebuilt totals: **57,786 events and 2,249,502 litres**; distinct trees: **11,127** |
| Examination brief | Four pages rendered and visually inspected |
| Map atlas | Thirteen pages (contents plus twelve map plates) rendered and visually inspected; image classifications preserved |
| Exact-file checks and internal links | Verified with `python tools/verify_examination.py`; the release manifest stores SHA-256 for all packaged files except itself |
| GitHub individual-file sizes | No selected file exceeds 100 MiB; largest is the approximately 61 MB compressed tree inventory |

## Verification environment

The scientific checks used Python 3.12.14 with the versions in [test_environment.json](test_environment.json). All direct spatial dependencies match `requirements-spatial.txt`. PDF assembly used ReportLab 4.4.9 and Pillow 12.3.0. Rendering used Poppler with a local writable font cache.

The clean-copy check used the existing tested Python environment, not a new dependency installation or an independent operating system. It did not copy `.venv`, local feedback files, draft Office documents, caches, or the uncompressed tree inventory. The latter was restored from the included archive. Tests no longer depend on a private file in Downloads.

The foundation was rebuilt separately from the frozen raw logs, restored inventory and LOR geometry. This verifies the main join, totals and shared panel. The complete notebooks and all exploratory models were not refitted during packaging; their persisted outputs, metadata and existing scientific checks were reviewed. Original proposal, slides and workbook were preserved, not substantively revised.

## Limitations retained by validation

Warnings cover the inventory CRS correction, source and denominator caveats, missing weather, and unverified local-LST processing. A green test suite does not resolve those scientific limitations. The positive tree-day table is not a completed daily risk set, and the proposed inferential models remain future work.

If files are intentionally rebuilt or edited, checksums will change. Review the changes and regenerate the release manifest deliberately; do not treat a hash mismatch as permission to replace a source snapshot.
