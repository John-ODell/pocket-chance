# PCB-001: Battery, charging and power path for spin 1

- **Status:** **decided by John 2026-10-04** (via the PM, after AUDIT-2): Option A as revised, JST LiPo only, cell temperature handled by the cell's protection board and a 0.5 C charge rate with a third socket pin for a thermistor cell, no on-board sensor. Awaiting the PM's ruling file. HR-P03 reviewed the earlier version; the expert is asked to re-check only the changed items (marked *re-review*).
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
- **Charger: BQ24074 (Texas Instruments).** A linear single-cell charger with "dynamic power path": with USB present the board runs from USB and the cell charges at the same time; when USB goes away the cell takes over with no glitch. Up to 1.5 A charge (we set about 500 mA); input over-voltage shut-off at about 6.6 V, operating input up to 10.5 V for the BQ24074 variant, and an absolute-maximum input per its datasheet (AUDIT-3 corrected my earlier "28 V": the datasheet's figure governs), so a wrong adapter does not kill it; thermal regulation; a thermistor input for the cell's temperature. 3 x 3 mm 16-pin QFN, fab-placed. KiCad has its symbol and a matching footprint. Source: ti.com product page, read 2026-10-04; datasheet to download with John's approval.
- **Regulator: TPS63001 (Texas Instruments).** A 3.3 V buck-boost: 1.8 to 5.5 V in, 1.2 A out when the input is above 3.6 V, 800 mA when boosting from a low cell, under 50 µA idle, 96 % peak efficiency, 3 x 3 mm 10-pin. It keeps 3.3 V steady from a full cell (4.2 V) down to an empty one (3.0 V), which an ordinary regulator cannot (HR-033). Its enable pin takes the slide power switch, with a pull-down so the board is off with no switch fitted. Source: ti.com product page, read 2026-10-04.
- **Protection: DW01A + FS8205A** on the board (over-charge, over-discharge, over-current, short), **and** only protected cells are ever fitted: a protected pouch cell, and a **protected 18650** (bare 18650s are usually unprotected; the expert's condition, HR-P02 follow-up).
- ~~Two connectors, one cell at a time~~ **Dropped 2026-10-04.** Replaced by:
- **One JST-PH 2.0 mm socket (3-pin S3B-PH-SM4-TB, surface-mount; pins 1-2 for the cell, pin 3 for a thermistor lead), pin 1 = positive, "+ RED WIRE" and "-" on the silkscreen beside the socket.** Cells from different sellers come with the red wire on either pin, which is the classic way a board dies on first plug-in. An electronic reverse-polarity guard was tried in rev 0.3 and rev 0.5 and **removed in rev 0.6 by John's decision** (see the section below): the protection is procedural, as on the Pico W.
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

## Cell temperature while charging: the decision and its residual risk (AUDIT-2 findings 7 and 8; John, 2026-10-04)
- **Assumed cell:** a protected single-cell LiPo pouch, 3.7 V nominal, **1000 mAh or more**, rated for at least **0.5 C** charging, charging temperature window **0 to 45 °C** (the usual pouch-cell rating; the cell's own datasheet rules), 2-wire JST-PH plug, + on pin 1 (red wire).
- **Charge current:** R14 1.8 kΩ gives 443 to 542 mA (BQ24074 K_ISET 797 to 975 AΩ), nominal 494 mA = 0.49 C for 1000 mAh. In the USB500 mode the charger's total input is capped at 500 mA including the board's own draw, so the cell never sees more than 500 mA minus the system load even at the top of the K_ISET spread (AUDIT-3). For a 500 mAh cell, R14 = 3.6 kΩ: 229 to 271 mA over the K_ISET spread, 247 mA nominal, so up to 0.54 C at the top of tolerance (AUDIT-3: use a 1 % resistor and a cell rated at least 0.6 C, or a larger cell). The value is printed on the silkscreen. Termination at the charger's 10 % default (about 49 mA), pre-charge handled by the chip, safety timer about 6 h (R16 47 kΩ).
- **What the charger cannot do with a two-wire cell:** sense the cell's temperature. R12 (10 kΩ on TS) is fitted by default, which tells the charger the cell is always at a safe temperature. The charger's own thermal regulation protects the charger chip, not the cell.
- **What protects the cell instead:** its own protection board (over-charge, over-discharge, over-current), the conservative 0.5 C rate, the 6 h safety timer, and the on-board DW01A + FS8205A as a second layer.
- **The better configuration:** a cell with a thermistor lead on socket pin 3 (TS); then R12 is removed and the charger stops charging below 0 °C and above about 45 °C by itself.
- **Owner warning (also on the schematic and in `pcb/BATTERY.md`):** use only a protected cell; check the wire colours against the + and - marks; charge on a non-flammable surface; never leave the first power-ups unattended; stop if the cell or the charger area gets warm to the touch.
- Residual risk accepted by John: a damaged or counterfeit cell without a working protection board, charged in a hot or freezing place, is not caught by this board.

## Reverse-polarity protection: John's decision after AUDIT-3 (option B, 2026-10-04): no on-board electronic guard (rev 0.6)
The rev 0.3 single-FET guard was not safe with USB present; the rev 0.5 polarity-sensing guard latched on after a cell swap with USB attached, and no passive two-wire circuit can do better (AUDIT-3, HR-P05 part 6, AUDIT-2-RESPONSE). Removed: Q2, Q5, R45 to R48. Kept: the R22 0 Ω ammeter link in the cell lead, the 3-pin socket with the thermistor pin, the DW01A + FS8205A protection, everything else of rev 0.5. The protection that replaces the guard: keyed JST-PH plug; **"+ RED WIRE"** and "-" on the silkscreen beside the socket; one approved cell listing with its wire colours recorded in `pcb/BATTERY.md` before purchase; a protected cell only; check the wires against the silkscreen BEFORE plugging in; UNPLUG USB before swapping cells; the first plug-in on a current-limited supply with the meter on the 3V3 and BAT+ test points. Honest residual: a mis-wired cell can damage the DW01A protection chip and the charger's BAT pin (both have a -0.3 V limit); this is the same posture as the Pico W and Pico 2 W.

## Changes from AUDIT-2 (commit 808ccf1, schematic rev 0.3)
- Reverse-polarity guard Q2 redrawn with its drain on the cell and source on the board (finding 1).
- Battery divider gated by the 3.3 V rail through Q3/Q4 so GPIO28 sees nothing while the board is off (finding 2).
- L2 named (Abracon ASPIAIG-F4020-2R2M, saturation and DCR to confirm from its datasheet) and the three 10 µF capacitors specified as 0805, 10 or 16 V, X5R (finding 10).
- R15 (ILIM) not fitted; USB500 is the active input limit (finding 13).

## Appendix
- Expert input so far: HR-033 section 2 (charger, protection, buck-boost not LDO, switch on enable, fuel gauge optional), HR-P01 (size the buck-boost for 500 mA+, consider a switched card supply), HR-P02 follow-up (protected 18650 only).
- Parts and KiCad symbols: `pcb/bom/PARTS.md`, power block.
- Datasheets still to download (official, with John's approval): BQ24074, TPS63001, DW01A, FS8205A, Keystone 1042, JST PH.
