# DR-006: Do the draft asset sizes in assets/ASSETS.md hold up?

- **Status:** pending
- **Filed by:** senior dev
- **Date:** 2026-10-03
- **Blocks:** Nothing. John can start art once DR-002 and DR-003 are ruled
- **Needs HW review:** yes

## The decision
Approve the sizes in `assets/ASSETS.md` as final, with the two small notes below.

## Why it matters
John makes the art, so a size change after he has drawn 60 images is expensive.

## What I checked
- **Flash:** Phase 1 is 434,816 bytes (67 files). Slots add 187,648. The total is about 0.62 MB. The RP2040-Plus has 16 MB, but I found a report that the stock MicroPython firmware only leaves about 1.4 MB for files unless the correct 16 MB firmware is used ([Waveshare wiki](https://www.waveshare.com/wiki/RP2040-Plus)). Even 1.4 MB would fit, but John should check which firmware is on the board (a probe script is in `tools/board_probe.py`).
- **Cards, 40 x 56:** the hand fits. Five cards side by side are 200 px. With a 28 px step between overlapped cards, eight cards span exactly 236 px, and the rank in the top-left corner stays visible. A blackjack hand can reach more cards than that only in extremely rare cases.
- **Vertical fit:** top 24 px plus bottom 40 px leaves 176 px. Two hands of 56 px use 112, which leaves 64 px for totals and a 32 px banner.
- **Chips 24 x 24, icons 48 x 48, banners 160 x 32, logo 200 x 40:** all fit with room. The slots cabinet works out: 3 x 56 + 2 x 18 = 204 px, leaving 18 px at each side.
- **RAM:** the largest sprite is 16 KB (logo), see DR-005.

## Options
### A. Keep every size as drafted (recommended)
### B. Change some sizes
- Nothing I found calls for it.

## Recommendation
Option A with two notes:
1. **Pilot first.** John makes four files first: `c_AS`, `c_back`, `chip_5`, and a small `table`. We run them through the converter and the board before he does the rest. That catches any problem after 4 files, not 60.
2. **`table` and `cabinet` are optional.** If they are missing, I draw a plain felt-colour background in code, so the game runs while the art is unfinished.

Orientation is still unknown (see DR-003); the same pilot test will settle which way up the art goes.

## What John would have to do or accept
Make the 4 pilot files, then the rest.
