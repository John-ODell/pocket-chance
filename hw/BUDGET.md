# Hardware budget

_Maintained by the microcontroller expert. The dev designs against this file. Every number carries its source: `measured` (script + date), `datasheet`, or `estimate`. Measured 2026-10-03 on **both** firmwares: v1.22.2 stock Pico build (before John reflashed) and **v1.29.0 WAVESHARE_RP2040_PLUS-FLASH_16M (current)**. CPU 125 MHz on both. Scripts in `hwtest/`. Where the two firmwares differ, both numbers are given._

## READ FIRST: the SPI clock changed with the new firmware
On v1.29.0 the peripheral clock (`clk_peri`) is fed from the 48 MHz USB PLL, not the 125 MHz system clock (`CLOCKS.CLK_PERI_CTRL = 0x840`, `hwtest/clk_peri.py`). SPI divides `clk_peri` by an even number, so the fastest SPI is now **24 MHz**, and a full frame takes **46 ms (21 fps)** instead of 18.5 ms. `machine.freq()` does not change this.

**Fix found, software only, 3 lines at boot** (`hwtest/clk_peri_fix.py`): clear the ENABLE bit of `CLK_PERI_CTRL`, set AUXSRC to `clk_sys`, set ENABLE. Measured after the poke: full frame **17.2 ms on the wire, 58 fps**. Traps:
- MicroPython caches the old peripheral clock, so `SPI(1, 62_500_000)` prints `baudrate=24000000` but really runs at 62.5 MHz. Every requested baud is really **x 2.6** (125/48). Request what the repr should say, and verify by timing a frame, not by reading the repr.
- A **soft reset does not undo it**; only a power cycle does. Harmless here (only UART baud depends on `clk_peri`, and this project uses no UART), but it means the board's state is not what a fresh boot gives until unplugged.
- It is a raw register write. It needs a decision request from the dev before it goes into `lib/lcd.py`; I am proposing it, not installing it.

Without the fix the game runs at 20 fps full-redraw and 78 fps for a 48-row band, which is still playable for cards. With it, the old numbers hold.

## Fixed facts
| Item | Value | Source |
|---|---|---|
| CPU | RP2040 dual Cortex-M0+, running at **125 MHz** on this firmware | measured, `board_info.py` |
| SRAM | 264 KB; 222,720 bytes free to Python at boot | measured, `ram_free.py` |
| Flash chip | 16 MB (reads above 2 MB are erased, not mirrored) | measured, `flash_probe.py`; 16 vs 8 from the box |
| **Filesystem available** | **15,728,640 bytes (15 MB)**, 15,720,448 free after `main.py`, since the reflash to v1.29.0 on 2026-10-03 (was 1.4 MB on the stock build). See HR-F01 | measured, `board_info.py` |
| `_thread` | reported `_thread='unsafe'` by v1.29.0 `sys.implementation` | measured, `board_info.py` |
| Display | 240 x 240, RGB565 | old driver |
| One full frame | 240 x 240 x 2 = **115,200 bytes** | arithmetic |

## SPI clock
| Requested | Granted by RP2040 | Full frame on the wire | Throughput |
|---|---|---|---|
| 100 MHz (old code) | **62.5 MHz** | 18.2 ms | 50.6 Mbit/s = 6.33 MB/s |
| 62.5 MHz | 62.5 MHz | 18.2 ms | same |
| 40 MHz | 31.25 MHz | 35.7 ms | 25.8 Mbit/s |
| 20 MHz | 15.625 MHz | 70.7 ms | 13.0 Mbit/s |

measured, `spi_clock.py`, **v1.22.2**. On **v1.29.0 as shipped** the same script gives: any request from 31.25 to 100 MHz → **24 MHz, 46.2 ms per frame, 20.0 Mbit/s**; 20 MHz → 12 MHz, 91.8 ms. After the `clk_peri` fix: 17.2–18.3 ms per frame (55–58 fps), `clk_peri_fix.py`, `fast_pattern.py`. **The panel is clean at a real 62.5 MHz on v1.29.0: John eyeballed colour bars, a 1-px checkerboard, text and a 1-px border on 2026-10-04 and reported no speckles, tearing or wrong colours.**

**Hard ceiling: 55–58 fps with the fix, 21 fps without.** No drawing strategy beats the wire time.

## Frame rate
Two columns: SPI at 62.5 MHz (v1.22.2, or v1.29.0 with the `clk_peri` fix) and SPI at 24 MHz (v1.29.0 as shipped). Python time is the same on both.

