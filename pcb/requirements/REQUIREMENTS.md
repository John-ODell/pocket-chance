# Requirements: the new board

**Status: Phase 0 / Stage 1, written 2026-10-04 from the repo, the two Waveshare product-page PDFs in `pcb/refs/` (now readable), the HAT example code and the expert's answers in `pcb/reviews/ENGINEER_ANSWERS.md`. Nothing here is decided until the owner rules.** This is the sourced fact base. The beginner's version, grouped by kind of constraint, is `pcb/CONSTRAINTS.md`. The first decision (scope) is drafted as `pm/inbox/DR-033-board-scope.md` and parked until the owner opens Stage 2.

**How to read the labels**
- **Verified** = measured or confirmed on the real board, or stated by the owner. The source file is named.
- **Documented** = stated in a Waveshare product page or a datasheet. Page number given. Not measured by us.
- **Unverified** = a suspicion or general knowledge. It must be checked before it drives a design choice.

Paths are relative to the repo root. "Doc p.N" means `pcb/refs/RP2040-Plus_WaveShare_Documentation.pdf` page N (a printout of docs.waveshare.com/RP2040-Plus). "Shop p.N" means `pcb/refs/RP2040_Plus_Diagram_and_Documentation.pdf` page N (a printout of the waveshare.com product page). Neither PDF contains a schematic, so anything that only a schematic shows is still listed under "Facts still needed".

## 1. Goal

A custom dev board that does what the Waveshare RP2040-Plus plus the Waveshare Pico LCD 1.3" HAT do together, built around the same RP2040 chip, so the Pocket Chance MicroPython game runs unchanged except for what section 9 lists. Source: `pcb/README.md`, `pcb/PLAN.md`, `docs/roles/PCB_MAKER.md`, owner's starter prompt (2026-10-04: "RP2040 plus the screen, joystick and buttons").

Scope, screen approach, battery, form factor, assembly, budget and licence are **not decided**. They are the owner's first questions (`pcb/PLAN.md`, "Decisions the owner must make first"), asked one at a time.

## 2. Verified facts about the current hardware

| Item | Value | Status | Source |
|---|---|---|---|
| MCU | RP2040, two Cortex-M0+ cores, 264 KB SRAM | Verified | `docs/HARDWARE.md`, `hw/BUDGET.md` |
| CPU clock | 125 MHz (the MicroPython default on this build; the chip is rated to 133 MHz) | Verified | `hw/BOARD.md` (`machine.freq()`); Doc p.2 for 133 MHz |
| Flash | **16 MB by aliasing evidence**: a NOR flash ignores address bits above its size, so an 8 MB chip read at 8 MB would show the firmware again; reads at 8 MB and 15 MB came back erased, not mirrored. The JEDEC ID was not read. Waveshare names the part W25Q128JVSIQ | Verified (larger than 8 MB, expert 2026-10-04); Documented (part name) | `pcb/reviews/ENGINEER_ANSWERS.md` q3; `hw/BOARD.md`; Doc p.3 |
| Filesystem | LittleFS, 15,728,640 bytes, 4 KB blocks, on firmware v1.29.0 build `WAVESHARE_RP2040_PLUS-FLASH_16M` | Verified | `hw/BOARD.md`, `docs/HARDWARE.md` |
| Stock Pico firmware | Runs on the board but maps only 1.4 MB of flash | Verified | `docs/HARDWARE.md`, `hw/reviews/HR-F01.md` |
| USB IDs | VID:PID 2e8a:0005 (MicroPython in FS mode) | Verified | `hw/BOARD.md` |
| Firmware drop-in | UF2 file dragged onto the `RPI-RP2` drive after holding BOOT while plugging in | Verified (workflow in use) | `SETUP.md` Step 1 |
| Screen controller | ST7789, 240 x 240, RGB565, 1.3" IPS | Verified (init works on the real HAT) | `docs/HARDWARE.md`, `lib/lcd.py` |
| Screen bus | SPI1, mode 0 (polarity 0, phase 0), write only (`miso=None`) | Verified | `lib/lcd.py` |
| Pixel format | Big-endian RGB565, `0x3A = 0x05`, orientation `0x36 = 0x70`, inversion on (`0x21`) | Verified (owner read the test pattern) | `lib/lcd.py`, `hw/BOARD.md` |
| Full frame | 115,200 bytes, 17 to 18 ms at 62.5 MHz, 46 ms at 24 MHz | Verified | `hw/BUDGET.md` |
| Panel at 62.5 MHz | Clean: no speckles, tearing or wrong colours on the owner's eyeball check | Verified | `hw/BUDGET.md`, `hw/reviews/HR-015.md` (2026-10-04) |
| Buttons and joystick | Nine inputs, all idle high with pull-ups, no bounce seen at a 240 us sample period | Verified | `hw/BUDGET.md`, `hw/BOARD.md` |
| Backlight | PWM at 1 kHz, duty set with `duty_u16` (default level 20000 of 65535 in `lib/lcd.py`) | Verified (software behaviour) | `lib/lcd.py`, `main_monolith.py` |
| Free RAM | 222,720 bytes at boot; about 104 KB after the framebuffer; roughly 50 to 55 KB while playing | Verified | `hw/BUDGET.md`, `docs/HARDWARE.md` |
| ADC3 / GPIO29 | **Unconnected on the Plus.** It floats and reads the same leakage (about 0.6 V) as the other free ADC pins. There is no Pico-style VSYS divider | Verified, read-only (`hwtest/pins_reserved.py`, 2026-10-04) | `pcb/reviews/ENGINEER_ANSWERS.md` q2 and pin survey |
| GP24 | Held **high** on the board: VBUS sense, as on a Pico | Verified, read-only | `pcb/reviews/ENGINEER_ANSWERS.md` pin survey |
| GP23, GP25 | Float. No evidence of an LED on GP25 (a Pico has one there). The user LED's pin is still unknown; an output test needs a ruling | Verified (float), LED pin Unknown | `pcb/reviews/ENGINEER_ANSWERS.md` pin survey |
| Battery and charging | Not measured. Nothing on the charge circuit was touched | Not known | `hw/BUDGET.md` Power |
| 3.3 V rail under load, backlight current | Not measured | Not known | `hw/BUDGET.md`, `pcb/INTAKE.md` |

