# Stage 2: from the approved scope to a quote

Ruling: `pm/outbox/DR-033.md` (2026-10-04, Option B with the owner's choices). This file tracks the phases of `PLAN.md` for spin 1. Nothing is ordered without John's explicit yes; John places the order.

## What spin 1 is (from the ruling)
RP2350A, 16 MB flash, 8 MB PSRAM; 1.54" 240 x 240 ST7789 module on a header; joystick and four buttons on today's pins; RM2 wireless fitted; speaker amplifier and speaker connector fitted; microSD; DS3231 RTC with CR1220; 6-axis IMU; STEMMA QT connector; SWD header; test points; single lithium cell (JST LiPo or 18650 holder), charged on the board, USB pass-through; flat credit-card-style board; PCBWay, fab-assembled. Design principle: **each optional block is grouped so it can be removed on spin 2 without touching the rest.**

## Phases and status

| # | Phase | Status | What John looks at when it ends |
|---|---|---|---|
| 1 | Install KiCad | **done** (KiCad 10.0.6, `kicad-cli` present) | open `pcb/kicad/pocket-chance-board.kicad_pro` once, confirm it opens |
| 2 | Parts shortlist | in progress: `pcb/bom/PARTS.md` | the shortlist, one line per part, with "fab can place it" and "in stock" columns |
| 2a | PCB-001: battery and power path | to file | the decision request (power-path charger, buck-boost, protection, two cell connectors) |
| 3 | Schematic, ERC clean | not started | the schematic PDF export, sheet by sheet |
| 4 | Review 1 (expert pins and electrics; PCB maker vs the RP2350 design guide) | not started | the review file |
| 5 | Footprints checked against datasheets | not started | the 3D view screenshots |
| 6 | Layout, DRC clean | not started | the board PDF and 3D view |
| 7 | Review 2 and the 1:1 paper print | not started | the print, with the real screen module and connectors held on it |
| 8 | Fab files (Gerbers, drill, BOM, centroid) | not started | the zip in `pcb/fab/` |
| 9 | PCBWay instant quote (no sign-in, no payment) | not started | the quote, read line by line against the checklist |
| 10 | Pre-order checklist | not started | the checklist, every box ticked, then John orders |

## Working rules for this stage
- KiCad files live in `pcb/kicad/`. The PCB maker generates and checks them with `kicad-cli`; John opens them in KiCad to look and to learn, and reports what he sees.
- Every part in `pcb/bom/PARTS.md` carries: manufacturer part number, package, KiCad symbol and footprint, official datasheet link, PCBWay/distributor stock status, and which block it belongs to (core, power, screen, input, audio, card, sensors, wireless).
- Decisions that need John: `pm/inbox/PCB-001`, `PCB-002`, ... one each.
- Each phase ends with a note to the PM and a line here.
