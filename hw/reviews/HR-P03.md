# HR-P03: Second opinion on PCB-001, battery, charging and power path

- **Verdict: fits. Option A, with the conditions below.** This is the second opinion role-file rule 7 asks for; the block is sound and the two chosen parts are the ones I would have picked.
- Reviewer: microcontroller expert, 2026-10-04. Desk review from the request, `pcb/bom/PARTS.md` and general experience with these parts; the datasheets named in the request are still to be downloaded and read, so every number below is to be checked against them before the schematic freezes.

## The four questions

### (1) BQ24074 OUT straight into TPS63001 VIN: agree
- OUT follows the input when USB is present (about 4.6–4.9 V after the pass element) and follows the cell when it is not (3.0–4.2 V). The TPS63001 accepts 1.8–5.5 V, so there is nothing to regulate in between, and the buck-boost is exactly what turns that 3.0–4.9 V swing into a steady 3.3 V.
- Two things to get right on that node: **the BQ24074's input-current limit** (ILIM / EN1-EN2) must not exceed what the USB source offers. With 5.1 kΩ CC pull-downs the board asks for default USB power, 500 mA from a USB 2.0 port, up to 1.5 A only when a Type-C source advertises it. Set the limit to 500 mA (or use the USB500 mode) unless you add CC detection; the dynamic power path then gives the board what it needs first and charges the cell with what is left, which is the feature you bought. **And decoupling**: the BQ24074 OUT capacitor (its datasheet value, typically 4.7–10 µF) plus the TPS63001 input capacitor (10 µF close to VIN) on a short, wide trace.
- One trap: when the board draws more than the input limit with no cell fitted, OUT sags and the TPS63001 runs in boost from a falling input; that is the "first power-up with no cell" case, so keep the backlight off for it (step 4).

### (2) 500 mA charge: agree, with one number per cell
- A protected 18650 of 2000 mAh or more: 500 mA is 0.25 C, gentle. A 1000 mAh pouch: 0.5 C, standard. **Below about 800 mAh the ISET resistor must change** (keep ≤ 0.5 C); write the ISET value and its C-rate on the silkscreen or in `PARTS.md` so a smaller cell is never charged at 500 mA by accident.
- Thermal: 500 mA into an empty cell from 5 V dissipates about 0.6 W in a linear charger. The BQ24074's thermal regulation folds the current back if the die gets hot, so it cannot damage itself; give it the copper pour and the thermal vias the datasheet's layout section shows, or charging will simply be slower when warm.
- The fixed 10 kΩ on TS: standard hobby practice and acceptable **given protected cells only**; the chip then believes the cell is at 25 °C. Keep the thermistor footprint as proposed, and if a cell with a thermistor lead ever appears, use it.

### (3) Protection after the select jumper, on the common node: agree, with a wiring note
- One DW01A + FS8205A protecting whichever cell is selected is the right economy, and it also covers the mistake of an unprotected 18650 in the holder.
- The DW01A/FS8205A pair switches the **negative** lead. So: the three-pad jumper selects the **positive** lead only; both connectors' negatives tie to the protection circuit's BAT− input, and the protected BAT− goes to the board's ground. Two protection circuits in series (the cell's own PCM and the board's) add two FET drops of a few tens of milliohms each: negligible.
- Confirm the FS8205A's continuous current rating against the worst case: charge 500 mA one way, discharge up to the TPS63001's input draw the other way (roughly 0.4 A at a 3.0 V cell for a 300 mA load, more with card write bursts). The usual FS8205A pair handles 2–3 A; fine, but check.

