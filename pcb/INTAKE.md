# Intake: what to read before designing

The PCB maker reads these in order. Items marked **local** are on the owner's computer and are not in the repository (they are copyrighted or large). Put copies in `pcb/refs/`, which git ignores.

## In this repository (read these first)

| File | Why |
|---|---|
| `docs/HARDWARE.md` | The verified pin map, screen settings, colour order, clock trap, memory and flash numbers. Proven on a real board |
| `hw/BOARD.md` | What the expert measured on the actual board, with how it was verified |
| `hw/BUDGET.md` | Frame rate, RAM and flash budget. Tells you how much headroom a new board has to give |
| `hw/reviews/` | The expert's reviews and findings (for example the 24 MHz SPI finding and the firmware size finding) |
| `README.md` | What the game is and what the board has to run |
| `SETUP.md` | How the current board is flashed and used. The new board should keep this workflow |
| `main_monolith.py` | The original driver code that talks to the screen (the ST7789 init sequence is in here) |
| `lib/lcd.py`, `lib/buttons.py`, `lib/clocks.py` | The code that depends on the pin map and clocks |

## Local manufacturer documents (the owner has these)

| Where on the owner's computer | What it is |
|---|---|
| `Pico_Reference/RP2040-Plus_WaveShare_Documentation.pdf` | Waveshare's product description for the RP2040-Plus (6 pages) |
| `Pico_Reference/RP2040_Plus_Diagram_and_Documentation.pdf` | Waveshare's diagram and documentation for the board (12 pages) |
| `Screen_Refernce/pico-waveshare-LCD/` | Waveshare's 1.3" LCD HAT library and example code |
| `Screen_Refernce/Pico_MircoPython_Examples-main/` | Waveshare's MicroPython examples (GPIO, SPI, I2C, PWM, PIO and more) |

The PDFs were not readable from the earlier sessions (no PDF tool was installed). Install a PDF reader tool for this session, or ask the owner to export the schematic page as an image.

## To fetch (public, free)

Record each download's URL and date in `pcb/refs/SOURCES.md`.

- Raspberry Pi **RP2040 datasheet** and **Hardware design with RP2040** guide (the official minimal design, with the required support parts and layout advice)
- The **ST7789** controller datasheet and the **display panel** datasheet (find the exact panel part number from the Waveshare documentation or the module)
- Datasheets for the chosen **flash chip**, **regulator or buck-boost**, **LiPo charger**, **USB-C connector**, **crystal**, and **ESD protection**
- The chosen fab's **capabilities page** (minimum trace and space, minimum drill, board sizes, layer options) and its **assembly requirements** (BOM and pick-and-place formats)
- The KiCad documentation for the installed version

## What to extract from the Waveshare board

Reading their schematic tells you what a working design of this kind contains. Note these facts, each with the page it came from:

1. How the flash is wired (size, interface) and how BOOTSEL is wired.
2. How USB-C is wired (CC resistors, ESD, series resistors on D+ and D-).
3. How power is made: buck-boost chip and its part number, the battery charger, the LiPo connector and any protection.
4. Which RP2040 pins go to which header pins.
5. Which pins are not available because the board uses them.
6. The clock source and its support parts.
7. Any indicator LEDs or test points.

Write these as **facts about signals** in `pcb/requirements/REQUIREMENTS.md`. Do not copy the drawing or the layout.

## Questions for the expert (the microcontroller expert has the board)

Ask the PM to route these to the expert, who can measure on the real board:
- Actual 3.3 V rail voltage under load while the screen is on at full backlight.
- Battery input behaviour, if the owner agrees to a supervised test.
- Which GPIO pins the board uses for the on-board LED and for battery sensing, if any.
- Whether any test points or unused pins would help bring-up.
