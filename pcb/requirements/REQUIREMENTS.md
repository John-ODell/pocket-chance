# Requirements: the new board

**Status: Phase 0 draft, written from the repo and the readable Waveshare example code only.** Nothing here is decided until the owner rules. The two Waveshare PDFs in `pcb/refs/` could not be read (no PDF tool installed), so everything that would come from the board's schematic is listed under "Facts still needed" and marked unverified. See `pcb/reviews/INTAKE_REPORT.md`.

**How to read the labels**
- **Verified** = measured or confirmed on the real board, or stated by the owner. The source file is named.
- **Reported** = written in the repo but not measured (for example "from the box").
- **Unverified** = a suspicion or general knowledge. It must be checked before it drives a design choice.

Source files are all relative to the repo root.

## 1. Goal

A custom dev board that does what the Waveshare RP2040-Plus plus the Waveshare Pico LCD 1.3" HAT do together, built around the same RP2040 chip, so the Pocket Chance MicroPython game runs unchanged except for what section 9 lists. Source: `pcb/README.md`, `pcb/PLAN.md`, `docs/roles/PCB_MAKER.md`.

Scope, screen approach, battery, form factor, assembly, budget and licence are **not decided**. They are the owner's first questions (`pcb/OWNER_QUESTIONS.md`).

## 2. Verified facts about the current hardware

| Item | Value | Status | Source |
|---|---|---|---|
| MCU | RP2040, two Cortex-M0+ cores, 264 KB SRAM | Verified | `docs/HARDWARE.md`, `hw/BUDGET.md` |
| CPU clock | 125 MHz (the MicroPython default on this build) | Verified | `hw/BOARD.md` (`machine.freq()`) |
| Flash | Larger than 2 MB (reads at 2, 4, 8, 15 MB offsets return erased data and do not mirror). Exactly 16 MB is **reported** from the box, not distinguishable from 8 MB by the probe | Verified (more than 2 MB); Reported (16 MB) | `hw/BOARD.md` (`hwtest/flash_probe.py`) |
| Filesystem | LittleFS, 15,728,640 bytes, 4 KB blocks, on firmware v1.29.0 build `WAVESHARE_RP2040_PLUS-FLASH_16M` | Verified | `hw/BOARD.md`, `docs/HARDWARE.md` |
| Stock Pico firmware | Runs on the board but maps only 1.4 MB of flash | Verified | `docs/HARDWARE.md`, `hw/BOARD.md` |
| USB IDs | VID:PID 2e8a:0005 (MicroPython in FS mode) | Verified | `hw/BOARD.md` |
| Firmware drop-in | UF2 file dragged onto the `RPI-RP2` drive after holding BOOTSEL while plugging in | Verified (workflow in use) | `SETUP.md` Step 1 |
| Screen controller | ST7789, 240 x 240, RGB565, 1.3" IPS | Verified (init works on the real HAT) | `docs/HARDWARE.md`, `lib/lcd.py` |
| Screen bus | SPI1, mode 0 (polarity 0, phase 0), write only (`miso=None`) | Verified | `lib/lcd.py` |
| Pixel format | Big-endian RGB565, `0x3A = 0x05`, orientation `0x36 = 0x70`, inversion on (`0x21`) | Verified (owner read the test pattern) | `lib/lcd.py`, `hw/BOARD.md` |
| Full frame | 115,200 bytes, 17 to 18 ms at 62.5 MHz, 46 ms at 24 MHz | Verified | `hw/BUDGET.md` |
| Panel at 62.5 MHz | Clean: no speckles, tearing or wrong colours on the owner's eyeball check | Verified | `hw/BUDGET.md` (2026-10-04) |
| Buttons and joystick | Nine inputs, all idle high with pull-ups, no bounce seen at a 240 us sample period | Verified | `hw/BUDGET.md`, `hw/BOARD.md` |
| Backlight | PWM at 1 kHz, duty set with `duty_u16` (default level 20000 of 65535 in `lib/lcd.py`) | Verified (software behaviour) | `lib/lcd.py`, `main_monolith.py` |
| Free RAM | 222,720 bytes at boot; about 104 KB after the framebuffer; roughly 50 to 55 KB while playing | Verified | `hw/BUDGET.md`, `docs/HARDWARE.md` |
| ADC3 / GPIO29 | Reads 1.17 V after a Pico-style x3 divider, so it is probably **not** wired to VSYS on this board | Verified reading, Unverified interpretation | `hw/BOARD.md`, `hw/BUDGET.md` |
| Battery and charging | Not measured. Nothing on the charge circuit was touched | Not known | `hw/BUDGET.md` Power |
| 3.3 V rail under load, backlight current | Not measured | Not known | `hw/BUDGET.md`, `pcb/INTAKE.md` |

