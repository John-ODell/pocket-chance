# PCB-001: Battery, charging and power path for spin 1

- **Status:** pending; **revised 2026-10-04 after John's choice of the JST LiPo over the 18650 holder** (via the PM). HR-P03 reviewed the earlier version; the expert is asked to re-check only the changed items (marked *re-review*).
- **Filed by:** PCB maker
- **Date:** 2026-10-04
- **Blocks:** the power sheet of the schematic (phase 3). The rest of the schematic proceeds.
- **Needs HW review:** yes (role file rule 7: the battery path gets the expert's second opinion)

## The decision
How the board is powered: which charger, which regulator, which protection, and how a single protected pouch LiPo on a JST connector is connected safely, charged on the board, with USB pass-through. (The 18650 holder and the cell-select jumper are **dropped**: John chose the flat board, 2026-10-04.)

## Why it matters
This is the one block that can start a fire if wrong, and the one that decides whether the board resets mid-game as the battery runs down. It also sets the board's thickness: an 18650 is 18 mm thick, a pouch cell 5 to 8 mm.

## What John asked for (DR-033 ruling, item 6)
A single lithium cell, either a LiPo through a connector or an 18650 holder, charged on the board, and the board may run from USB while charging.

## Options

### A. Power-path charger + buck-boost + protection, two cell connectors with a select jumper (recommended)
- **Charger: BQ24074 (Texas Instruments).** A linear single-cell charger with "dynamic power path": with USB present the board runs from USB and the cell charges at the same time; when USB goes away the cell takes over with no glitch. Up to 1.5 A charge (we set about 500 mA); input over-voltage shut-off at about 6.6 V and 28 V survival, so a wrong adapter does not kill it; thermal regulation; a thermistor input for the cell's temperature. 3 x 3 mm 16-pin QFN, fab-placed. KiCad has its symbol and a matching footprint. Source: ti.com product page, read 2026-10-04; datasheet to download with John's approval.
- **Regulator: TPS63001 (Texas Instruments).** A 3.3 V buck-boost: 1.8 to 5.5 V in, 1.2 A out when the input is above 3.6 V, 800 mA when boosting from a low cell, under 50 µA idle, 96 % peak efficiency, 3 x 3 mm 10-pin. It keeps 3.3 V steady from a full cell (4.2 V) down to an empty one (3.0 V), which an ordinary regulator cannot (HR-033). Its enable pin takes the slide power switch, with a pull-down so the board is off with no switch fitted. Source: ti.com product page, read 2026-10-04.
- **Protection: DW01A + FS8205A** on the board (over-charge, over-discharge, over-current, short), **and** only protected cells are ever fitted: a protected pouch cell, and a **protected 18650** (bare 18650s are usually unprotected; the expert's condition, HR-P02 follow-up).
- ~~Two connectors, one cell at a time~~ **Dropped 2026-10-04.** Replaced by:
- **One JST-PH 2.0 mm socket (S2B-PH-SM4-TB, surface-mount, the hobby-LiPo standard), pin 1 = positive, marked + and - on the silkscreen beside the socket.** Cells from different sellers come with the red wire on either pin, which is the classic way a board dies on first plug-in, so the board also gets a **reverse-polarity guard**: a small P-channel MOSFET (AO3401A, SOT-23, the most common hobby P-FET) in the positive lead that only conducts when the cell is the right way round; a reversed cell simply does nothing. Cost: one part, about 20 mV drop. *re-review.* John still checks the wire colours against the silkscreen before plugging in.
- **Cell size guideline for a flat credit-card board:** a thin pouch cell of about 3 to 6 mm thickness, up to about 35 x 50 mm, 500 to 1200 mAh, with its own protection board and a JST-PH plug: sizes sold as 503450 (5.0 x 34 x 50 mm, about 1000 mAh), 603048 (6 x 30 x 48 mm, about 1000 mAh) or 303450 (3 x 34 x 50 mm, about 500 mAh). It lies flat beside or under the board. **Charge current must match the cell:** 500 mA (R_ISET 1.8 kΩ) for 1000 mAh and up; 250 mA (R_ISET 3.6 kΩ) for a 500 mAh cell. One resistor; the value is written on the silkscreen. *re-review of the two values.*
- Old text, kept for the record: a JST-PH 2-pin surface-mount socket for the pouch cell and a Keystone 1042 holder (through-hole, PCBWay places it) for the 18650, both feeding one protected battery node through a **three-pad solder jumper** that selects exactly one. The fab bridges the JST side by default; moving the bridge takes a soldering iron for ten seconds, which is the one deliberate hand step. Silkscreen: "ONE CELL ONLY: JST or 18650, set J1". Why not both live at once: two cells at different voltages tied together push large currents into each other, and the charger would charge both without knowing.
- **Cell temperature:** the BQ24074's thermistor pin gets a 10 kΩ fixed resistor (treats the cell as always at a safe temperature) because hobby pouch cells and holders have no thermistor; the footprint for a real thermistor is left in. This is the common practice on hobby boards; a cell with a thermistor lead can use it.
- **Charge current:** 500 mA. Safe for any 18650 (2000 mAh and up) and for pouch cells of 1000 mAh or more; a smaller pouch cell needs a resistor change (one part). Linear charging from 5 V into an empty cell dissipates about 0.6 W in the charger: the layout gives it a copper pour.
- Cost: about 6 to 9 USD of parts per board (estimate).

### B. Same as A with the MCP73871 (Microchip) as the charger
- The other well-known power-path charger (used on Adafruit boards). 4 x 4 mm 20-pin, more external parts, 1 A. Microchip's product page refused the fetch today, so its figures are from memory and **unverified**. Equivalent in function; A is chosen for the smaller part and the verified page.

### C. Simple charger without power path (MCP73831) and a diode to share USB and cell
- Cheaper and simpler, but the "run from USB while charging" wish is only half met (the charger cannot tell the board's current from the cell's, so charging finishes early or never) and the diode costs voltage. Not recommended for a board that wants USB pass-through.

### D. One connector only (JST pouch cell), 18650 later
- Simplest and thinnest. Does not meet John's "either" wish on spin 1.

## Recommendation
**Option A as revised (JST only, with the reverse-polarity guard).** It meets every part of the ruling with the two best-documented parts in their class and keeps the safety rules: protected cells only, on-board protection as well, one cell at a time by construction, current-limited first power-up (no cell fitted first; then cell with USB off; then both). What would change my mind: if the expert prefers the MCP73871 from experience, B; if John decides the 18650 bump spoils the flat board, D with the holder as a spin 2 item.

## What John would have to do or accept
- The board stays flat; the pouch cell lies beside or under it. John buys a protected pouch cell with a JST-PH plug in the size range above and checks its wire colours against the + and - marks before plugging in.
- Buy **protected** cells only (the listing says "protected" or "with PCM").
- Before the first battery test: a current-limited bench supply (or the expert's agreed alternative), the first power-up with no cell.

## Appendix
- Expert input so far: HR-033 section 2 (charger, protection, buck-boost not LDO, switch on enable, fuel gauge optional), HR-P01 (size the buck-boost for 500 mA+, consider a switched card supply), HR-P02 follow-up (protected 18650 only).
- Parts and KiCad symbols: `pcb/bom/PARTS.md`, power block.
- Datasheets still to download (official, with John's approval): BQ24074, TPS63001, DW01A, FS8205A, Keystone 1042, JST PH.
