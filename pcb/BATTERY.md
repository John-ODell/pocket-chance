# Battery: what to buy and how to be safe (spin 1)

Written for John, 2026-10-04. The decisions behind it are in `pm/inbox/PCB-001-battery-and-power-path.md` and the audit response in `pcb/reviews/AUDIT-2-RESPONSE.md`.

## The fuse
The board has a self-resetting fuse in the battery lead (1.5 A hold, your decision). It trips if a battery lead, a protection transistor or the board shorts, and it limits the heat after a wiring mistake. It does not save the two chips a reversed battery destroys: the wire check above is still the protection. It costs a few tens of millivolts, so a charge finishes a few minutes later. To reset it, **unplug the battery**: a tripped fuse stays warm and keeps passing a small current as long as the battery is connected; it resets within a minute of being unplugged, once it has cooled. Then find the fault before plugging the battery back in.

## Approved test battery (John, 2026-10-04)
**JLJLUP 3.7 V 2000 mAh LiPo, 2-pack (Amazon listing B0FH7G1WPG):** 34 x 10 x 52 mm, 34 g, integrated protection circuit, JST-PH 2.0 mm two-wire plug, rated 1 C discharge (about 2 A). Fits the standard-cell specification below except thickness (10 mm instead of 5 to 6), which is fine for the spin 1 dev board; the enclosure question comes with spin 2.
- Charging at this board's 494 mA is 0.25 C, gentle for the cell. A full charge from empty takes about 4.5 to 5 hours (longer when the board is also drawing from the same 500 mA USB budget), which is close to the safety timer's shortest possible setting with the current resistor; the next revision raises the timer resistor (R16 47 k to 68 k, about 9 h nominal, 6.8 h minimum) so a full charge always completes. Until then a charge that stops short simply restarts when USB is re-plugged.
- Discharge: the cell's 2 A rating covers the board's worst all-on draw (about 1 A from an empty cell) and the fuse (1.5 A hold, 3 A trip) with margin.
- **The listing itself warns that the plug's polarity is not universal.** Before the first plug-in of each cell: hold the plug against the socket and check that the red wire sits at the + mark.

## The standard test cell specification (any seller)
Any cell that matches all of this is approved for the first boards:
- single-cell 3.7 V lithium-polymer pouch, **1000 to 1200 mAh**;
- **with its own protection board** (the listing says "protected", "with PCM" or "with protection circuit");
- **JST-PH 2.0 mm two-wire plug**;
- size **503450** (5 x 34 x 50 mm) or **603048** (6 x 30 x 48 mm).

Because sellers wire the plug both ways, the rule stands for **every new cell, every time**: hold the plug against the socket and check that the red wire sits at the **+** mark before plugging in. That check is the protection; there is no electronic guard.

## What to buy
- A single **LiPo pouch cell, 3.7 V, 1000 to 1200 mAh, WITH a protection board** (the listing says "protected", "with PCM" or "with protection circuit"). Sizes that fit a flat credit-card board: 503450 (5 x 34 x 50 mm) or 603048 (6 x 30 x 48 mm).
- With a **JST-PH 2.0 mm plug** (two wires, red and black). This is the plug most hobby cells come with.
- Rated for at least 0.5 C charging (1000 mAh cell: 500 mA). Nearly all pouch cells are; the cell's own listing is the authority.
- A battery whose own protection has tripped (it shows 0 V) may not wake on this board; charge it briefly on an ordinary single-cell charger first, then use it here.
- Cells with a third thermistor wire cannot be used on this board (the socket has two pins); a later spin may add that.

## Before plugging in, every time
0. **Unplug USB first.** With USB plugged in the socket's + pin is live at about 4.2 V from the charger even with no battery in it. So: USB out, swap the battery, USB back in.
1. Look at the socket's silkscreen: **+ RED WIRE** on pin 1, **-** on pin 2. Hold the plug next to it and check that the red wire goes to the + side. Cells from different sellers are wired both ways. **There is no electronic guard on this board** (decided after the audit: none can be made safe with a two-wire plug). A reversed cell puts a wrong-way voltage on the protection chip and the charger the instant the plug seats, and with USB connected the cell then drives current through the damaged chips, limited only by the cell's own protection board (the charger's limit does not apply in that loop). This check, and a protected cell from the approved listing, are the protection. Buy from the one approved listing below, which has its wire colours recorded.
2. Make sure the cell is not swollen, dented or warm.

## First power-ups, in order (with the expert on the line)
1. No cell, power switch off. Current-limited supply at 5.0 V, 100 mA limit, into the USB socket. Switch on. Read 3.3 V on the 3V3 test point and 1.1 V on the 1V1 test point.
2. Raise the limit to 500 mA. Hold BOOT, reset: the `RPI-RP2` drive appears. Flash MicroPython. Run the expert's load script and read the current.
3. Cell only (no USB): switch on, the board runs from the cell.
4. Cell and USB together: the charge LED comes on; the current into the USB socket stays under 500 mA.

## While charging
- Charge on a **non-flammable surface** (a ceramic plate, a metal tray), away from paper and fabric.
- **Never leave the first charges unattended.** Stop if the cell or the area around the charger chip gets warm to the touch.
- The board does not measure the cell's temperature with a two-wire cell. The cell's own protection board and the gentle 0.5 C charge rate are what protect it. That is the residual risk you accepted.
- A safety timer ends a charge after roughly 6 hours; it runs slower while the charger is throttling itself (hot, or the USB port is weak), so "about 6 hours" is not a hard stop. Do not rely on it instead of attention.

## What the charge current is
494 mA nominal with the resistor the board ships with (R14 = 1.8 kΩ). With USB the charger's total input is capped at 500 mA, board included, so a 1000 mAh or larger cell gets at most 0.50 C whatever the tolerances. For a 500 mAh cell the resistor must be 3.6 kΩ (247 mA nominal, up to 274 mA with chip spread and a 1 % resistor, so a hair over 0.5 C): say so before the boards are ordered, or use a 1000 mAh cell. With USB the charger's total input is capped at 500 mA, board included, so the cell can never get more than that.