## 3. What the Waveshare board is made of (documented, from the product pages)

These are facts about parts and signals, not a drawing. They tell us what a working board of this kind contains. No layout was copied.

| Block | What Waveshare says | Source |
|---|---|---|
| Flash | 16 MB version: **W25Q128JVSIQ** (Winbond 128 Mbit QSPI NOR). 4 MB version: W25Q32JVSSIQ | Doc p.3 item 6; Shop p.10 item 6 |
| USB | USB Type-C connector, "USB 1.1 with device and host support", used for program download and power | Doc p.2, p.3 item 2; Shop p.4 |
| Battery charger | **ETA6096**, "high efficiency lithium battery recharge manager", single-cell 3.7 V | Doc p.3 item 3; Shop p.10 item 3 |
| Power converter | **MP28164**, "high efficiency DC-DC buck-boost chip, maximum 2 A load current" | Doc p.2, p.3 item 4; Shop p.4, p.10 item 4 |
| Battery connector | **MX1.25** header for a 3.7 V lithium battery; charging and powering the board at the same time | Doc p.3 item 9; Shop p.10 item 9 |
| Buttons on the board | **BOOT** ("press it when resetting to enter download mode") and **RESET** | Doc p.3 items 5, 7; Shop p.10 |
| LED | One **user LED, not a power indicator**. Which GPIO drives it is **not stated** | Doc p.3 item 1; Shop p.10 item 1 |
| Test points | USB test points (USB_N, USB_P) and a BOOT test point on the USB end; **SWDIO, GND, SWCLK** debug pads on the other end | Doc p.4 "Interfaces" drawing; Shop p.9 items 11 to 13 |
| Header | "Compatible with Raspberry Pi Pico": 2 x 20 castellated pins, Pico pin order (see section 4) | Doc p.3 item 10, p.4 drawing; Shop p.10 item 10 |
| Not on the board | No wireless, no crystal part number given, no regulator details beyond the MP28164 name | (absence in both PDFs) |
| Low power | "Low-power sleep and dormant modes" (an RP2040 feature, not a board feature) | Shop p.4 |

**What the product pages do not say** (needs the schematic, a datasheet or a measurement): the USB-C CC resistor values and any ESD part, the series resistors on D+ and D-, how BOOT and RESET are wired, whether the MP28164 feeds 3.3 V directly or a second regulator exists, the ETA6096 charge current setting, whether any battery protection exists beyond the charger, the crystal frequency and its load parts, the LED's GPIO, what GPIO29 and the 3V3_EN pin do on this board.