## 3. GPIO table: what the software uses

All nine inputs and six screen pins below are Verified on the real board (`hw/BOARD.md`, "Pin map: VERIFIED", 2026-10-04). They are the same in `lib/lcd.py`, `lib/buttons.py`, `main_monolith.py` and the Waveshare HAT example `lcd_lib.py`.

| GPIO | Function | Direction and setup | Source in code |
|---|---|---|---|
| 2 | Joystick up | Input, pull-up, active low | `lib/buttons.py` |
| 3 | Joystick press (centre) | Input, pull-up, active low | `lib/buttons.py` |
| 8 | LCD DC (data/command) | Output | `lib/lcd.py` (`DC`) |
| 9 | LCD CS | Output, idles high | `lib/lcd.py` (`CS`) |
| 10 | LCD SCK (SPI1 SCK) | SPI1 | `lib/lcd.py` (`SCK`) |
| 11 | LCD MOSI (SPI1 TX) | SPI1 | `lib/lcd.py` (`MOSI`) |
| 12 | LCD RST | Output, idles high; code pulses low 10 ms, waits 120 ms | `lib/lcd.py` (`RST`) |
| 13 | LCD backlight | PWM output, 1 kHz | `lib/lcd.py` (`BL`) |
| 15 | Button A | Input, pull-up, active low | `lib/buttons.py` |
| 16 | Joystick left | Input, pull-up, active low | `lib/buttons.py` |
| 17 | Button B | Input, pull-up, active low | `lib/buttons.py` |
| 18 | Joystick down | Input, pull-up, active low | `lib/buttons.py` |
| 19 | Button X | Input, pull-up, active low | `lib/buttons.py` |
| 20 | Joystick right | Input, pull-up, active low | `lib/buttons.py` |
| 21 | Button Y | Input, pull-up, active low | `lib/buttons.py` |

Notes on the table:
- SPI1 on the RP2040 can use GPIO 10 as SCK and GPIO 11 as TX. That is why the screen sits on these pins. This is general RP2040 knowledge, **unverified in this repo**; confirm in the RP2040 datasheet GPIO function table before committing to any change.
- MISO is not used (`miso=None`). GPIO12 is therefore not a SPI1 pin in this design; it is a plain GPIO used as RST.
- The software depends only on the pin numbers, not on which physical button is which letter (`docs/HARDWARE.md`). The physical top-to-bottom order of A/B/X/Y is **not confirmed** (`hw/BOARD.md`).
- Software relies on the internal pull-ups. A new board needs no external pull-ups for the software to work, but see section 8 about whether to add some.

## 4. GPIO table: everything else on the RP2040

Which pins are free is only known from the repo for the pins listed in section 3 (used). The rest is what the **chip** offers. Whether the **Waveshare board** reserves any of them is **unknown** until the schematic is read.

| GPIO | Used by software? | What the repo knows | What is only suspected (unverified) |
|---|---|---|---|
| 0, 1 | No | Nothing. The Waveshare generic example uses them as UART0 TX/RX on a plain Pico (`Pico_MircoPython_Examples-main/05_UART/UART.py`) | Probably free on the Plus. Common choice for a debug UART |
| 4, 5, 6, 7 | No | The generic example uses 6 and 7 for I2C1 (`06_I2C/I2C_TEST/I2C_TEST.py`) | Probably free. Candidate I2C or extras |
| 14 | No | Nothing | Probably free |
| 22 | No | Nothing | Probably free |
| 23, 24 | No | Nothing | On a standard Raspberry Pi Pico these are internal to the board (power-save and VBUS sense). The Plus may differ. Do not assume free |
| 25 | No | Generic examples blink the LED on GPIO25 (`01_Blink/Blink.py`). Those examples are written for a plain Pico, not the Plus | On a Pico, GPIO25 is the user LED. The Plus may use another pin or an RGB/other LED. Unknown |
| 26, 27, 28 | No | ADC0 to ADC2 on the RP2040. The generic example reads GPIO26 (`04_ADC/ADC.py`) | Probably free; would be needed for battery sensing if the owner wants it |
| 29 | No | Reads 1.17 V on ADC3 through the assumed Pico divider (`hw/BOARD.md`) | On a Pico this senses VSYS. On the Plus it appears not to. Unknown what it is wired to |
| QSPI pins (flash) | n/a | Flash works and holds 15 MB for the filesystem | These are dedicated pins, not GPIO 0 to 29 |
| SWD (debug) | Not used | Nothing | The RP2040 has dedicated SWCLK/SWD pins. Whether the Plus exposes them is unknown |
| USB D+/D- | n/a | USB works (serial and BOOTSEL) | Dedicated pins |

