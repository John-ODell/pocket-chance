# Plan: from the existing board to your own board

A first-PCB roadmap. Each phase ends with something you can check. The PCB maker teaches each step as you reach it. Costs and times below are **estimates**: confirm every price on the fab's quote page before you order.

## What you are making

A new dev board that does what the Waveshare RP2040-Plus plus the 1.3" LCD HAT do together, built around the same RP2040 chip so the game's software keeps working. The exact scope is your first decision (below).

## Two stages (the owner's order of work)

**Stage 1: Understand. No design choices yet.** The PCB maker learns what we have (the Waveshare board, the HAT, the software that depends on them), how a board like this becomes a manufactured PCB, and every constraint we face: electrical, mechanical, software, fab, tools, budget and skill. The result is `pcb/CONSTRAINTS.md` and a short primer, `pcb/HOW_A_BOARD_IS_MADE.md`, both written for a beginner. Nothing is chosen, bought or drawn.

**Stage 2: First design.** Only after the owner has read Stage 1 do they say what to add: the scope, screen approach, battery, extras. The decisions below belong to Stage 2.

## Decisions the owner must make first

The PCB maker asks these one at a time, recommends an answer, and records each in `pm/outbox/` once ruled.

1. **Scope.** Which of these are on the board?
   - RP2040, 16 MB flash, USB-C: yes (the starting point)
   - Screen: the same 1.3" 240 x 240 module (on a header), or a bare panel on a connector
   - Joystick and 4 buttons: on the board, same pins as today
   - LiPo battery with charging: yes or no
   - Extras: speaker or buzzer, vibration, a microSD slot, expansion headers
2. **Screen approach.** A header for the existing Waveshare screen module is far easier for a first board. A bare panel on a flex connector gives a thinner product but is harder to source and test.
3. **Battery.** A handheld wants it. It adds a charger chip, protection and real safety work.
4. **Form factor.** One board the size of the HAT (the board is the handheld), or a board that plugs under the existing HAT.
5. **Assembly.** Order bare boards and solder them yourself, or have the fab assemble the small parts for you. Hand-soldering the RP2040 (a tiny square chip with no leads) is hard. Assembly costs more but is the realistic route for a first board.
6. **Budget and timeline.** What are you willing to spend on the first run, and how long can you wait?
7. **Sharing.** Will the board design be published as open hardware, and under which licence?

## Phases

| # | Phase | What you do | What you have at the end |
|---|---|---|---|
| 0 | Requirements | Answer the decisions above. PCB maker reads the docs | `pcb/requirements/REQUIREMENTS.md`, every fact with its source |
| 1 | Install tools | Install KiCad. Confirm it opens | A blank KiCad project in `pcb/kicad/` |
| 2 | Parts choice | Choose the main parts with the PCB maker (flash, regulator, charger, connector, crystal, ESD, passives) | A shortlist with datasheet links and a "can the fab assemble it?" check |
| 3 | Schematic | Draw it in KiCad's schematic editor, guided step by step | A schematic that passes the electrical rules check (ERC) |
| 4 | Review 1 | The microcontroller expert checks every pin against the code. The PCB maker checks against the official RP2040 design guide | A written review with open risks listed |
| 5 | Footprints | Assign a physical footprint to every part, check each against its datasheet | Every part has a footprint that matches the real part |
| 6 | Layout | Place parts, route traces, add the ground plane. Follow the official layout advice for the crystal, flash and USB | A board that passes the design rules check (DRC) |
| 7 | Review 2 | Second review of the layout, 3D view, test points | A written review |
| 8 | Fab files | Export Gerbers, drill, BOM and pick-and-place with `kicad-cli` | A zip in `pcb/fab/` the fab will accept |
| 9 | Fab's checks | Upload to the fab's quote page. Read the preview. Fix anything it flags | A quote and a preview you have checked layer by layer |
| 10 | Order | **You** place the order. The PCB maker gives you a checklist with the exact options | A confirmation and a tracking number |
| 11 | Bring-up | Follow the first-power-up checklist: measure before you connect the battery, then the screen, then flash | A working board, or a precise list of what is wrong |
| 12 | Software | Flash MicroPython and run the game from `SETUP.md`. Update `docs/HARDWARE.md` for the new board | The game running on your own board |

You can stop after any phase. Everything up to phase 8 costs nothing but time.

## Rough costs (estimates, check the quote)

| Item | Typical range |
|---|---|
| 5 to 10 bare 2-layer boards, small size | about 5 to 30 USD |
| Same boards with fab assembly of small parts | about 30 to 150 USD or more, depending on parts and fees |
| Parts the fab does not stock | about 5 to 30 USD |
| Shipping | about 10 to 40 USD, depending on speed |
| Time: design and review | days to weeks for a first board |
| Time: fab and shipping | roughly 1 to 3 weeks |

Plan for a second spin. Most first boards need one fix.

## What can go wrong on a first board (and how this plan guards against it)

| Risk | Guard |
|---|---|
| A footprint does not match the real part | Check each footprint against the datasheet. Use the 3D view. Check the fab's assembly preview |
| A part is out of stock when you order | Check stock at the fab's parts library while choosing |
| Wrong pin assignments break the software | The expert reviews every pin against `docs/HARDWARE.md` |
| USB, crystal or flash layout misbehaves | Follow the official RP2040 layout rules. Second review before ordering |
| LiPo charger or protection mistake | Use a proven charger and protection design. Test with a current-limited supply first |
| The screen module does not fit | Measure the real module. Make a paper print of the footprint at 1:1 and hold the module against it |
| You order something you did not check | The owner places the order, from a checklist, after a second review |

## Tooling

| Tool | Use |
|---|---|
| KiCad (free) | Schematic, layout, 3D view, ERC and DRC, Gerber export |
| `kicad-cli` (comes with KiCad) | ERC, DRC and exports from the terminal, so the PCB maker can check your files |
| The fab's quote page | Price, preview, design-rule check, parts stock |
| A multimeter | First power-up measurements |
| A current-limited bench supply (recommended) | Safe first power-up with a LiPo design |
| A USB-C cable and the existing board | Reference while you compare behaviour |

## Where things go

| Folder | Contents |
|---|---|
| `pcb/requirements/` | The requirements and the decisions behind them |
| `pcb/kicad/` | The KiCad project files |
| `pcb/bom/` | The bill of materials |
| `pcb/fab/` | Exported Gerbers, drill and assembly files |
| `pcb/reviews/` | Written design reviews and bring-up results |
| `pcb/refs/` | Local copies of datasheets and documents. **Ignored by git, never committed** |
