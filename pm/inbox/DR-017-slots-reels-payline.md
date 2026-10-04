# DR-017: Slots: reels, symbols, paylines and virtual strips

- **Status:** pending
- **Filed by:** senior dev
- **Date:** 2026-10-04
- **Blocks:** Slots screen (the engine is built with these as parameters)
- **Needs HW review:** no

## The decision
The shape of the slot machine: how many reels and paylines, how many symbols, and how the odds are set.

## Why it matters
It fixes the art (the cabinet windows) and the whole feel of the game. The odds come from the reel strips, so this and DR-018 together set the RTP.

## Options
### A. Three reels, one centre payline, 8 symbols, 32-stop virtual strips (recommended)
- What it is: the approved art spec already shows **three 56 x 56 windows in one row**, so one symbol per reel is visible and there is exactly one payline. Each reel is a strip of 32 stops; a symbol appears on the strip as many times as its odds need (cherry 3, lemon 7, orange 6, bell 5, bar 4, seven 3, diamond 3, star 1). Every stop is equally likely and all three reels use the same strip. While spinning, the player sees the real strip scroll past, so what flies by is honest.
- Pros: matches the art John has agreed to make; simple to read on a 240 px screen; 32,768 combinations, so odds are exact and easy to state; the top prize is 1 in 32,768 spins.
- Cons: one line only, no diagonal or "near miss" lines.

### B. Three reels, three paylines (top, middle, bottom)
- Cons: three visible symbols per reel means 168 px tall windows and a new cabinet layout; three bets per spin; much more to read on this screen.

### C. Five reels
- Cons: 5 x 56 = 280 px, does not fit.

## Recommendation
Option A. I would reconsider only if John wants the three-line look and is happy to redraw the cabinet.

## What John would have to do or accept
Nothing new: the Phase 2 art list stands (see DR-023). The symbol names are the eight in `assets/ASSETS.md`.

## Appendix
Engine: `games/slots_rules.py` (`strip`, `Reels`, `Paytable`, `exact_stats`), tests in `tests/test_slots_rules.py`. Strips and the paytable are parameters.