## 4. The Waveshare header pinout (documented)

From the "Interfaces" drawing, Doc p.4 (same drawing on Shop p.9 without labels). Pin numbers are the Pico's. **This is the Pico pinout** and matches what the game verified: everything the game uses is on these pins.

| Pin | Signal | Pin | Signal |
|---|---|---|---|
| 1 | GP0 | 40 | VBUS |
| 2 | GP1 | 39 | VSYS |
| 3 | GND | 38 | GND |
| 4 | GP2 | 37 | 3V3_EN |
| 5 | GP3 | 36 | 3V3 (OUT) |
| 6 | GP4 | 35 | ADC_VREF |
| 7 | GP5 | 34 | GP28 / ADC2 |
| 8 | GND | 33 | AGND |
| 9 | GP6 | 32 | GP27 / ADC1 |
| 10 | GP7 | 31 | GP26 / ADC0 |
| 11 | GP8 | 30 | RUN |
| 12 | GP9 | 29 | GP22 |
| 13 | GND | 28 | GND |
| 14 | GP10 | 27 | GP21 |
| 15 | GP11 | 26 | GP20 |
| 16 | GP12 | 25 | GP19 |
| 17 | GP13 | 24 | GP18 |
| 18 | GND | 23 | GND |
| 19 | GP14 | 22 | GP17 |
| 20 | GP15 | 21 | GP16 |

Extra pads (not header pins): USB_N, USB_P, BOOT at the USB end; SWDIO, GND, SWCLK at the far end (Doc p.4).

**Not on the header: GP23, GP24, GP25 and GP29.** On a Raspberry Pi Pico these are board-internal (power-save control, VBUS sense, user LED, VSYS sense). On the Plus they are also absent from the header (Doc p.4). The expert's read-only survey (`pcb/reviews/ENGINEER_ANSWERS.md`, 2026-10-04) found: GP24 held high (VBUS sense, like a Pico); GP23 and GP25 floating, so no LED on GP25; GP29 unconnected. **The user LED's GPIO is still unknown.** Finding it means driving GP23 or GP25 as an output while watching the LED, which needs a ruling because it is a write to the board. Candidates for the LED by elimination: GP23 or GP25, or a GPIO that is also on the header.

## 5. GPIO table: what the software uses

All nine inputs and six screen pins below are Verified on the real board (`hw/BOARD.md`, "Pin map: VERIFIED", 2026-10-04). They are the same in `lib/lcd.py`, `lib/buttons.py`, `main_monolith.py` and the HAT library `lcd_lib.py` (`Screen_Refernce/pico-waveshare-LCD/Pico Micropython/`, which uses BL 13, DC 8, RST 12, MOSI 11, SCK 10, CS 9).

| GPIO | Header pin | Function | Direction and setup | Source in code |
|---|---|---|---|---|
| 2 | 4 | Joystick up | Input, pull-up, active low | `lib/buttons.py` |
| 3 | 5 | Joystick press (centre) | Input, pull-up, active low | `lib/buttons.py` |
| 8 | 11 | LCD DC (data/command) | Output | `lib/lcd.py` (`DC`) |
| 9 | 12 | LCD CS | Output, idles high | `lib/lcd.py` (`CS`) |
| 10 | 14 | LCD SCK (SPI1 SCK) | SPI1 | `lib/lcd.py` (`SCK`) |
| 11 | 15 | LCD MOSI (SPI1 TX) | SPI1 | `lib/lcd.py` (`MOSI`) |
| 12 | 16 | LCD RST | Output, idles high; code pulses low 10 ms, waits 120 ms | `lib/lcd.py` (`RST`) |
| 13 | 17 | LCD backlight | PWM output, 1 kHz | `lib/lcd.py` (`BL`) |
| 15 | 20 | Button A | Input, pull-up, active low | `lib/buttons.py` |
| 16 | 21 | Joystick left | Input, pull-up, active low | `lib/buttons.py` |
| 17 | 22 | Button B | Input, pull-up, active low | `lib/buttons.py` |
| 18 | 24 | Joystick down | Input, pull-up, active low | `lib/buttons.py` |
| 19 | 25 | Button X | Input, pull-up, active low | `lib/buttons.py` |
| 20 | 26 | Joystick right | Input, pull-up, active low | `lib/buttons.py` |
| 21 | 27 | Button Y | Input, pull-up, active low | `lib/buttons.py` |

