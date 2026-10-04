# DR-003: Byte order of converted pixels (and a hardware check first)

- **Status:** pending
- **Filed by:** senior dev
- **Date:** 2026-10-03
- **Blocks:** Converter script; John should not make the full art set before this is verified
- **Needs HW review:** yes

## The decision
In which byte order the converter writes each 16-bit colour.

## Why it matters
Wrong order gives wrong colours (red and blue swapped, or garbage). It must be right before John converts 60 images.

## What I found
Reading the old driver: `colour()` builds a value whose low byte is `RRRRRGGG` and whose high byte is `GGGBBBBB`. `framebuf` keeps pixels in little-endian memory and the SPI sends memory bytes in order, so the panel receives `RRRRRGGG` then `GGGBBBBB`. That is ordinary big-endian RGB565, the order a ST7789 expects. The `0x36 = 0x70` setting leaves the colour-order bit at RGB. The Waveshare example calls the panel "BRG", but I believe that is a misreading of the same byte swap. **This is from reading code only. It has not been tested on the board.** The expert can check it with a test image.

## Options
### A. Big-endian RGB565 in the file, copied unchanged into the framebuffer (recommended)
- The file bytes are exactly what goes down the wire, so loading is a plain `readinto` with no per-pixel work. The transparent key is the bytes `F8 1F`, which `framebuf` reads as the number `0x1FF8`.
- Cons: if my reading is wrong, the first test image shows it (cheap to flip).

### B. Little-endian (native) in the file, swap on load
- Cons: a swap loop on a 133 MHz core for every image. Slower and more code, for no benefit.

## Recommendation
Option A, **plus a gate**: I write a small test-image converter and board test, John runs it and reports what he sees (colour bars and a "top-left" marker, which also settles which way up the art must be, given `0x36 = 0x70`). Only after that does John make the full art set. If the colours are wrong, I flip the order in one line and nothing else changes.

## What John would have to do or accept
Run one test image on the board and tell me what he sees. I will put exact steps in `UPLOAD.md` once the converter exists (after DR-002, DR-003 and DR-004 are ruled).
