# DR-033: Scope of the first custom board (one integrated handheld)

- **Status:** draft, **parked** until the PM confirms John has seen the options (big scope decision). Rewritten 2026-10-04 from John's Stage 2 wishes, relayed by the PM.
- **Filed by:** PCB maker. Numbering note: this is the only PCB request with a DR number; later PCB requests are `PCB-001`, `PCB-002`, ... and their reviews `HR-P01`, ... (PM, 2026-10-04).
- **Date:** 2026-10-04
- **Blocks:** PCB phase 2 (parts choice) and everything after. Phase 1 (install KiCad) can go ahead.
- **Needs HW review:** yes. **Done: `hw/reviews/HR-033.md` (2026-10-04), verdict "fits, Option B, with limits."** The limits are folded in below (marked "HR-033").

## The decision
Which chip, which wireless, which screen and which power blocks go on the **first** spin of one integrated handheld board, and which wait for a second spin.

## John's wishes (his words, via the PM, 2026-10-04)
One board together with the HAT, no gap ("not a sandwich with a hole"). Resizable buttons; a power switch; LiPo charging and battery management; a small speaker; more RAM and storage for the multi-line slots that was shelved (D-009); wireless (an "RP2040 W" or any 2.4 GHz Wi-Fi/Bluetooth). Trade-offs he accepts: button size, joystick replaced by buttons or a different style, a different or slightly larger screen (anything except e-ink). Footprint does not matter yet.

## Why it matters
Each of the four big asks (new chip for RAM, wireless, integrated screen, battery) is a classic way a first board fails on its own. Stacking all four on spin 1 means that when something does not work, four unknowns hide the cause. Staging them puts each unknown on a board where the rest is already proven.

## Options (all are "one integrated handheld"; they differ in what spin 1 carries)

### A. Everything on spin 1
- What it is: RP2350 + 8 MB PSRAM + 16 MB flash, RM2 wireless module, 2.0" 320 x 240 screen, buttons and joystick, LiPo charger + protection + fuel gauge + power switch, speaker amplifier.
- Pros: one order, the full handheld.
- Cons: four unknowns at once on a first board; a new chip means a software port before the game even runs; the 320 x 240 screen changes every screen layout in the game. Highest chance of a dead or half-working board and a confusing bring-up.
- Cost: about 90 to 120 parts; assembled run roughly 80 to 200 USD plus parts and shipping (estimate).