Notes:
- The header drawing labels GP10 as "SPI1 SCK" and GP11 as "SPI1 TX" (Doc p.4), which agrees with the code. GP12 is labelled "SPI1 RX" but the code uses it as a plain output (RST) and never reads MISO.
- The software depends only on the pin numbers, not on which physical button is which letter (`docs/HARDWARE.md`). The physical top-to-bottom order of A/B/X/Y is **not confirmed** (`hw/BOARD.md`).
- Software relies on the internal pull-ups. A new board needs no external pull-ups for the software to work; see section 8 about adding some anyway.
- The HAT also puts the four buttons and joystick on these pins. Whether the HAT itself has pull-ups, series resistors or capacitors on them is **Unverified** (no HAT schematic in hand).

## 6. GPIO table: everything else on the RP2040

| GPIO | Used by software? | What is known | Status |
|---|---|---|---|
| 0, 1 | No | On the header (pins 1, 2), labelled UART0 TX/RX by default | Documented (Doc p.4). Free for a debug UART |
| 4, 5, 6, 7 | No | On the header; GP4/GP5 labelled I2C0, GP6/GP7 I2C1 | Documented (Doc p.4). Free |
| 14 | No | On the header (pin 19) | Documented. Free |
| 22 | No | On the header (pin 29) | Documented. Free |
| 23, 25 | No | **Not on the header.** Both float on the Plus. One may drive the user LED (needs an output test and a ruling) | Verified float (`ENGINEER_ANSWERS.md`). Do not assume free |
| 24 | No | Not on the header. Held high: VBUS sense | Verified (`ENGINEER_ANSWERS.md`). Reserved on the Plus |
| 26, 27, 28 | No | On the header as ADC0 to ADC2 | Documented. Free; one would be needed for battery sensing |
| 29 | No | Not on the header. Unconnected on the Plus (floats like a free ADC pin) | Verified (`ENGINEER_ANSWERS.md`). Free on a new board |
| QSPI (flash) | n/a | Dedicated pins to the W25Q128JVSIQ | Documented (part), wiring Unverified |
| SWD | Not used | SWDIO / SWCLK pads exist on the Plus | Documented (Doc p.4) |
| USB D+/D- | n/a | Dedicated pins; USB_P / USB_N test points exist | Documented (Doc p.4) |

**A free pin on the chip is not automatically free on the new board.** The new board defines its own reservations.

## 7. Electrical facts the new board must satisfy

| # | Requirement | Status | Source / how to confirm |
|---|---|---|---|
| E1 | 3.3 V logic on all GPIO. The screen module and buttons are driven at 3.3 V | General RP2040 fact, Unverified in this repo | RP2040 datasheet (to fetch), screen module documentation |
| E2 | SPI1 to the screen must work at a real **62.5 MHz**. The panel was verified clean at this speed on the HAT wiring | Verified on the existing hardware | `hw/BUDGET.md`, `hw/reviews/HR-015.md`. A new layout must keep the SPI traces short with a ground return, or the clean result may not hold |
| E3 | Software fallback exists: 24 MHz SPI also works (46 ms per frame, 20 fps) | Verified | `hw/BUDGET.md` |
| E4 | The 125 MHz clock and the `clk_peri` fix (`lib/clocks.py`) depend on **MicroPython**, not on the board. A new board must run a MicroPython build whose board definition matches its flash size and pins | Verified for the Waveshare build; Unverified for a custom board | `lib/clocks.py`, `SETUP.md`, section 9 |
| E5 | USB-C with data lines, serial REPL via MicroPython, and BOOT drag-and-drop (the `RPI-RP2` drive appears when BOOT is held at plug-in) | Verified workflow | `SETUP.md` Step 1 |
| E6 | A BOOT button (holds the flash chip-select low at reset) must exist and be reachable. A RESET button is strongly wanted (the Plus has one; it avoids unplugging) | Required by the workflow; wiring Unverified | `SETUP.md`; Doc p.3 items 5, 7; RP2040 hardware design guide has the standard circuit |
| E7 | 16 MB QSPI flash so the 16 MB MicroPython build gives about 15 MB of filesystem. W25Q128JVSIQ is the part Waveshare uses and the part the Raspberry Pi reference design uses on the Pico | Documented (Doc p.3); Verified filesystem size | `hw/BOARD.md`, `SETUP.md` |
| E8 | A 12 MHz crystal (the RP2040 needs 12 MHz for USB) with the support parts from the hardware design guide | General RP2040 practice, Unverified in the PDFs (no crystal is named) | RP2040 hardware design guide (to fetch) |
| E9 | Nine inputs with the internal pull-up on the listed GPIO, active low, to ground when pressed | Verified | `lib/buttons.py`, `hw/BOARD.md` |
| E10 | Backlight on a PWM-capable pin (GPIO13), driven from the RP2040 | Verified in software | `lib/lcd.py`. Whether the HAT drives the backlight LED straight from the pin or through a transistor is Unverified; a bare panel needs its own check |
| E11 | Power budget: 3.3 V rail current with the screen on at full backlight | **Not measured** | Needs the expert (`pcb/INTAKE.md`). Rough expectation for an RP2040 plus a 1.3" backlight is well under 200 mA (Unverified estimate; measure it) |
| E12 | If a LiPo is on the board: a proven charger and protection part, a second opinion from the expert, and a current-limited first power-up | Required by the role file | `docs/roles/PCB_MAKER.md` rule 7. Waveshare's choice (ETA6096 charger, MP28164 buck-boost) is one proven combination to evaluate, not a decision |
| E13 | Power path: the Plus runs from USB 5 V or the battery, and charges while powered | Documented (Doc p.3 item 9) | A new board with a battery needs the same: USB present → charge and run; USB absent → run from the cell |