| Strategy | At 62.5 MHz | At 24 MHz | Source |
|---|---|---|---|
| Full redraw: `fill()` + `show()` | 4.2 ms Python + 18.5 ms wire = **22.7 ms, 44 fps** | 4.2 + 46.4 = **50.6 ms, 20 fps** | measured, `frame_full.py`, 100 frames each |
| Full redraw, busy scene (20 `fill_rect` + 10 `text` + `show`) | 26.4 ms, 38 fps | 54.5 ms, 18 fps | measured, 50 frames |
| Full redraw with a 115 KB background streamed from flash first | ≈ 45–50 ms, **~20 fps** | ≈ 75–80 ms, ~13 fps | read and wire measured; sprite time is an estimate |
| Partial: 48x48 sprite over a 51x48 window, scratch buffer, pushed | 3.9 ms (max 7.7), 253 fps | 5.1 ms (max 13), 198 fps | measured, `frame_partial.py`, 150 frames |
| Partial: full-width band, 240x48 rows, pushed straight from the framebuffer | 7.2 ms (max 19), 138 fps | 12.7 ms (max 24), 79 fps | measured |
| Partial: 8x8 region (a digit) | 1.2 ms | 1.1 ms | measured |

Where the time goes in a full frame: about **80% on the wire, 20% in Python** for simple scenes. Partial pushes are the win: a band of 48 rows costs 20% of a full frame. Pushing from the framebuffer needs a contiguous byte range, which is a full-width band; a narrow window must be copied into a scratch buffer first (`frame_partial.py` strategy (a) shows this still wins).

## RAM
| Item | Value | Source |
|---|---|---|
| Free at boot (nothing imported) | 222,720 | measured, `ram_free.py` |
| Framebuffer + bench driver cost | 118,528 | measured |
| **Free after framebuffer** | **104,192** | measured |
| Largest single allocation after framebuffer | **83,980** | measured (bisection) |
| Second full framebuffer (115,200) | **does not fit** | measured |
| Sprite cache alongside the framebuffer | 16 KB → 87.6 KB left; 32 KB → 71.2 KB; 48 KB → 54.8 KB; 64 KB → 38.5 KB | measured |

These are before the dev's modules load. Each imported module costs RAM (estimate 2–10 KB each for modules this size). Plan on **~60–70 KB free in play** after a dozen modules, a 16 KB scratch and the framebuffer. No double buffering: draw into the one framebuffer and push, or push bands.

## Flash
| Item | Value | Source |
|---|---|---|
| Read speed, `readinto`, 480-byte chunks (one row) | 4.44 MB/s → a 115,200-byte background in **25.9 ms** | measured, `flash_read.py` |
| Read speed, 4,800-byte chunks | 5.44 MB/s → 21.2 ms per background | measured |
| Read speed, one 32 KB read | 5.63 MB/s → 20.5 ms per background | measured |
| One 40x56 card (4,480 bytes) from flash | **~1 ms** | derived from the above |
| Save a 41-byte JSON file, plain overwrite | 2.9 ms mean (2.5–3.3) | measured, `flash_write.py`, 10 writes |
| Save with tmp + `os.rename` (atomic) | **22 ms mean, 6–79 ms** (v1.22.2); 26 ms mean, 7–**119 ms** (v1.29.0, fresh 15 MB filesystem) | measured, 10 writes each |
| Write endurance | ~100,000 erase cycles per 4 KB block, class figure for NOR flash; LittleFS spreads writes across free blocks | datasheet-class estimate |

Saving once per round is harmless (a round every 5 s for 10 hours is 7,200 writes). Saving on every button press or every frame is not.

## Second core
| Item | Value | Source |
|---|---|---|
| Baseline, one core: draw busy scene + push | 40.9 fps (62.5 MHz); 19.1 fps (24 MHz) | measured, `core2.py`, 60 frames |
| `_thread`: core 1 pushes while core 0 draws | core 0 drew at 145 fps on both firmwares; core 1 pushed at 55.8 fps (62.5 MHz) / 21.9 fps (24 MHz), wire-bound; thread exited cleanly both times. v1.29.0 labels `_thread` **unsafe** | measured |

It works and it moves the 18.5 ms push off the drawing core, so drawing gets the full CPU. Costs: tearing (the push reads a buffer that is being drawn), the GIL in MicroPython (only one core runs Python bytecode at a time; the gain here is because `spi.write` releases it), and `_thread` is documented as experimental on rp2. Verdict: **real gain, not needed for a card game at 20–40 fps.** Recommend against it for phase 1; revisit for slots animation if needed.