### (4) Current-limited first power-up: the sequence I would use
1. **No cell, no switch on (EN low), USB from a bench supply at 5.0 V, limit 100 mA.** Expect only the charger's and regulator's quiescent draw plus whatever the RP2350 pulls in BOOTSEL (tens of mA). Check: OUT ≈ 4.6–4.9 V, nothing warm.
2. **Switch on, same limit.** Check the 3V3 pin at 3.25–3.35 V and the RP2350's core regulator output (about 1.1 V) at a test point. Expect 30–60 mA at the REPL with the backlight off. If the limit trips, stop and look.
3. **Raise the limit to 500 mA**, flash MicroPython, run `hwtest/load_hold.py` (backlight 100 %, continuous frames). Read the current: this is the number the whole power design has been waiting for.
4. **Cell only** (USB off): protected pouch first, charged to about 3.8 V, switch on, same checks, then the screen under load; watch 3V3 stay at 3.3 V as the cell sits at 3.7–3.8 V (that is the buck-boost doing its job).
5. **Both**: USB back on with the cell fitted; measure the charge current in the cell lead (or infer from the ISET value) and confirm it falls when the board draws more (the power path working). First charge supervised until the charger reports done.
- **Add to the board for this:** test points on VBUS, OUT (battery node), 3V3, 1V1 and GND; a 0 Ω link footprint in the cell lead that can be opened to insert an ammeter.
- John said he has a multimeter and a soldering iron but no bench supply; a USB inline power meter (about 10 USD) gives the current for steps 1–3 and 5 without cutting anything, and a USB power bank with a known limit is a poor substitute for a current-limited supply: for step 1 and 2 borrow or buy a small bench supply, or do those steps with the inline meter and a hand on the power switch.

## Alternatives
- **MCP73871** (option B): a good part, the Adafruit lineage proves it; bigger and with more external parts, and its page could not be read today. No reason to prefer it over the BQ24074 for this board.
- **MCP73831 + diode** (option C): I would not; the request says why.
- **JST only** (option D): a fine fallback if the 18650 bump spoils the board's shape; keep the holder's footprint so the decision can be made at layout.

## Core block values glanced at (`PARTS.md` block 1)
ABM8-272-T3 12 MHz with 15 pF C0G load capacitors and a 1 kΩ series resistor; the Abracon 3.3 µH inductor with the polarity dot, 4.7 µF x3 and the 33 Ω VREG_AVDD filter; 27 Ω USB series resistors; 1 kΩ in the flash CS line to the BOOT button and the PSRAM CS pull-up on GP0. These match the RP2350 hardware design guide as I know it; nothing to add. Two "verify" flags the PCB maker already has (the APS6404L package body, the inductor footprint) are the right ones to carry.

## What I could not verify
The BQ24074, TPS63001, DW01A, FS8205A datasheets themselves (not yet downloaded); the real board current (needs the multimeter session, `hwtest/load_hold.py`).

## Re-review after John's choice: JST pouch cell only (2026-10-04)
- **(a) Reverse-polarity guard, AO3401A P-FET in the positive lead, gate to the cell's negative pin:** correct and standard. Right way round: the body diode lifts the source to the cell voltage, the gate sits at cell negative, Vgs = −Vcell (−3.0 to −4.2 V) turns it fully on (Vgs(th) about −0.9 V, Rds(on) around 50 mΩ: roughly 25 mV at 500 mA, as the request says). Reversed: the body diode blocks and Vgs is positive, so nothing conducts. Charging current flows source→drain with the same Vgs, so it charges through the FET too. Two notes: take the gate from the **connector's** negative pin, not from the protected ground after the DW01A, so the guard judges the cell itself; and the AO3401A's Vgs maximum (±12 V) is never approached by one cell. Agree.
- **(b) ISET 1.8 kΩ → 500 mA, 3.6 kΩ → 250 mA:** consistent with the BQ2407x relation I_CHG = K_ISET / R_ISET with K_ISET ≈ 890 A·Ω (494 mA and 247 mA). From memory; **confirm K_ISET and the resistor range in the datasheet** when downloaded. The silkscreen note of the fitted value is the right habit.
- **(c) Cell guideline (503450 / 603048 ≈ 1000 mAh, 303450 ≈ 500 mAh, 3–6 mm thick, with PCM and a JST-PH plug):** sensible sizes for a flat board; add "check the red wire is on the + mark before plugging in" to the silkscreen, since the guard protects the board but not a cell shorted by a wrong adaptor.
- **EN1 high, EN2 low = 500 mA input limit:** matches my memory of the BQ24074 EN table (EN2:EN1 = 00 → 100 mA, 01 → 500 mA, 10 → ILIM, 11 → disabled). **Verify in the datasheet**; a swapped pair would silently give 100 mA and a board that browns out at full backlight.
Everything else stands as reviewed.