## 8. The screen module interface, as the code sees it

The code treats the screen as a fixed set of signals. A new board that keeps this contract keeps the software unchanged.

| Signal | Detail | Source |
|---|---|---|
| Interface | 4-wire SPI plus DC, write only | `lib/lcd.py` |
| Controller | ST7789 (init sequence in `_INIT` in `lib/lcd.py`, same as `main_monolith.py` and the HAT library) | `lib/lcd.py`, `lcd_lib.py` |
| Reset | Active low, hardware reset pulsed at start | `lib/lcd.py` |
| Chip select | Active low, toggled around every command and data block | `lib/lcd.py` |
| Window commands | `0x2A` column, `0x2B` row, `0x2C` memory write; partial window pushes are used for speed | `lib/lcd.py` |
| Display on / sleep out | `0x29`, `0x11` | `lib/lcd.py` |
| Inversion on | `0x21` (so the module is an IPS panel that needs inversion) | `lib/lcd.py` |
| Backlight | One control signal on GPIO13 (PWM) | `lib/lcd.py` |
| Resolution and offset | 240 x 240. No window offset is applied in code, so the module has no hidden RAM offset | `lib/lcd.py` (inference; Unverified for a different panel) |
| Colour | Big-endian RGB565 | `docs/HARDWARE.md` |
| Orientation | `0x36 = 0x70`; USB-C and joystick on the left of the landscape frame, buttons on the right | `docs/HARDWARE.md` |

If the owner replaces the Waveshare module with a bare panel: a different panel needs its own init values and possibly a window offset (the init above is tuned for this module, Unverified for others), and the panel's connector, backlight voltage and current, and rails are **not in the repo**.

Things to make a conscious choice about on the new board:
- **External pull-ups on buttons.** Not needed by the software. Optional for robustness (a 10 k pull-up and a small capacitor per input is cheap ESD and noise insurance; general practice, Unverified here).
- **Test points and SWD pads.** The Plus has them (Doc p.4). Cheap on a first board; the plan asks for them (`pcb/PLAN.md` phase 7).
- **A user LED and a RESET button.** Not used by the software, but both help bring-up: an LED is the first "is it alive" test, and RESET saves unplugging.

## 9. Mechanical facts

| Item | What is known | Status |
|---|---|---|
| Orientation of USB-C, joystick and buttons | USB-C and joystick on the left, buttons on the right, landscape | Verified (`docs/HARDWARE.md`) |
| Waveshare board outline | **21.00 x 51.00 mm**, USB-C on one short edge, battery connector on the other | Documented (Doc p.5, Shop p.13 dimension drawing) |
| Header | 2 x 20 castellated pins, **2.54 mm pitch**, rows **17.78 mm** apart (centre to centre), first pin 1.61 mm from the battery-end edge and 1.37 mm from the long edge | Documented (Doc p.5) |
| USB-C position | Connector body 8.95 mm wide, centred on the short edge (6.17 mm from the long edge to the connector) | Documented (Doc p.5) |
| HAT mounts on the board | "The HAT plugs onto the board" via the 2 x 20 header | Verified in use (`README.md`) |
| HAT outline, screen position, hole positions | Not in the repo and not in the PDFs | **Unknown. Needs a ruler, or the HAT's own documentation** |
| Screen module size, thickness, connector | Not in the repo | Unknown |
| Joystick and button part types and footprints | Not in the repo | Unknown. Needs the HAT documentation or a look at the physical parts |

