# Constraints: what the new board has to live with

Written 2026-10-04 by the PCB maker, for a first-time board designer. Stage 1: understand only. Nothing here is a design choice.

Every line says where it comes from and how sure we are:
- **Verified**: measured on the real board, or you told us.
- **Documented**: Waveshare's product page says it. Not measured by us.
- **Unverified**: general knowledge or a guess. Must be checked before it drives a choice.

The long version with every number and source is [`requirements/REQUIREMENTS.md`](requirements/REQUIREMENTS.md). This file is the plain-language summary.

## 1. What we have today

Two boards stacked. The **Waveshare RP2040-Plus** is the brain: the RP2040 chip, a 16 MB memory chip for your files, a USB-C socket, a battery socket and charger, a boot button and a reset button. The **Waveshare Pico LCD 1.3" HAT** sits on top of it: a 240 x 240 colour screen, a five-way joystick and four buttons. The HAT plugs onto the brain's 40 pins. (Verified in daily use, `README.md`.)

The game is MicroPython code that talks to the screen over a fast serial link called SPI, and reads nine switches (joystick up, down, left, right, press, buttons A, B, X, Y). (Verified, `docs/HARDWARE.md`.)

## 2. Electrical constraints

| Constraint | Why | Status |
|---|---|---|
| The chip must be an **RP2040** | The whole game is written for it and tuned to its speed and memory | Verified, the project's premise |
| The memory chip must be a **16 MB QSPI flash**. Waveshare uses a W25Q128JVSIQ | The 16 MB MicroPython build expects it and gives 15 MB of file space. The Plus's chip is bigger than 8 MB by evidence | Documented part; size Verified by the expert |
| Every chip runs at **3.3 V**; USB gives 5 V, so the board needs a part that turns 5 V into 3.3 V | The RP2040, flash and screen are 3.3 V parts | General RP2040 fact, Unverified in this repo |
| The screen link (SPI1) must run cleanly at **62.5 MHz** | That gives 58 frames a second. At 24 MHz the game still works at 20 frames a second | Verified on the HAT wiring. A new board's wiring may be worse: short traces, next to a ground return |
| Nine inputs must be **switches to ground** on the exact GPIO numbers in section 5 | The code uses the chip's built-in pull-up resistors and expects a press to read 0 | Verified |
| The backlight must be on a pin the chip can **PWM** (dim by pulsing). Today GPIO13 | The code dims the screen that way | Verified in software |
| A **BOOT button** (and ideally RESET) must exist and be reachable | Holding BOOT while plugging in is how you load firmware. RESET saves unplugging | Verified workflow; the Plus has both |
| The chip needs a **12 MHz crystal** and about a dozen small support parts | USB will not work without the right clock. The official RP2040 design guide lists them | General RP2040 practice, Unverified here |
| USB-C needs two **5.1 k resistors** on its CC pins and should have ESD protection | Without the resistors a USB-C host will not supply power. ESD protection stops static from a finger killing the chip | General USB-C practice, Unverified here |
| If there is a battery: a **proven charger and a protection circuit**, reviewed by the expert, first powered through a current-limited supply | A wrong lithium charger can start a fire. Waveshare uses an ETA6096 charger and an MP28164 buck-boost converter | Role file rule 7; Documented parts |
| The 3.3 V current the screen and chip need is **not measured** | Needed to choose the regulator. The expert has a load script ready; it needs you at the 3V3 pin with a multimeter | **Open** |

## 3. Mechanical constraints

| Constraint | What we know | Status |
|---|---|---|
| Waveshare brain board size | 21 x 51 mm, 40 castellated pins at 2.54 mm pitch, rows 17.78 mm apart | Documented (dimension drawing) |
| Where the USB-C socket is | Centred on one short edge; the battery socket on the other | Documented |
| The HAT's size, where the screen sits, hole positions | **Unknown.** Not in the repo, not in the PDFs we have | Needs a ruler, or Waveshare's HAT page |
| The screen module's size, thickness and connector | Unknown | Needs the module's page |
| Button and joystick parts, their footprints and heights | Unknown. The joystick must sit level with the screen for comfortable play | Needs the HAT's page or a look at the real parts |
| Orientation | Landscape: USB-C and joystick on the left, buttons on the right | Verified (`docs/HARDWARE.md`) |

Rule of thumb for later: before ordering, print the board at 1:1 on paper and hold the real parts on it.

## 4. Software constraints

| Constraint | Why | Status |
|---|---|---|
| **Keep every pin number exactly as today** (section 5) | Then not one line of the game changes. Any change touches `lib/lcd.py`, `lib/buttons.py`, `docs/HARDWARE.md` and `hw/BOARD.md` | Role file rule 8 |
| The screen must be the same kind: **ST7789 controller, 240 x 240, IPS**, started with the same commands | The start-up commands in `lib/lcd.py` are tuned to this module. Another panel may need different ones | Verified for this module; Unverified for any other |
| The board must run a **MicroPython build that knows its flash size** | The stock Pico build uses only 1.4 MB of 16 MB. The Waveshare 16 MB build should work on a board with the same flash part and USB wiring | Verified on the Plus; Unverified on a new board |
| The screen-speed fix in `lib/clocks.py` is plain RP2040 and does not depend on the board | The firmware decides whether it is needed | Verified by the expert on two builds |
| About 50 KB of RAM is free while playing | That is the code and MicroPython, not the board. A new board cannot add RAM; the RP2040 has 264 KB inside | Verified |