Reserved by this design for sure: nothing beyond section 3. **A free pin on the chip is not automatically free on the new board.** The new board will define its own reservations.

## 5. Electrical facts the new board must satisfy

| # | Requirement | Status | Source / how to confirm |
|---|---|---|---|
| E1 | 3.3 V logic on all GPIO. The screen module and buttons are driven at 3.3 V | Unverified. The previous draft of this file said "3.3 V logic" citing `docs/HARDWARE.md`, but that file does not state it. It is true of the RP2040 in general | Confirm in the RP2040 datasheet and the screen module's documentation |
| E2 | SPI1 to the screen must work at a real **62.5 MHz** (125 MHz system clock divided by 2). The panel was verified clean at this speed on the Waveshare HAT wiring | Verified on the existing hardware | `hw/BUDGET.md`. A new layout must keep the SPI traces short, with a ground return, or the clean result may not hold. This is a risk, see the report |
| E3 | Software fallback exists: 24 MHz SPI also works (46 ms per frame, 20 fps) | Verified | `hw/BUDGET.md` |
| E4 | The 125 MHz clock and the `clk_peri` fix (`lib/clocks.py`) depend on **MicroPython**, not on the board. A new board must run a MicroPython build whose board definition matches its flash size and pins | Verified for the Waveshare build; Unverified for a custom board | `lib/clocks.py`, `SETUP.md`. See section 9 |
| E5 | USB-C with data lines, serial REPL via MicroPython, and BOOTSEL drag-and-drop (the `RPI-RP2` drive appears when BOOTSEL is held at plug-in) | Verified workflow | `SETUP.md` Step 1 |
| E6 | A BOOTSEL button (or an equivalent that holds the flash chip-select low at reset) must exist and be reachable | Required by the workflow; wiring Unverified | `SETUP.md`. RP2040 hardware design guide has the standard circuit |
| E7 | 16 MB QSPI flash, so the 16 MB MicroPython build gives about 15 MB of filesystem | Reported | `hw/BOARD.md`, `SETUP.md` |
| E8 | A crystal-based clock. The RP2040 needs a crystal or external clock for USB | Unverified for the Waveshare board; general RP2040 practice | Waveshare schematic, RP2040 hardware design guide |
| E9 | Nine inputs with the internal pull-up on the listed GPIO, active low, to ground when pressed | Verified | `lib/buttons.py`, `hw/BOARD.md` |
| E10 | Backlight on a PWM-capable pin, driven from the RP2040 output | Verified in software | `lib/lcd.py`. Whether the Waveshare HAT drives the backlight directly from the pin or through a transistor is Unverified. Any other screen needs its own check |
| E11 | Power budget: 3.3 V rail current with the screen on at full backlight | **Not measured** | Needs the expert (`pcb/INTAKE.md`, questions for the expert) |
| E12 | If a LiPo is on the board: a proven charger and protection part, a second opinion, and a current-limited first power-up | Required by the role file | `docs/roles/PCB_MAKER.md` rule 7 |

## 6. The screen module interface, as the code sees it

The code treats the screen as a fixed set of signals. A new board that keeps this contract keeps the software unchanged.

| Signal | Detail | Source |
|---|---|---|
| Interface | 4-wire SPI plus DC, write only | `lib/lcd.py` |
| Controller | ST7789 (init sequence in `_INIT` in `lib/lcd.py`, same as `main_monolith.py`) | `lib/lcd.py` |
| Reset | Active low, hardware reset pulsed at start | `lib/lcd.py` |
| Chip select | Active low, toggled around every command and data block | `lib/lcd.py` |
| Window commands | `0x2A` column, `0x2B` row, `0x2C` memory write; partial window pushes are used for speed | `lib/lcd.py` |
| Display on / sleep out | `0x29`, `0x11` | `lib/lcd.py` |
| Inversion on | `0x21` (so the module is an IPS panel that needs inversion) | `lib/lcd.py` |
| Panel power, backlight | One backlight control signal on GPIO13 (PWM) | `lib/lcd.py` |
| Resolution and offset | 240 x 240. No window offset is applied in code, so the module has no hidden RAM offset | `lib/lcd.py` (inference from absence of an offset; Unverified for a different panel) |
| Colour | Big-endian RGB565 | `docs/HARDWARE.md` |
| Orientation | `0x36 = 0x70`; USB-C and joystick on the left of the landscape frame, buttons on the right | `docs/HARDWARE.md` |

