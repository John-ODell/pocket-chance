# DR-004: Use the Pillow library for the Mac-side asset converter

- **Status:** pending
- **Filed by:** senior dev
- **Date:** 2026-10-03
- **Blocks:** Converter script (PNG input, resizing)
- **Needs HW review:** no

## The decision
Whether the converter may use the third-party Python library Pillow.

## Why it matters
`ASSETS.md` promises PNG input and nearest-neighbour resizing. Python's standard library cannot read PNG.

## Options
### A. Pillow (recommended)
- What it is: the standard Python imaging library. Licence: HPND (a permissive MIT-style licence), fine for this use. It is Mac-side only and never goes on the board. Version 12.3.0 is already installed on John's Mac.
- Pros: reads BMP, PNG and more. Handles resizing. Almost no code.
- Cons: one tool dependency on the Mac (already present).

### B. Standard library only, 24-bit BMP input only
- Pros: no dependency.
- Cons: drops PNG, and John would have to export exact-size BMP every time. No resize helper.

## Recommendation
Option A. I would change my mind only if John does not want to install anything; here it is already installed.

## What John would have to do or accept
Nothing; Pillow is already installed.
