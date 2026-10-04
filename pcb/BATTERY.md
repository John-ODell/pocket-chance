# Battery: what to buy and how to be safe (spin 1)

Written for John, 2026-10-04. The decisions behind it are in `pm/inbox/PCB-001-battery-and-power-path.md` and the audit response in `pcb/reviews/AUDIT-2-RESPONSE.md`.

## What to buy
- A single **LiPo pouch cell, 3.7 V, 1000 to 1200 mAh, WITH a protection board** (the listing says "protected", "with PCM" or "with protection circuit"). Sizes that fit a flat credit-card board: 503450 (5 x 34 x 50 mm) or 603048 (6 x 30 x 48 mm).
- With a **JST-PH 2.0 mm plug** (two wires, red and black). This is the plug most hobby cells come with.
- Rated for at least 0.5 C charging (1000 mAh cell: 500 mA). Nearly all pouch cells are; the cell's own listing is the authority.
- Optional, better: a cell with a **third wire, a thermistor**. It plugs into pin 3 of the board's socket and lets the charger stop when the cell is too hot or too cold. If you fit one, the resistor R12 is removed (tell the PCB maker).

## Before plugging in, every time
1. Look at the socket's silkscreen: **+ RED** on pin 1, **-** on pin 2. Hold the plug next to it and check that the red wire goes to the + side. Cells from different sellers are wired both ways; a reversed cell does nothing on this board thanks to the guard transistor, but check anyway.
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
- Charging stops by itself after about 6 hours whatever happens (safety timer).

## What the charge current is
494 mA with the resistor the board ships with (R14 = 1.8 kΩ), which is 0.49 C for a 1000 mAh cell. For a 500 mAh cell the resistor must be 3.6 kΩ (247 mA): say so before the boards are ordered, or do not use a smaller cell.
