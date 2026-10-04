# DR-005: How assets are loaded from flash and drawn

- **Status:** pending
- **Filed by:** senior dev
- **Date:** 2026-10-03
- **Blocks:** Asset loader (lib/assets.py), blackjack screens
- **Needs HW review:** yes

## The decision
How image files move from flash to the screen without running out of RAM.

## Why it matters
The framebuffer alone is 115,200 bytes of the board's 264 KB. All 52 cards in RAM would be another 233 KB, which is impossible.

## Options
### A. Background straight into the framebuffer, small sprites through one shared scratch buffer (recommended)
- What it is:
  - A full-screen image (`table`, `cabinet`) is read with a single `readinto` straight into the framebuffer. It needs no extra RAM.
  - A sprite (card, chip, symbol, banner) is read into one scratch buffer sized for the largest sprite (16 KB for the logo, 4.5 KB for a card), wrapped in a `FrameBuffer`, and drawn with `blit()` using the transparent key. No sprites are cached, because reading a few KB from flash should be quick (my estimate is about a millisecond; the expert should measure it).
  - Redraw order each frame: table, cards, chips, text, then `show()`.
- Pros: peak extra RAM is about 16 KB. Simple.
- Cons: re-reading the table each frame costs time (my guess is tens of milliseconds; **not measured**, the expert should measure full-frame redraw and flash read speed). If that feels slow I would redraw only what changed, a small change inside the same approach.

### B. Cache a few sprites in RAM (chips, card back)
- Pros: slightly faster.
- Cons: more RAM and code for no visible gain.

### C. Skip the framebuffer and stream rows straight to the display
- Pros: lowest RAM.
- Cons: no layering or transparency. Much more complicated.

## Recommendation
Option A. I will report `gc.mem_free()` and a redraw timing from the board in the hardware test notes.

## What John would have to do or accept
Nothing.
