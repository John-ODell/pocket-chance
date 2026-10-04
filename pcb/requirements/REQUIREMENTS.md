# Requirements: the new board

**Status: draft. Nothing here is decided until the owner rules.** Every line needs a source: a measured value in `hw/`, a datasheet page, or "owner's choice". The PCB maker fills this in and keeps it current.

## Goal
A custom dev board that runs the Pocket Chance game as the current Waveshare RP2040-Plus plus 1.3" LCD HAT do, so the software in this repo keeps working with no change except what this file lists.

## What we already know (verified on the real board, see `docs/HARDWARE.md`)

| Item | Value | Source |
|---|---|---|
| MCU | RP2040 (two Cortex-M0+, 264 KB RAM) | `docs/HARDWARE.md` |
| Flash | 16 MB QSPI, runs MicroPython v1.29.0 with 15 MB of filesystem | `hw/BOARD.md` |
| Screen | ST7789, 240 x 240, 16-bit colour, on SPI1, big-endian RGB565, init `0x36 = 0x70`, `0x3A = 0x05` | `docs/HARDWARE.md` |
| Screen pins | DC 8, CS 9, SCK 10, MOSI 11, RST 12, backlight 13 (PWM) | `docs/HARDWARE.md` |
| Buttons A / B / X / Y | GPIO 15 / 17 / 19 / 21, active low, internal pull-ups | `docs/HARDWARE.md` |
| Joystick up / down / left / right / press | GPIO 2 / 18 / 16 / 20 / 3, active low, internal pull-ups | `docs/HARDWARE.md` |
| SPI speed needed | 62.5 MHz for a full frame in 17 ms (24 MHz also works, slower) | `hw/BUDGET.md` |
| USB | USB-C, drag-and-drop BOOTSEL mode must work | `SETUP.md` |
| Power | 3.3 V logic. Battery via LiPo header on the current board | `docs/HARDWARE.md` |

## Open: the owner decides (see `pcb/PLAN.md`)
Scope, screen approach, battery, form factor, assembly, budget, licence.

## To extract from the manufacturer documents (see `pcb/INTAKE.md`)
Flash part and wiring, BOOTSEL wiring, USB-C wiring, power chain and part numbers, header pin assignments, reserved pins, clock source, indicator LEDs, test points. Each with its page number. Facts about signals only. Do not copy their drawing or layout.

## Constraints from the software
- If any GPIO assignment changes, list the files that change (`lib/lcd.py`, `lib/buttons.py`, `docs/HARDWARE.md`).
- The software needs about 50 KB of free RAM while playing. That is a property of MicroPython and the code, not of the board.
- The game assumes the screen's backlight is on a PWM-capable pin.

## Acceptance (what "done" means for the first board)
1. Flashes with the 16 MB MicroPython build by BOOTSEL drag-and-drop.
2. `mpremote run pocket.py` shows the menu with the correct colours and orientation.
3. All four buttons and the joystick work on the documented pins.
4. Runs 30 minutes of play on USB power without a reset.
5. If the board has a battery: charges and runs from the cell, with measured current within limits.