## 10. Things that may differ on the new board (and should be conscious choices)

Listed in section 8's last block (pull-ups, test points, LED, RESET). Also: whether to keep the Pico header at all. If the board is a handheld with the screen and buttons on it, the header can shrink to the few pins worth exposing (UART, I2C, a couple of GPIO, power) or disappear.

## 11. Constraints from the software

- Any GPIO change means editing `lib/lcd.py` (pins at the top), `lib/buttons.py` (`PINS`), `docs/HARDWARE.md`, `hw/BOARD.md`. `main_monolith.py` is read-only and must not be edited (`CLAUDE.md`, rule 4). Source: `docs/roles/PCB_MAKER.md` rule 8. **Recommendation: keep every pin in section 5 exactly as it is.**
- `lib/lcd.py` requests `SPI(1, 62_500_000)`. With the `clk_peri` fix it really runs at 62.5 MHz on MicroPython v1.29.0. The fix is a raw register write and depends on that MicroPython build's clock setup (`lib/clocks.py`, `docs/HARDWARE.md`).
- Firmware: the owner flashes `WAVESHARE_RP2040_PLUS-FLASH_16M`. On a custom board with the **same flash part (W25Q128JVSIQ) and the same USB wiring**, that build should work as is, because a MicroPython board definition for the RP2040 is mostly "which flash size and which USB name" (Unverified; test on the first board). Fallback: the generic Raspberry Pi Pico build, which maps only 1.4 MB (`docs/HARDWARE.md`). A custom board definition is possible but out of scope for a first PCB.
- About 50 KB of free RAM while playing is a property of the code and MicroPython, not the board (`hw/BUDGET.md`).
- The game assumes a PWM-capable backlight pin. Every RP2040 GPIO can be a PWM output (general knowledge, Unverified in this repo; the header drawing labels all GP pins "GPIO, PIO, and PWM", Doc p.4).
- No network or radio is used (`CLAUDE.md`).

## 11a. Stage 2 wishes (owner, 2026-10-04, via the PM) and the resulting pin plan

The owner's wishes for the first custom board: one integrated handheld, more RAM, LiPo with charging and management, a power switch, a small speaker, wireless, a microSD slot, possibly a larger screen. The analysis and the staged proposal are in `pm/inbox/DR-033-board-scope.md` (expert review `hw/reviews/HR-033.md`). The pin plan that comes out of it, for an RP2350A, keeps every pin in section 5 and uses 29 of 30 GPIO:

| GPIO | Use | Status |
|---|---|---|
| 0 | PSRAM chip-select (XIP_CS1n; the only option not used by the game, the others being 8 and 19) | Documented, pico-sdk function table |
| 1 | UART0 RX on the expansion header (serial GPS listen-only), spare | plan |
| 2, 3, 16, 18, 20; 15, 17, 19, 21; 8 to 13 | joystick, buttons, screen, exactly as section 5 | Verified |
| 4, 6, 7, 5 | microSD over SPI0 (MISO, SCK, MOSI), chip-select; no card-detect | Documented pin functions; reviewed `hw/reviews/HR-P01.md` (fits) |
| 14 | IMU interrupt (wake on motion or step) | plan |
| 22 | speaker, PWM audio | plan |
| 23, 24, 25, 29 | RM2 wireless module, as the stock Pico 2 W firmware expects | Documented, pico-sdk `pico2_w.h` (HR-033) |
| 26, 27 | shared I2C1 bus: fuel gauge, RTC, IMU, STEMMA QT connector | plan |
| 28 | battery voltage divider, ADC2, on the expansion header (also the only free UART0 TX, if the divider gives way to the fuel gauge) | plan |

All 30 GPIO used. SWD uses dedicated pins. Full reasoning in DR-033 appendix I.