Two things to watch if the owner replaces the Waveshare module with a bare panel (see section 10):
- A different panel needs its **own** init values and possibly a window offset. Tony Goodhew's init in `main_monolith.py` is tuned for the Waveshare module, not for every ST7789 panel (Unverified).
- The panel's own connector, backlight circuit (voltage and current) and voltage rails are **not in the repo**.

## 7. Mechanical facts

Almost none are known. This is a gap.

| Item | What is known | Status |
|---|---|---|
| Orientation of USB-C, joystick and buttons | USB-C and joystick on the left, buttons on the right, landscape | Verified (`docs/HARDWARE.md`) |
| HAT mounts on the board | "The HAT plugs onto the board" | Reported (`docs/HARDWARE.md`, `README.md`) |
| Board and HAT dimensions, header pitch, header position, hole positions | Not in the repo | **Unknown. Needs the PDFs, the Waveshare documents or a ruler** |
| Header type | Probably 2 x 20 pin, 2.54 mm, Pico style | **Unverified** |
| Screen module size, thickness, connector | Not in the repo | Unknown |
| Joystick and button part types and footprints | Not in the repo | Unknown. Needs the HAT documentation or an inspection of the physical parts |

## 8. Things that may differ on the new board (and should be a conscious choice)

- **External pull-ups on buttons.** Software uses internal pull-ups and no bounce was measured. A small capacitor per button is optional for ESD, not for bounce. Unverified whether the Waveshare HAT has any (`INTAKE.md` item to read).
- **Test points and a debug header.** Cheap on a first board. The role file asks for test points (`pcb/PLAN.md` phase 7).
- **A user LED and a reset button.** Not used by the software. Whether the Waveshare board has them is unknown.

## 9. Constraints from the software

- Any GPIO change means editing `lib/lcd.py` (pins at the top), `lib/buttons.py` (`PINS`), `docs/HARDWARE.md`, `hw/BOARD.md`, and probably `pm`/ruling notes. `main_monolith.py` is read-only and must not be edited (`CLAUDE.md`, rule 4). Source: `docs/roles/PCB_MAKER.md` rule 8.
- `lib/lcd.py` requests `SPI(1, 62_500_000)`. With the `clk_peri` fix from `lib/clocks.py` it really runs at 62.5 MHz on MicroPython v1.29.0. This fix is a raw register write and **depends on the clock layout of that MicroPython build**. A different build, a custom board definition, or a different MicroPython version could behave differently (`lib/clocks.py` comments, `docs/HARDWARE.md`).
- The firmware: the owner currently flashes `WAVESHARE_RP2040_PLUS-FLASH_16M`. On a custom board the same file may work if the flash type and USB behaviour match, or may not. Unknown. Fallback: the generic Raspberry Pi Pico build, but it maps only 1.4 MB (`docs/HARDWARE.md`). Building a custom MicroPython board definition is possible but out of scope for a first PCB (Unverified).
- About 50 KB of free RAM while playing is a property of the code and MicroPython, not the board (`hw/BUDGET.md`).
- The game assumes a PWM-capable backlight pin. Any GPIO works as PWM on the RP2040 (general knowledge, Unverified in this repo).
- No network or radio is used. The RP2040-Plus does not need a wireless part (`CLAUDE.md`).

## 10. Open decisions (owner, see `pcb/OWNER_QUESTIONS.md`)

Scope, screen approach, battery, form factor, assembly, budget and timeline, sharing and licence. Source: `pcb/PLAN.md`.

## 11. Acceptance (what "done" means for the first board)

Unchanged from the earlier draft and still unconfirmed by the owner (source: previous `REQUIREMENTS.md`, `pcb/PLAN.md`).
1. Flashes with the 16 MB MicroPython build by BOOTSEL drag-and-drop.
2. `mpremote run pocket.py` shows the menu with the correct colours and orientation.
3. All four buttons and the joystick work on the documented pins.
4. Runs 30 minutes of play on USB power without a reset.
5. If the board has a battery: charges and runs from the cell, with measured current within limits.