## 5. The pin map (the part that must not change)

| Signal | GPIO | Signal | GPIO |
|---|---|---|---|
| Screen DC | 8 | Joystick up | 2 |
| Screen CS | 9 | Joystick press | 3 |
| Screen clock (SCK) | 10 | Joystick left | 16 |
| Screen data (MOSI) | 11 | Joystick down | 18 |
| Screen reset | 12 | Joystick right | 20 |
| Backlight (PWM) | 13 | Button A / B / X / Y | 15 / 17 / 19 / 21 |

All Verified on the real board, 2026-10-04 (`hw/BOARD.md`). The expert found GP24 is VBUS sense, GP29 is unconnected, and GP23 and GP25 float; which pin drives the user LED is still unknown.

## 6. Fab constraints (what a factory can make)

We have not yet read a fab's capabilities page (that download needs your approval, see section 10). What follows is general knowledge, **Unverified** until read:
- Cheap "standard" boards are **two copper layers**, 1.6 mm thick, with minimum trace width and spacing around 0.15 mm and minimum drill around 0.3 mm. The RP2040's 0.4 mm pin pitch fits inside these limits, but only just; the official design guide shows how.
- Assembly services only place parts **they stock**. Choosing from their catalogue avoids waiting on parts.
- Boards are priced by size, layers, quantity and options. Five to ten small two-layer boards is the cheap sweet spot.
- Fabs want **Gerber files** (one per layer), a **drill file**, and for assembly a **BOM** and a **pick-and-place file**. KiCad produces all four.

## 7. Tool constraints

| Tool | Have it? | Needed for |
|---|---|---|
| A Mac with Python and `mpremote` | Yes (Verified, `hw/BOARD.md`) | Flashing and testing, same as today |
| KiCad (free) | Not yet. `brew install --cask kicad` | Drawing the schematic and the board, checks, exports |
| poppler (`pdftotext`, `pdftoppm`) | Installed 2026-10-04 by this session | Reading PDFs |
| A multimeter | Yes (John, via the PM, 2026-10-04: owns one, not yet located) | The first power-up: checking 3.3 V before anything else is connected |
| A soldering iron, hot air | Iron yes, hot air not mentioned. John says he is not good at soldering, so the design targets **fab assembly of every part** and zero hand-soldering | Only for a repair or a wired speaker |
| A current-limited bench power supply | Unknown; recommended only if a battery is ever on the board | Safe first power-up of a charger |
| Calipers or a ruler | Unknown | Measuring the HAT and parts |

## 8. Budget and time constraints

Estimates from `pcb/PLAN.md`; confirm every price on the fab's quote page before ordering.
- Bare boards, 5 to 10 pieces, small: about 5 to 30 USD.
- The same boards with the factory soldering the small parts: about 30 to 150 USD or more.
- Parts the fab does not stock: about 5 to 30 USD. Shipping: about 10 to 40 USD.
- A screen module for the new board, if the first board uses a plug-in module: about 10 to 20 USD (Unverified, check the shop).
- Time: days to weeks of design and review, then roughly 1 to 3 weeks for making and shipping.
- **Plan for a second order.** Most first boards need one fix.

## 9. Skill constraints (yours, and honestly, mine)

- You have never made a board. Every step will be explained before you do it, and you will be asked to confirm what you see.
- Hand-soldering the RP2040 or RP2350 (a 7 x 7 mm chip with pads underneath) is hard even for experienced people. John has said he is not good at soldering, so the rule is: every part surface-mount and from the fab's stock, assembled by the fab. Hand work limited to plugging in the screen module and the battery.
- I cannot drive KiCad's window. You click; I read the files KiCad writes and run its checks from the terminal.
- I have not seen a schematic of the Waveshare board or the HAT, and I will not copy one. The design will come from the official RP2040 design guide and the part datasheets.

## 10. What I need from you to close the gaps

1. Approval to download these public documents into `pcb/refs/` (never committed): the **RP2040 datasheet**, **Hardware design with RP2040** (Raspberry Pi), the **W25Q128JV** flash datasheet (Winbond), the **ST7789** controller datasheet, Waveshare's **Pico-LCD-1.3** wiki page (for the HAT's schematic and dimensions), and one fab's **capabilities page** (PCBWay or JLCPCB, your pick).
2. ~~Multimeter, iron~~ answered (yes, yes). Calipers or a ruler: still to ask when a measurement is needed.
3. Ten minutes at the board with a multimeter when the expert asks, to read the 3.3 V rail under load. (Section 2, last row.)
4. If you have a ruler: the HAT's width and height, and the distance from its edge to the screen.