## Input
| Item | Value | Source |
|---|---|---|
| All 9 inputs idle with pull-ups | high 200/200 samples each | measured, `pins_idle.py` |
| Key to GPIO mapping | all nine match the old pin map (see `BOARD.md`) | measured, `bounce.py` + `pin_hunt.py`, 2026-10-04, John pressing |
| Contact bounce | **none seen**: 44 edges across 7 keys, 0 edges within 5 ms of another; sample period 240 µs, so any bounce longer than that would have shown | measured, `bounce.py` 45 s |
| Press length, a human tap | 140–880 ms buttons; 1.1–1.6 s deliberate joystick holds | measured |
| Poll cost | sampling all 9 pins in a Python loop runs at ~4.1 kHz, so one poll of nine pins ≈ 240 µs | measured, `bounce.py` |

For the dev: poll at 50–100 Hz, treat a key as pressed on the falling edge, and ignore it until it goes high again (edge detect, not level). No debounce timer is needed on this HAT; a 20 ms one costs nothing if you want belt and braces. A 240 µs poll of all nine pins is under 3% of a 10 ms frame.

## Power
| Item | Value | Source |
|---|---|---|
| ADC3/GPIO29 | 1.17 V equivalent; probably **not** VSYS on this board | measured, `pins_idle.py`; check schematic |
| Backlight current at PWM levels | not measured, no meter in the loop | |
| Battery, charging | not measured; nothing on the charge circuit will be touched without John present | |

## First on-board code (UPLOAD.md step 1, measured 2026-10-04, v1.29.0, fast clock, no art files)
Scripts: `hwtest/pocket_bench.py` (8 scripted hands), plus a per-module import run. The import collision in HR-F02 was worked around in the bench only.

| Item | Measured |
|---|---|
| RAM cost of all 12 modules (compile + import) | **19,632 bytes**: blackjack 4,608, blackjack_rules 3,344, lcd 2,592, cards 1,952, save 1,520, blackjack_table 1,344, bankroll 1,072, buttons 960, font 768, pixfmt 720, clocks 480, assets ~80 |
| Free after LCD framebuffer | 101,104 |
| Free after all imports and objects | 84,272 |
| Free after 8 hands, `gc.collect()` | **64,576** (matches the "60–70 KB in play" rule) |
| `draw_all` (full redraw + show), code-drawn felt and cards | 39–43 ms, of which ~18 ms is the wire and ~25 ms Python drawing, mostly size-2 text (`font.text` draws each lit glyph pixel as a `fill_rect`) |
| Bet change: `draw_top` + 24-row band | 15 ms (band push ≈ 3.6 ms, drawing ≈ 12 ms) |
| Hit/stand: `draw_player` + `draw_bottom` + 142-row band | 29 ms |
| `finish_round`, first build: save then `draw_all` | 121 ms mean, 177 ms max |
| `finish_round`, fixed build (`draw_all` then save), whole call | 131 ms mean, 225 ms max |
| **Key press → result banner on screen** (fixed build) | **82 ms mean, 97 ms max.** A result scene draws 6+ cards; each code-drawn card is ~5 ms of size-2 text. With card art, a blit is ~1 ms, so this drops to ~45 ms by itself |
| Save with `.bak` (write tmp, rename old → bak, rename tmp → json) | 54 ms mean / 102 ms max on a near-empty filesystem; **77 ms mean / 151 ms max** once `save.json`, `save.bak` and bench files exist. LittleFS housekeeping varies; budget **up to ~250 ms** for the whole end-of-round, once per round |
| `Double`: bet doubles, one card, round resolves, balance moves by exactly the doubled bet | correct in 8 of 8 hands (bench pressed X whenever allowed) |

Everything fits the budget. Notes for the dev: size-2 text is the main Python cost (~1 ms per character), so the menu, card faces and banners are where art pays off; the menu label `Slots (soon)` at size 2 is 192 px wide from x=92 and runs 44 px off the right edge, which is what John saw as "messy".

## Rules of thumb for the dev
- **Until the `clk_peri` fix is ruled on, design for 24 MHz SPI: 46 ms per full push, 20 fps full redraw, 79 fps for a 48-row band.** With the fix: 18.5 ms, 44 fps, 138 fps. Design so the game is fine at the slow numbers and looks better at the fast ones.
- Time frames with `utime.ticks_us()`, never trust the `SPI` repr's `baudrate=`.
- Push bands or windows for anything that moves; full `show()` only on scene changes.
- Backgrounds stream from flash in ~21–26 ms. Do it on scene change, not every frame.
- Do not allocate in the draw loop. One 16 KB scratch buffer, preallocated, covers the largest sprite.
- Roughly 60–70 KB of RAM will be free in play. No second framebuffer.
- Save to flash once per round, atomically. Expect up to 80 ms; do it between hands, not mid-animation.
- Stay on one core.