### B. Staged: proven core first, then the new blocks (recommended)
- **Spin 1 (the handheld core):** RP2350A + 16 MB flash + **8 MB PSRAM** (the RAM answer), USB-C, BOOT and RESET, the same 1.3" 240 x 240 ST7789 screen as a plug-in module, joystick and four buttons on today's pins, LiPo charger + protection + battery socket + power switch, a **footprint for the RM2 wireless module left unpopulated** (or populated but unused), a speaker amplifier footprint, SWD pads and test points.
- **Spin 2:** populate and bring up wireless and sound, and if John still wants it, move to a larger screen. Fix whatever spin 1 taught us.
- Pros: the RAM problem is solved on spin 1 with the chip family the project already knows (RP2350 is the RP2040's successor; MicroPython v1.29 supports it, PSRAM support merged in v1.25). The screen, pins and driver stay exactly as verified, so the game runs on day one. Battery is on spin 1 because John asked for it and the charger block is a well-trodden design; it gets its own review and a current-limited first power-up. Wireless rides a pre-certified module, placed on spin 1 but not depended on.
- Cons: two orders. The software still needs an RP2350 port (small; see appendix A). The RP2350A has 0.4 mm pin pitch like the RP2040, so it is assembly-only.
- Cost: spin 1 about 70 to 90 parts; assembled run roughly 60 to 180 USD plus parts and shipping; spin 2 similar (estimates).

### C. Change platform: ESP32-S3 module
- What it is: an ESP32-S3-WROOM-1 module (Wi-Fi + Bluetooth + 8 MB PSRAM + flash in one pre-certified module) with the screen, buttons, battery and speaker around it.
- Pros: wireless and RAM in one part, no RF layout at all, the easiest board to draw of the three.
- Cons: a full software port: new pin map, new MicroPython port (esp32), the clk_peri fix is meaningless, SPI peaks at 80 MHz but the esp32 port's behaviour with `framebuf` and large writes is unmeasured by us; every hardware number in `hw/BUDGET.md` must be re-measured; the expert's bench scripts need rework. The team's whole knowledge base is RP2040.
- Cost: about 60 to 80 parts; assembled run roughly 50 to 150 USD (estimate). Software cost: the largest of the three.

### D. Keep the RP2040 and give up on more RAM
- What it is: option B's spin 1 with an RP2040 instead of an RP2350. Lowest-risk core.
- Pros: zero software change.
- Cons: does not deliver the RAM for slots, which John named first. 264 KB is fixed in the RP2040; there is no way to add RAM the Python heap can use.
- Cost: lowest.

## Recommendation
**Option B.** It answers every wish, in an order that keeps each spin debuggable: RAM and battery now (they change the board, not the game), wireless and sound as the second step on the same board, a bigger screen only if John still wants it after seeing the 1.3" module in his own handheld. What would change my mind: if John would rather have wireless than more RAM and accepts a full software port, C; if he wants the fewest possible orders and accepts a long bring-up, A.

## What John would have to do or accept
- **A custom MicroPython build for the new board (HR-033).** The stock Pico 2 build assumes 4 MB of flash and knows nothing about our PSRAM pin or the peripheral-clock flag, so the new board needs its own small board definition and a firmware built from source. That is a new tool in the project (the expert or the developer builds it; the `.uf2` lives with the other firmware in `backups/firmware/`, which git ignores) and needs its own decision request. Until it exists, the stock `RPI_PICO2_W` build still boots the board for bring-up, with 4 MB of flash visible and the slow SPI, exactly like the Plus on the stock Pico build in HR-F01.
- Two orders instead of one, a few weeks apart.
- The game gets an RP2350 port before spin 1 arrives: the developer's work, small, listed in appendix A. The expert re-measures the budget on the new board.
- The 1.3" screen stays for spin 1 (bought as a plug-in module, about 10 to 20 USD, estimate). The screen choice reopens for spin 2 (appendix C).
- Battery safety steps: a protected cell from a known seller, the expert's second opinion on the charger block, and the first power-up through a current-limited supply. If John does not own one, we borrow or buy one (about 30 to 60 USD, estimate) or do the battery block on spin 2.
- Tools: John has a multimeter and a soldering iron (PM, 2026-10-04) and says he is not good at soldering, so the board is designed for **fab assembly of everything** (appendix G). Hand work is limited to plugging in the screen module and the battery.

---

## Appendix A: More RAM for multi-line slots

**Why the RP2040 cannot do it.** The RP2040 has 264 KB of SRAM on the chip and no way to add more that MicroPython's heap can use (`hw/BUDGET.md`; D-009). After the 115 KB framebuffer and the game's modules, about 50 to 65 KB is free in play. A five-reel, multi-line slots needs its symbol strips, several reel windows and the win-line overlays in RAM at once; the three-reel version already ran at 36 KB mid-spin with a 29 ms garbage-collection pause (HR-F04).

| Option | RAM for Python | Software impact on what we have | Status of the facts |
|---|---|---|---|
| **RP2350A + external PSRAM** | 520 KB on chip, plus up to 8 MB PSRAM added to the heap (MicroPython merges PSRAM into the heap when the board defines `MICROPY_HW_ENABLE_PSRAM` and a CS pin; auto-detects, falls back to internal RAM) | Pin map: RP2350A has 30 GPIO, same numbering 0 to 29, same peripherals (SPI1 on GP10/11 exists), so **the pin map can stay identical**. Display driver: `framebuf` and `machine.SPI` are the same API; the init sequence is unchanged. `lib/clocks.py`: the register address and the clk_peri source differ on RP2350 (150 MHz system clock; the datasheet's clock block is different), so the fix must be **re-derived or dropped**; the expert measures SPI speed on the new build first. Flash: 16 MB W25Q128 stays. Sprite sheet format: unchanged (it is just RGB565 bytes). Firmware: an official `RPI_PICO2`/`RPI_PICO2_W` build exists (micropython.org, v1.29.0); a PSRAM-enabled build needs a board definition with the PSRAM CS pin, as Pimoroni ships for the Pico Plus 2 W (RP2350B + 16 MB flash + 8 MB PSRAM + RM2, a shipping board that proves this exact combination runs MicroPython). | Documented: Raspberry Pi RP2350 page (520 kB SRAM, PSRAM via QMI, RP2350A QFN-60 7 x 7 mm, 30 GPIO); MicroPython PR #15620 merged 2025-04-08, in v1.25.0. **Unverified:** that the Waveshare v1.29 behaviour (clk_peri on the USB PLL) also applies to the RP2350 port; the expert can test on a Pico 2 (about 5 USD) before the board exists. |
| RP2350B | Same, 48 GPIO, QFN-80 10 x 10 mm | More pins than we need; bigger chip, more routing. Not needed | Documented |
| RP2354A | RP2350A with 2 MB flash in the package | 2 MB is less than the 16 MB we use. Not suitable alone | Documented |
| ESP32-S3-WROOM-1 (N16R8) | 512 KB SRAM + 8 MB PSRAM, heap uses PSRAM | **Full port**: different port (`esp32`), different pin numbers, no clk_peri, SPI driver differences, `framebuf` same. Every number in `hw/BUDGET.md` re-measured. Flash is inside the module (16 MB variants exist). Sprite sheets unchanged | Documented (module spec). Performance with our driver: **Unverified** |
| Any other MCU (STM32, nRF52) | varies | A full port plus a less common MicroPython board; no advantage for us | Not pursued |

**What needs porting for the RP2350 route (developer's list, to confirm with the dev):** `lib/clocks.py` (re-derive or disable; measure), `pocket.py` `FAST_SPI` default, `hw/BUDGET.md` re-measured by the expert, `SETUP.md` firmware file name, the module-name trap test (unchanged). Nothing in the games, rules, saving or art pipeline changes.

**PM's two checks (answered 2026-10-04):**

1. **PSRAM chip-select pin on the RP2350A.** The PSRAM hangs on the chip's QSPI bus next to the flash and needs one extra chip-select, called XIP_CS1n. The Pico SDK's function table (`hardware/gpio.h`, RP2350 table) lists XIP_CS1n on **GPIO 0, 8 and 19** only, plus GPIO 47 on the 80-pin RP2350B. Our game uses GPIO 8 (LCD DC) and GPIO 19 (button X), so those two are out. **GPIO 0 is free in our map and is the PSRAM chip-select.** Proof the choice works: Adafruit's Feather RP2350 is an RP2350A with 8 MB PSRAM on GPIO 8, built into MicroPython with `MICROPY_HW_ENABLE_PSRAM 1` and `MICROPY_HW_PSRAM_CS_PIN 8` in its board file; ours would say 0. No collision with any pin the game uses. Cost: GPIO 0 (and its neighbour GPIO 1, by convention the debug UART pair) is no longer free for a debug UART; GPIO 4/5 or 6/7 take that role. Documented: pico-sdk `gpio.h`, MicroPython `ADAFRUIT_FEATHER_RP2350/mpconfigboard.cmake`.

2. **Peripheral clock and SPI on the RP2350 port.** Three facts:
   - MicroPython's rp2 documentation now says `machine.freq(MCU_frequency[, peripheral_frequency=48_000_000])`: the peripheral clock defaults to 48 MHz and may be set to 48 MHz or to the CPU frequency. That is the documented, supported way to do what `lib/clocks.py` does with raw register writes: `machine.freq(125_000_000, 125_000_000)` before creating the SPI object. It applies to RP2040 and RP2350 builds alike. **Recommendation for the developer (separate request): replace the register poke with this call; the expert should measure that it gives the same 17 ms frame.**
   - `lib/clocks.py` as written **cannot run on an RP2350**: it writes to `0x40008048`, but the RP2350's CLOCKS block is at `0x40010000` (pico-sdk `rp2350 addressmap.h`), so the poke would hit the wrong register. Another reason to move to `machine.freq`.
   - The RP2350's default CPU clock is **150 MHz**, not 125. SPI divides the peripheral clock by an even number, so with the peripheral clock at 150 MHz the choices near our target are **75 MHz or 37.5 MHz**, not 62.5. 75 MHz is above what we verified on the panel (62.5 MHz clean); 37.5 MHz costs frame time (about 30 ms per full frame, estimate). The clean option is `machine.freq(125_000_000, 125_000_000)` on the RP2350 too, which gives 62.5 MHz exactly as today. **For the expert to measure on a Pico 2:** (a) boot default of clk_peri on the `RPI_PICO2` v1.29 build, (b) real SPI clock for a 62.5 MHz request at 150/150 and at 125/125, (c) full-frame push time, (d) whether PSRAM changes any of that. Status: documented API and addresses; timings Unverified.

**HR-033 limits on the port (expert, 2026-10-04):** the 24 MHz SPI cap comes from the Pico SDK's default (clk_peri on the 48 MHz USB PLL unless the build sets `PICO_CLOCK_ADJUST_PERI_CLOCK_WITH_SYS_CLOCK`), so it will be on a stock Pico 2 build too. Do **not** port `lib/clocks.py` by changing its address; the clean fix is the custom board definition with that flag, after which `lib/clocks.py` is deleted and `FAST_SPI` becomes a no-op, with a boot-time `show()` timing printed so a wrong build is noticed. Runtime alternative, documented in the rp2 quickref: `machine.freq(125_000_000, 125_000_000)`; the expert can measure that on today's RP2040 with no new hardware. On the RP2350 run the system clock at 125 MHz (or a divider at or below 62.5 MHz, re-checked by eye); do not assume 75 MHz is clean. Re-measure everything on the first board; `hwtest/` runs unchanged.

**Caveat on PSRAM speed.** PSRAM over QSPI is slower than on-chip SRAM. The framebuffer and anything in the animation loop should stay in internal SRAM (520 KB is already twice today's), and PSRAM holds the bulk (sheets, decks, strips). How MicroPython places objects is not controllable per object, so the expert must measure a full-frame push and a blit with PSRAM enabled. **Unverified.** HR-033 adds the test: allocate the framebuffer first after boot (today's HR-001 rule), time `show()`; if it is not about 17 ms at the same SPI speed, the buffer landed in PSRAM and the port needs the SRAM-first heap option.

## Appendix B: Wireless on a first PCB

- **"RP2040 W" is not a part.** The Pico W is an RP2040 plus a separate Infineon CYW43439 radio chip on the same board, with its own antenna and RF layout. There is no RP2040 or RP2350 with wireless inside.
- **Pre-certified module vs bare chip.** A bare radio chip needs an RF layout (controlled-impedance trace, matching network, antenna, keep-outs) and, to sell or even legally operate in most countries, radio certification. A pre-certified module carries its own antenna and approvals; the host board only needs a ground-plane keep-out under the antenna and a few digital lines. **For a first PCB the module is the only sensible route.**
- **Raspberry Pi RM2.** 14.5 x 16.5 x 2.55 mm, 21 castellated pads at 1.5 mm pitch, CYW43439 inside (the same chip as the Pico W and Pico 2 W), 2.4 GHz Wi-Fi 4 and Bluetooth 5.2, shared on-module antenna, gSPI host interface plus three host GPIOs. Full modular approval in the EU, UK, USA and Canada. About 4 USD at launch (June 2025). MicroPython's `RPI_PICO2_W` build already talks to this chip over PIO-SPI, so the pins the module uses must match that build's expectations (or we make a board definition). Source: Raspberry Pi RM2 documentation and datasheet.
- **ESP32-S3-WROOM-1.** Wireless, PSRAM and flash in one pre-certified module. Easiest board, hardest software port (appendix A).
- **Which families make wireless easy:** ESP32 family (radio inside the chip, module pre-certified, MicroPython mature); RP2040/RP2350 with the RM2 module (MicroPython mature for the Pico W / Pico 2 W pinout); nRF52 (Bluetooth only, MicroPython less common). Everything else is harder.
- **HR-033 confirmed the pins** from the SDK's `pico2_w.h`: REG_ON GP23, the single bidirectional data line GP24, CS GP25, CLK GP29. Route the RM2 to exactly those four so the stock `RPI_PICO2_W` build drives it. The Pico 2 W also shares GP29 with its VSYS divider; we will not: the battery divider goes on GP26 to GP28 and GP29 belongs to the radio. Which RM2 castellation carries which signal comes from the RM2 datasheet (download pending).
- **Cost of wireless on the board:** the module, a few passives, 6 to 7 GPIO (the Pico 2 W uses GP23, GP24, GP25, GP29 for the radio, which are exactly the pins the game does not use), and about 2 cm² of board with a keep-out. **Unverified until the RM2 datasheet is read:** exact pad functions and keep-out.
- **What wireless would be for:** John has not said. Until there is a software use (score sync, a phone companion, updates over the air), the module can sit on the board unpopulated at zero cost.

## Appendix C: Screens larger than 1.3", not e-ink

| Module (Waveshare, as examples of what is sold) | Resolution | Controller | Interface | Outline / active area | What changes in our code |
|---|---|---|---|---|---|
| 1.3" LCD Module (today's panel, in module form) | 240 x 240 | ST7789 | SPI, 8 pins | about 1.3" active | Nothing |
| 1.54" LCD Module | 240 x 240 | ST7789VW | SPI, 8 pins | 50 x 35 mm, active 27.72 x 27.72 mm | **Nothing in the drawing code** (same pixel count). Init values may need a check; the framebuffer is the same 115,200 bytes. The cheapest "bigger" step: 18% larger on each side |
| 2.0" LCD Module | 240 x 320 | ST7789V | SPI, 8 pins | 58 x 35 mm, active 30.6 x 40.8 mm, 3.3 V at up to 46 mA | Framebuffer becomes 153,600 bytes (does not fit comfortably on an RP2040 next to the game; fine on an RP2350). Every screen layout in the game is written for 240 x 240 and would be re-laid-out; the orientation command changes. The driver's window commands carry over |
| 2.4" to 2.8" modules | 240 x 320 | ILI9341 (usually) | SPI | larger | As above, plus a different init sequence (ILI9341 is not an ST7789) and a slower panel. The `lib/lcd.py` structure carries over; `_INIT` is rewritten |
| 1.69" / 1.9" modules | 240 x 280 / 170 x 320 | ST7789V2 | SPI | | Odd sizes with RAM offsets; more driver work for little gain |

Availability: all of the above are stock items at Waveshare and others (Documented from the wiki pages, 2026-10-04); the bare panels behind them are harder to source and need a flex connector, which is why the module-on-header route stays recommended for every spin. The HAT's own screen cannot be moved: it is soldered to the HAT.

Recommendation inside this appendix: spin 1 keeps 240 x 240 (1.3" or 1.54" module, John's pick, same code). The 2.0" 320 x 240 is a spin 2 question, taken together with the RP2350's larger RAM and a developer estimate for re-laying out the screens.

## Appendix D: Battery, charger, protection, fuel gauge, power switch, speaker

Safety first: **a lithium cell with a wrong charger or no protection can catch fire.** Role file rule 7 applies: proven parts, the expert's second opinion, a current-limited supply for the first power-up, and a protected cell.

| Block | First-board-level choice | Notes | Status |
|---|---|---|---|
| Cell | Single-cell 3.7 V LiPo **with a built-in protection board**, JST-PH 2.0 mm connector (the most common hobby pouch cell) | Waveshare uses an MX1.25 socket; JST-PH is easier to buy cells for. Capacity 1000 to 2000 mAh is plenty for a screen at under 200 mA (Unverified; measure) | General practice, Unverified |
| Charger | **MCP73831** (Microchip, linear, up to 500 mA, SOT-23-5, one resistor sets the current; the Adafruit and SparkFun boards use it) or the ETA6096 Waveshare uses | Linear chargers are simple and well documented. Set 500 mA for a 1000 mAh cell, less for smaller cells | Documented in the MCP73831 datasheet (to be read); Unverified here |
| Protection | A protected cell **and** on-board protection (DW01A + FS8205A pair, the standard low-cost combination) | Belt and braces: the cell's own board plus ours | General practice, Unverified |
| Power path | USB 5 V to the charger; the system runs from the battery rail through the regulator. A **3.3 V buck-boost** (what the Plus does with the MP28164) or a low-dropout regulator if the load is small enough | A LiPo runs 4.2 V down to 3.0 V, which crosses 3.3 V: a buck-boost keeps 3.3 V all the way; an LDO browns out below about 3.4 V. Decide after the expert measures the load | Documented (MP28164 on the Plus); choice Unverified |
| Fuel gauge | **MAX17048** (I2C, tells the game the percentage) or the cheap route: an ADC divider on the battery and a lookup table | The gauge chip is a few dollars and one I2C pair (GP4/GP5 free). The divider is free but rough | Documented (part exists); Unverified here |
| Power switch | A slide switch in the battery line to the regulator **enable** pin (not in the high-current path), so the switch is small and the charger still charges with the switch off | Standard handheld practice | General practice, Unverified |
| Speaker amplifier | **PAM8302A** (class-D, mono, 2.5 W, analog input from a PWM pin through an RC filter) is the simplest; **MAX98357A** (I2S digital input) sounds cleaner and MicroPython's `machine.I2S` exists on rp2 | Either needs one small 8 ohm speaker, 1 W or less. PWM audio costs one GPIO (GP22 free); I2S costs three (GP0/1 + one more) | Documented parts; audio in MicroPython on our board Unverified |

**HR-033 second opinion (expert, 2026-10-04):** MCP73831 agreed (set at or below 0.5 C, give it copper; charge from USB 5 V only); DW01A + FS8205A plus a protected cell agreed, with the software low-battery warning at about 3.4 to 3.5 V because the protection cut-off is far lower; **buck-boost, not an LDO** (an LDO browns out at about 3.5 V and loses the bottom third of the cell; MP28164 or a TPS63001-class part, laid out per its datasheet, away from the ADC reference); switch on the regulator enable with a pull-down; **ADC divider on spin 1** (100 kΩ or more total, or switched by a GPIO) with the MAX17048 as a footprint; **PAM8302A with PWM audio** as the lower-risk sound path, sampling the battery only when audio is idle; expected load about 100 mA today, to be measured with `hwtest/load_hold.py` when John is scheduled, so any 500 mA-class buck-boost is plenty. No part datasheet was read by the expert either; read each reference schematic before placing.

Spin 1 carries the charger, protection, cell socket, power switch and regulator. The fuel gauge and the speaker amplifier can be footprints only on spin 1 (zero cost if unpopulated), populated on spin 2 once the core is proven, unless John wants sound early.

## Appendix E: The staged proposal in one table

| Block | Spin 1 | Spin 2 |
|---|---|---|
| RP2350A, 16 MB flash, 8 MB PSRAM, USB-C, BOOT, RESET, crystal | yes | fixes only |
| 1.3" or 1.54" 240 x 240 ST7789 module on a header, same pins | yes | keep, or 2.0" 320 x 240 if John wants it and the dev re-lays out the screens |
| Joystick and four buttons, same pins (sizes and style John's choice) | yes | fixes only |
| LiPo charger, protection, cell socket, power switch, 3.3 V regulator | yes, with the safety steps | fixes only |
| RM2 wireless module | footprint and pins routed; populate only if cheap to do so | bring up in software |
| Speaker amplifier and speaker | footprint | populate and bring up |
| Fuel gauge | footprint | populate |
| SWD pads, test points, user LED | yes | yes |

## Appendix G: Assembly plan (John: "as many small parts as possible assembled by the fab")

- **Design rule for every part: surface-mount, from the fab's own stock.** Then the fab's assembly service places it and John solders nothing. The RP2350A (0.4 mm pitch, pads underneath), the flash, the regulator, the charger, every resistor and capacitor, the crystal, the ESD part, the RM2 module (castellated, surface-mount) and the amplifier are all surface-mount and all routinely machine-placed.
- **Connectors and switches, also surface-mount:** USB-C receptacle (surface-mount 16-pin type with through-board pegs for strength), JST-PH battery socket (surface-mount version exists), tactile buttons and 5-way joystick switch (surface-mount versions exist), slide power switch (surface-mount), a surface-mount 2.54 mm pin socket for the screen module, surface-mount speaker pads or a small wired speaker on two pads.
- **What might still be hand-soldered, and how to avoid it:** (1) a part the fab does not stock: avoid by choosing from their catalogue while drawing the schematic, or let PCBWay source it (they will, at a fee); (2) a through-hole part: avoid by not using any; (3) a wired speaker: two wires to two pads, the one hand-solder job that is easy; or pick a surface-mount speaker. Target: **zero hand-soldering** on spin 1.
- **Which service:** PCBWay "PCB assembly" (they source any part, place both sides and through-hole, quote by hand, slower) or JLCPCB "PCBA" (cheaper and faster, but parts must come from their library; their "economic" tier is one side only, the "standard" tier does both sides and odd parts). For a first board with a 0.4 mm-pitch chip, both are fine; JLCPCB is usually cheaper if every part is in their library, which we can check while choosing parts. **The exact constraints (one side or two, minimum quantity, which packages they refuse) are Unverified until the capabilities page is read (download pending John's approval).**
- **Assembly fees to expect:** a setup fee, a stencil, a per-joint price and the parts. The PLAN's "30 to 150 USD or more" range for a small run is the right order of magnitude; the RP2350, PSRAM and RM2 add roughly 10 to 15 USD per board in parts (estimate).
- **Minimum quantity:** assembled runs are usually 2 to 5 boards minimum. Having a spare is good: one for bring-up, one kept clean.

## Appendix F: Sources read for this request (online, 2026-10-04; nothing downloaded yet)
- Raspberry Pi, "Microcontroller chips" (RP2040 and RP2350 variants, SRAM, PSRAM via QMI): raspberrypi.com/documentation/microcontrollers/microcontroller-chips.html
- Raspberry Pi, Radio Module 2 documentation and datasheet: datasheets.raspberrypi.com/rm2/rm2-datasheet.pdf and the documentation repository's rm2.adoc
- MicroPython, PR #15620 "rp2: Add PSRAM support" (merged 2025-04-08, in v1.25.0); micropython.org/download/?mcu=rp2350 (v1.29.0 builds, Pico 2 W listed)
- Pimoroni, Pico Plus 2 W product page (RP2350B, 16 MB flash, 8 MB PSRAM, RM2)
- Waveshare wiki, 2inch LCD Module and 1.54inch LCD Module pages
- Espressif ESP32-S3-WROOM-1 module (via product listings; the datasheet is to be read if option C is chosen)
- Repo: `hw/BUDGET.md`, `hw/reviews/HR-F04.md`, `pm/DECISIONS.md` (D-009), `docs/HARDWARE.md`, `pcb/requirements/REQUIREMENTS.md`
- Charger, protection, fuel gauge and amplifier part names come from general practice and vendor reference boards (Adafruit, SparkFun); their datasheets are not yet read.

**Everything marked Unverified above must be checked against the datasheet or measured by the expert before it becomes a design fact.**
