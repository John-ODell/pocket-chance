# DR-002: Converted asset file format: tiny header or raw pixels

- **Status:** pending
- **Filed by:** senior dev
- **Date:** 2026-10-03
- **Blocks:** Converter script (tools/convert_assets.py), asset loader
- **Needs HW review:** yes

## The decision
What a converted image file on the board contains. `ASSETS.md` says headerless raw pixels with the size taken from a manifest or the filename.

## Why it matters
John will make about 60 images. A wrong-sized or wrong-format file should be caught immediately with a clear message, not show up as a scrambled card on the screen.

## Options
### A. Headerless raw RGB565, size from the filename or a manifest
- Pros: simplest possible file. Matches the current draft.
- Cons: the loader needs a manifest or a size table. A file of the wrong size is only noticed if the loader checks the file length against the table.

### B. Raw RGB565 with a 4-byte header: width and height, each 16-bit little-endian (recommended)
- Pros: each file describes itself, so no manifest is uploaded. The loader checks that file length equals 4 + width x height x 2 and refuses bad files with a clear error. Streaming still works: read 4 bytes, then read pixels straight into a buffer.
- Cons: 4 extra bytes per file (negligible). The draft says headerless, so this changes `ASSETS.md`.

## Recommendation
Option B, extension `.565`, names as in `ASSETS.md` with `.bmp` replaced by `.565` (for example `c_AS.565`). Transparency stays magenta #FF00FF. The converter guarantees that no other pixel in the art ever converts to the transparent value (it nudges such a pixel by one shade), so a normal pixel never turns invisible by accident.

## What John would have to do or accept
Nothing extra. The "Bytes on board" column in `ASSETS.md` gains 4 bytes per file.
