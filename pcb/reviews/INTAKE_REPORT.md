# Intake report: Phase 0

Written by the PCB maker worker. Honest summary of what was read, what was not, and how sure I am.

## What I read

In the repo: `docs/roles/PCB_MAKER.md`, `pcb/README.md`, `pcb/PLAN.md`, `pcb/INTAKE.md`, `docs/HARDWARE.md`, `hw/BOARD.md`, `hw/BUDGET.md`, `README.md`, `SETUP.md`, `CLAUDE.md`, `lib/lcd.py`, `lib/buttons.py`, `lib/clocks.py`, and the pin, SPI and PWM lines of `main_monolith.py`.

From the Waveshare reference folders (readable as text): the README of the 1.3" LCD HAT library, `Pico Micropython/lcd_lib.py`, the examples' top-level README, every sub-README, and the pin and bus setup lines of the example `.py` files (GPIO, PWM, ADC, UART, I2C, SPI LCD, XPT2046, Blink).

I did not read in full: the long image-conversion scripts, the ICM20948 and ws2812b examples, and the rest of the long `main_monolith.py` game code. They have no pin-map content that matters here.

## What I could not read, and why

The two PDFs in `pcb/refs/` (the RP2040-Plus documentation and the diagram and documentation). I tried once with the Read tool's `pages` parameter. It failed with: `pdftoppm is not installed`. No PDF tool is installed, and I was told not to install anything, so I did not work around it. **Nothing in my requirements comes from those PDFs.**

Important side note: the Waveshare example code under `Pico_MircoPython_Examples-main` is written for a plain Raspberry Pi Pico and a 3.5" LCD, not for the RP2040-Plus. Its pins (for example GPIO25 for the LED, LCD_RST on GPIO15) do **not** describe this project's board. I used it only as general context and said so.

## Confidence per section of `REQUIREMENTS.md`

| Section | Confidence | Why |
|---|---|---|
| 2. Verified hardware facts | High | Measured on the real board, with the script named |
| 3. GPIO used by the software | High | Matches `lib/`, `main_monolith.py`, the HAT library code and the 2026-10-04 measurement |
| 4. Other GPIO, free or reserved | Low | The repo only says what is used. Reserved pins on the Plus come from the schematic I cannot read |
| 5. Electrical requirements | Medium | SPI speed and inputs are verified. 3.3 V logic, crystal and BOOTSEL wiring are general RP2040 knowledge |
| 6. Screen module interface | High for what the code does; Low for the hardware behind it | Code is clear. The panel part number, backlight circuit and connector are unknown |
| 7. Mechanical | Very low | Nothing about dimensions, headers or part footprints is in the repo |
| 12. Candidate parts | Low by design | General knowledge, all unverified |
| 13. Facts still needed | n/a | List of gaps |

## Top risks for a first board

1. **No mechanical facts.** I do not know the header pitch, board outline or where the HAT sits. A wrong connector footprint means a board that cannot be used. Guard: paper print at 1:1, and read the PDFs.
2. **62.5 MHz SPI on a new layout.** The panel was clean at 62.5 MHz on Waveshare's wiring. A longer or noisier new layout may not be. There is a 24 MHz fallback (46 ms per frame, still playable), but check this early.
3. **The `clk_peri` fix and the firmware.** The 62.5 MHz speed depends on a register write that fits the Waveshare MicroPython build. A custom board may need a different MicroPython build or definition. Not verified.
4. **Flash and BOOTSEL wiring.** Wrong flash wiring or BOOTSEL circuit means no drag-and-drop and no recovery. Follow the official RP2040 design guide closely.
5. **The 16 MB flash size is only reported, not measured.** The probe could not tell 8 MB from 16 MB.
6. **Battery.** A lithium charger or protection mistake is a fire risk. Recommend leaving it off the first board.
7. **Part stock and footprints.** Typical first-board failure. Check each footprint against its datasheet and the fab's stock before ordering.
8. **Unknown reserved pins.** Free pins on the chip may be used on the Waveshare board for power or LED functions. Do not assume.
9. **Screen approach.** A bare panel has an unknown part number and unknown init values for a different panel.
10. **Licence.** The Waveshare HAT example repo has a `LICENSE` file I did not review. Do not copy code from it.

## Next steps for the owner

1. Install KiCad: `brew install --cask kicad`
2. Install a PDF tool so the PDFs can be read: `brew install poppler`
3. Ask the PM to continue the intake. The next pass will read both PDFs and fill sections 4, 5 and 7 of `REQUIREMENTS.md` and the "Facts still needed" list.
4. In the meantime, read and answer `pcb/OWNER_QUESTIONS.md`, starting with Question 1.
5. Optional: if you have a ruler or caliper, measure the RP2040-Plus and the HAT (outline, hole positions, header pitch) and write the numbers down.

The expert's open measurements (3.3 V rail under load, any LED pin) are listed in `REQUIREMENTS.md` section 13, group D.