## 12. Candidates to evaluate (unverified)

These come from general knowledge, **not from the repo**. None is chosen. Every one must be checked against its current datasheet, stock at the fab and the footprint before use. No voltage, current or pin number below should be trusted.

| Block | Candidate families to look at | What to check |
|---|---|---|
| MCU | RP2040 (the chip itself) | Datasheet, "Hardware design with RP2040" guide, stock at the fab |
| Flash | A 16 MB (128 Mbit) QSPI NOR flash from a major maker (the Raspberry Pi design guide and many RP2040 boards use Winbond-class parts) | Exact part, package, the boot behaviour the RP2040 expects, fab stock |
| Crystal | A 12 MHz crystal is the usual RP2040 choice | Load capacitance, series resistor, layout advice in the hardware design guide |
| 3.3 V regulator | A small low-dropout or buck-boost regulator (what the Waveshare board uses is in the PDFs, not yet read) | Input range vs USB 5 V and LiPo, current for screen backlight, dropout, fab stock |
| USB-C connector | A 16-pin USB-C receptacle for power and data | CC resistor values for a USB device, ESD diode, footprint match, hand-solder vs assembly |
| LiPo charger (only if battery is chosen) | A single-cell linear charger from a known family | Charge current, protection, thermal limits. **Needs the expert's second opinion** |
| Battery protection (only if battery is chosen) | A protected cell or a protection IC | Required by the safety rule in the role file |
| Screen | The same Waveshare module on a header, or a bare 1.3" 240 x 240 ST7789 IPS panel | Connector, backlight rail, init values, availability |
| Joystick and buttons | A 5-way tactile switch and four tactile buttons | Footprint, height vs the screen, fab stock |
| ESD protection | A USB ESD diode array | Capacitance, footprint |

## 13. Facts still needed from the PDFs or the owner

Group A: from the Waveshare PDFs (`pcb/refs/`) once a PDF tool exists. Record each with a page number. Facts about **signals** only. Do not copy drawings or layout.
1. Flash part number and size, how it is wired to the RP2040 QSPI pins.
2. How BOOTSEL is wired (button to which signal, any resistor).
3. USB-C wiring: CC resistors, series resistors on D+ and D-, ESD part.
4. Power chain: regulator or buck-boost part, input range, output current, battery charger part, LiPo connector, any protection.
5. Which RP2040 pin goes to which header pin (full pin map for the board).
6. Which RP2040 pins the board reserves (LED, battery sense, power control, anything else).
7. The clock source: crystal frequency and its support parts.
8. Indicator LEDs, buttons beyond BOOTSEL (reset button?), test points.
9. Board outline, hole positions, header pitch and position, USB-C position (mechanical).
10. Whether GPIO23, 24, 25 and 29 are used on the Plus and for what.

Group B: from the Waveshare HAT (documents or physical inspection).
11. The HAT's schematic page: how the backlight is switched, the screen connector, whether the buttons have pull-ups or capacitors.
12. The exact display panel part number and its datasheet (this decides whether a bare panel is possible).
13. Joystick and button parts, footprints and heights.
14. HAT outline and header position.

Group C: from the owner.
15. The answers in `pcb/OWNER_QUESTIONS.md`: scope, screen approach, battery, form factor, assembly, budget, sharing.
16. A ruler or caliper measurement of the real board and HAT, or the 1:1 paper print test from `pcb/PLAN.md`.
17. Does the owner already own a multimeter, a soldering iron, hot air, a bench supply? (Affects the assembly choice.)

Group D: from the expert (needs the real board, `pcb/INTAKE.md`).
18. 3.3 V rail under load with the backlight at full.
19. Battery behaviour only if the owner agrees to a supervised test.
20. Whether the bare Waveshare board's GPIO25 or any other pin drives an LED.

## 14. Licence and sharing notes

- The repo is public. This file records facts about signals and parts, not Waveshare drawings or layout.
- The Waveshare HAT examples that were read are published by a third party under a repository `LICENSE` file (`Screen_Refernce/pico-waveshare-LCD/LICENSE`). The licence was not reviewed in this phase. Do not copy that code into the repo until it is reviewed.
- The licence for the owner's board design is an owner decision (open hardware or not). Not decided.