Requirement E14 (new): a microSD slot in SPI mode on the pins above, with pull-ups, a bulk capacitor for write bursts (up to about 200 mA, estimate), ESD protection and a push-push surface-mount slot the fab stocks. The card is bulk storage and file transfer only; the game, its modules and its saves stay in internal flash. Source: owner's wish via the PM; details in DR-033 appendix H; all electrical values Unverified until the datasheets are read.

Requirement E15 (new): a real-time clock that keeps time with the board off: DS3231-family I2C clock with a **non-rechargeable CR1220 coin cell** in a holder connected only to the clock's backup input, never to the 3.3 V rail or the LiPo charger. Source: owner's wish via the PM (D-012 discussion); DR-033 appendix I.2; part details Unverified until the datasheet is read.

Requirement E16 (new): a 6-axis IMU on the shared I2C bus with its interrupt on a GPIO, for step counting and wake-on-motion (candidate LSM6DSOX, official MicroPython driver in micropython-lib). A STEMMA QT / Qwiic I2C connector, an expansion header (GP1, GP28, I2C, 3.3 V, GND) and an SWD header for everything else (temperature, humidity, GPS). Source: owner's wish via the PM; DR-033 appendix I.3 and I.4.

## 11c. Fab constraints (PCBWay, chosen by the owner 2026-10-04; pages read the same day)

Documented from pcbway.com (capabilities, assembly capabilities, assembly file requirements): minimum trace and space 0.1 mm; drill 0.15 to 6.0 mm (extra cost under 0.2 mm); annular ring 0.15 mm; 1 to 14 layers; thickness 0.2 to 3.2 mm; finishes include HASL and ENIG; assembly minimum 5 boards; passives to 0201 (with a 100-piece minimum per 0201 line); fine pitch to 0.25 mm; QFN, castellated, through-hole and double-sided placement offered; **assembly boards smaller than 50 x 100 mm are panelised**; turnkey, consigned or combo parts; files: Gerber RS274X, BOM (CSV/Excel, manufacturer name and part number), centroid (designator, X, Y, rotation, side). Prices only on the quote page.

## 11b. Owner's direction on form factor and design base (2026-10-04, in chat)

- **Design base:** the official Raspberry Pi Pico W / Pico 2 W reference (schematics in `pcb/refs/pico-w-datasheet.pdf` and `pico-2-w-datasheet.pdf`, minimal designs in the two "Hardware design with ..." guides), not Waveshare's parts. Owner's choice.
- **Spin 1 form factor:** a flat, credit-card style board (about 85.6 x 54 mm as a starting size, Unverified by the owner) with screen, buttons, joystick and the other features on one board, nothing stacked. Purpose: learn what is really wanted, then shrink. Owner's choice.
- **Chip:** RP2350 if it works out better; the owner accepts the change. Decided in DR-033. Note: not a drop-in swap on the board (different package), so it is chosen before the schematic.
- **Licence of the reference material (read 2026-10-04 from the PDFs in `pcb/refs/`):** every Raspberry Pi document is **CC BY-ND 4.0** (attribution, no derivatives), so their drawings and text may be quoted with credit but not altered and republished; the Pico W and Pico 2 W datasheets say the source design files "are made available openly except for the antenna" (the antenna is licensed from ABRACON and must not be copied, which is one more reason the RM2 module is used instead); the "Hardware design with RP2040/RP2350" guides point to downloadable **minimal design examples in KiCad format** (RP2040 minimal, RP2350A minimal). The exact licence inside those KiCad zips is read when they are downloaded (a separate approval). Rule applied: the schematic is drawn by us from the datasheets and the guides' circuits; no Raspberry Pi drawing or layout file is copied into this repo.

## 12. Acceptance (what "done" means for the first board)

Still unconfirmed by the owner (source: `pcb/PLAN.md`).
1. Flashes with the 16 MB MicroPython build by BOOT drag-and-drop.
2. `mpremote run pocket.py` shows the menu with the correct colours and orientation.
3. All four buttons and the joystick work on the documented pins.
4. Runs 30 minutes of play on USB power without a reset.
5. If the board has a battery: charges and runs from the cell, with measured current within limits.

## 13. Candidates to evaluate (unverified)

These come from the Waveshare part names and general knowledge, **not from measurements**. None is chosen. Every one must be checked against its current datasheet, stock at the fab and the footprint before use.

