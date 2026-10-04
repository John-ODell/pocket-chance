# DR-033: What goes on the first custom board (scope)

- **Status:** pending, **parked until the owner opens Stage 2** (`pcb/PLAN.md`). Drafted now so the recommendation is on record; do not take it to John before then.
- **Filed by:** PCB maker
- **Date:** 2026-10-04
- **Blocks:** PCB phase 2 (parts choice) and every later phase. Phase 1 (install KiCad) can go ahead.
- **Needs HW review:** yes (pin plan and power; the expert should confirm the pin map in `pcb/requirements/REQUIREMENTS.md` section 5 before this goes to John)

## The decision
Which blocks are on the first custom board: the bare minimum (an RP2040 board the existing HAT plugs onto), a handheld (screen, joystick and buttons on the board), or a full product (handheld plus battery and extras)?

## Why it matters
Every block added is a block that can be wrong on a first board, and a first board usually needs one re-spin. Too little and the board is not the handheld John asked for. Too much and the first spin fails on something that had nothing to do with the goal.

## Options
### A. RP2040 core only ("my own Pico")
- What it is: RP2040, 16 MB flash, USB-C, BOOT and RESET, the 2 x 20 Pico header. The existing Waveshare HAT plugs on top.
- Pros: smallest design, closest to the official reference design, the HAT is already proven, nothing in the software changes.
- Cons: it is not the handheld John described; the screen and buttons stay on a bought part.
- Cost: lowest. Roughly 25 to 35 parts.

### B. Handheld core (recommended)
- What it is: everything in A, plus a header for the Waveshare 1.3" screen module, the 5-way joystick and four buttons on the same GPIO as today, SWD pads and test points, a user LED. No battery circuit on this spin; leave room for it. A short expansion header (power, UART, a few GPIO) instead of the full Pico header.
- Pros: it is the handheld, with the fewest new risks. The screen stays a plug-in module, so a screen problem cannot kill the board. All verified pins stay the same, so the software runs unchanged.
- Cons: USB-powered only on this spin. The battery (question 3) comes on the second spin or as a daughter board.
- Cost: roughly 40 to 50 parts. Bare boards about 5 to 30 USD, assembled about 30 to 150 USD (estimates, confirm on the quote page).

### C. Full handheld
- What it is: B plus a LiPo charger, protection and battery connector, and possibly a buzzer or microSD.
- Pros: one board does everything.
- Cons: the battery path is the one block that can start a fire if wrong, and it needs its own review and a current-limited first power-up. Doing it on the same spin as a first-ever RP2040 layout stacks the two hardest things.
- Cost: roughly 60 to 80 parts; assembly fees higher.

## Recommendation
Option B. It delivers what John asked for (RP2040 plus the screen, joystick and buttons) while keeping the first spin close to the official RP2040 reference design. The battery gets its own decision (question 3) and its own review once the core is proven. What would change my mind: if John wants a battery in the first physical prototype no matter what, C with a conservative, proven charger design; or if John mainly wants to learn the fab process with the least risk, A.

## What John would have to do or accept
- Accept that the first board runs from USB only. The battery comes later.
- Keep the same screen module (the Waveshare 1.3" LCD module) plugged into a header on the new board.
- Buy or already have: a multimeter. A current-limited bench supply is recommended before any battery work.

## Appendix
- Pin map and sources: `pcb/requirements/REQUIREMENTS.md`, sections 4 to 7.
- Parts Waveshare uses on the Plus (for the expert's reference, from the product page, not a decision): W25Q128JVSIQ flash, MP28164 buck-boost, ETA6096 charger, MX1.25 battery connector.
- Cost figures are the ranges in `pcb/PLAN.md` and are estimates.
