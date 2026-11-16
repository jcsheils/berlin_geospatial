# Validation record

Checked on 17 October 2026 against the packaged files. This lists the checks run; it does not certify scientific validity or approval.

| Check | Result |
| --- | --- |
| Automated suite | **46 tests passed**, in the working repository and in a clean copy holding only release files |
| Dataset contracts | **0 errors**, 10 documented limitation warnings, 25 informational results |
| Inventory restore | Clean copy restored the compressed snapshot; the uncompressed SHA-256 matched the original input |
| Foundation rebuild | **36,856 monthly rows** and **11,127 crosswalk rows** reproduced; tables matched at tolerance 1e-10 |
| Sample reconciliation | **57,786 events, 2,249,502 litres, 11,127 distinct trees** |
| Examination brief | Four pages rendered and inspected |
| Map atlas | Thirteen pages (contents plus twelve plates) rendered and inspected; classifications preserved |
| File checksums and links | `python tools/verify_examination.py`; the manifest stores SHA-256 for every packaged file except itself |
| File sizes | Nothing exceeds GitHub's 100 MiB limit; the largest file is the 61 MB compressed inventory |

## Environment

Python 3.12.14 with the versions in [test_environment.json](test_environment.json); all direct spatial dependencies match `requirements-spatial.txt`. PDF assembly used ReportLab 4.4.9 and Pillow 12.3.0, and rendering used Poppler with a local font cache.

The clean copy reused the tested Python environment rather than a fresh install or a different operating system. It left out `.venv`, local feedback files, Office drafts, caches and the uncompressed inventory, which it restored from the archive. No test depends on private files.

The foundation rebuild started from the frozen logs, restored inventory and LOR geometry, which verifies the main join, totals and shared panel. Packaging did not refit the notebooks or exploratory models; it reviewed their saved outputs, metadata and checks. The proposal, slides and workbook are unchanged.

## Limits

Warnings cover the inventory CRS correction, source and denominator caveats, missing weather and unverified LST processing; passing tests does not resolve them. The positive tree-day table is not a daily risk set, and the inferential models are future work.

Intentional edits change checksums. Review the changes and refresh the manifest deliberately; a mismatch never justifies replacing a source snapshot.