| Block | Candidates | What to check |
|---|---|---|
| MCU | RP2040 | Datasheet, "Hardware design with RP2040" guide, stock at the fab |
| Flash | W25Q128JVSIQ (what the Plus and the Pico use) | Package (SOIC-8 208 mil), QSPI wiring per the design guide, fab stock |
| Crystal | 12 MHz, as in the design guide | Load capacitance, series resistor, layout advice |
| 3.3 V supply | Option 1: a plain 3.3 V LDO from USB 5 V (simplest, USB-only board). Option 2: MP28164 buck-boost (what the Plus uses; works from a LiPo whose voltage crosses 3.3 V) | Input range vs 5 V and a 3.0 to 4.2 V cell, output current, dropout, fab stock |
| USB-C connector | 16-pin USB-C receptacle (USB 2.0 pins only) | CC pull-downs (5.1 k each) for a device, ESD array, footprint, hand-solder vs assembly |
| LiPo charger (only if battery is chosen) | ETA6096 (what the Plus uses) or a similar single-cell linear charger | Charge current setting, thermal limits, whether it includes protection. **Needs the expert's second opinion** |
| Battery protection (only if battery is chosen) | A protected cell, or a protection IC | Required by the safety rule |
| Screen | The same Waveshare 1.3" module on a header, or a bare 1.3" 240 x 240 ST7789 IPS panel | Connector, backlight rail, init values, availability |
| Joystick and buttons | A 5-way tactile switch and four tactile buttons | Footprint, height vs the screen, fab stock |
| ESD protection | A USB ESD diode array | Capacitance, footprint |

## 14. Facts still needed

**Group A: only a schematic or a measurement can answer** (the Waveshare PDFs are product pages and do not show these).
1. USB-C wiring: CC resistors, series resistors on D+ and D-, ESD part.
2. How BOOT and RESET are wired (which signal, which resistor).
3. The power chain in detail: does the MP28164 produce 3.3 V directly; the ETA6096 charge current; any protection beyond the charger; what VSYS, 3V3_EN and RUN do on this board.
4. Which GPIO drives the user LED (GP24 is VBUS sense, GP29 is unconnected, GP23 and GP25 float: `pcb/reviews/ENGINEER_ANSWERS.md`). Only an output test or the schematic can finish this.
5. The crystal frequency and its load parts.
Plan: design these from the official RP2040 design guide and the part datasheets instead of from Waveshare's schematic. That is the correct route anyway (role file, rule 2).

**Group B: from the HAT** (its documentation page or a physical inspection).
6. How the backlight is switched, the screen connector, whether the buttons have pull-ups or capacitors.
7. The exact display panel part number and its datasheet (this decides whether a bare panel is possible).
8. Joystick and button parts, footprints and heights.
9. HAT outline, header position, screen position.

**Group C: from the owner.**
10. The decisions in `pcb/PLAN.md`: scope (DR-033), then screen approach, battery, form factor, assembly, budget and timeline, sharing.
11. A ruler or caliper measurement of the real board and HAT, or the 1:1 paper print test from `pcb/PLAN.md`.
12. Does the owner own a multimeter, a soldering iron, hot air, a bench supply? (Affects the assembly choice.)

**Group D: from the expert** (needs the real board, `pcb/INTAKE.md`).
13. 3.3 V rail under load with the backlight at full, and the current drawn from USB. The expert has a load script ready (`hwtest/load_hold.py`); it needs the owner at the 3V3 pin with a multimeter.
14. Which GPIO drives the user LED: drive GP23, then GP25, as an output and watch. Needs a ruling (it writes to the board).
15. ~~GP29~~ Answered 2026-10-04: unconnected (`pcb/reviews/ENGINEER_ANSWERS.md`).
16. Whether any test points or unused pins would help bring-up.

## 15. Licence and sharing notes

- The repo is public. This file records facts about signals and parts, not Waveshare drawings or layout. The two PDFs stay in `pcb/refs/` (git-ignored).
- `Screen_Refernce/pico-waveshare-LCD/` is a third-party repository (copyright 2021 Gopala Dhar, **MIT licence**, `LICENSE` file read 2026-10-04). Its `lcd_lib.py` was read only to confirm the pin numbers. Nothing from it is copied into this repo.
- `Screen_Refernce/Pico_MircoPython_Examples-main/` is Waveshare's tutorial code (README in Chinese). No licence file was seen in a quick look. Not copied.
- The licence for the owner's board design is an owner decision (open hardware or not). Not decided (question 7 in `pcb/PLAN.md`).
