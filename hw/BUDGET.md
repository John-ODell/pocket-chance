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
| Flash chip | **16 MB by aliasing evidence**: reads at 2, 4, 8 and 15 MB are erased, not mirrors of the start, so the chip is larger than 8 MB; JEDEC ID not read (PM ruling) | measured, `flash_probe.py` |
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
| Re-banded screen (commit `2c930a9`, four non-overlapping bands), re-bench | unchanged within noise: `draw_all` 45 ms, bet band 16 ms, key→banner 82.5 / 101 ms, save 62 / 119 ms, 63.3 KB after 8 hands |
| John playing the real game (`pocket.py` RESULT lines) | boot 82,800 free; inside blackjack 58,736 (pre-split build) / **54,096 (split build)**; after leaving 74,080 / 71,664; a second entry costs only ~8 KB because the rules modules stay cached |
| Card blit from flash after the HR-F03 fix (step 1f `art.py`): first call / cached | 8.5 ms / **5.6 ms** (`open()` alone ≈ 3 ms). `Assets.load` 3.9 ms; `LCD.show_buf` 56x56 1.9 ms; `background_rows` 48 rows 6.7 ms cached. A code-drawn card is 3.9 ms, so per-file card art is still slower than drawing; a sprite sheet (one open per scene) would be ~2 ms per card (`blit_bench.py`, HR-F03) |
| **`os.stat` on this LittleFS** | **3.7 ms**; `open` + header + 6,272-byte read 4.1 ms; so one `Assets.blit` from flash costs ~8 ms, of which ~1 ms is the read (HR-F03). Blit the same sprite from RAM: 1.5 ms keyed, 0.8 ms unkeyed |
| Slots spin, 3 reels, 8 px/frame, as described in DR-020 (flash reads + copy + `show_rect` per reel per frame) | **82 ms, 12 fps** at 62.5 MHz; 90 ms at 24 MHz (`slots_spin_bench.py`, HR-020) |
| Slots spin, fixed path (symbols in RAM, compose pushed directly) | **13.1 ms, 76 fps** at 62.5 MHz; 17.7 ms, 56 fps at 24 MHz; frame with 6 symbol reads 38 ms; one reel 4.5 ms (`slots_spin_bench2.py`) |
| Direct push of a 56x56 window | 1.5 ms; `show_rect` of the same window 7.1 ms (Python row copy) |
| Blink: gold frame on/off around three 60x60 windows via `show_rect` | 57.8 ms per toggle, 85 max (HR-021) |
| **Slots as built (step 1g), real `games/slots.py`**, scripted spins | frame steady **10.8 ms** mean / 17.8 max; symbol-change frame 14.9 / 19.9 ms; 0 overruns at the 20 ms pace; spin 3.2–4.1 s end to end; save after spin 63 / 110 ms; blink 784 ms (720 ms designed sleeps); paytable 111 ms; bet change 21 ms (`slots_play_bench.py`) |
| **`machine.freq(125_000_000, 125_000_000)` vs the register poke (HR-F05)** | same 17.9 ms frame; `CLK_PERI_CTRL` `0x820` (pll_sys); **SPI repr honest (62,500,000)**, so the 2.6x request trap goes away; `(125M, 48M)` → 46 ms; PWM and USB unaffected; runtime setting, must run at every boot before `LCD()` (`freq_peri.py`) |
| **Hold'em layout (DR-043), nine cards + four seat boxes, real card primitives** | full redraw **85 ms** drawn / 74 ms sheet; deal with seven backs 49 / 67.5 ms (backs from a sheet are slower); community band 27 ms; dealer band 15 ms; seat row 18 ms; four text strips 2.7 ms; 24x24 chip stack 1.4 ms sheet / 3.1 drawn (`holdem_bench.py`, HR-043/044/047) |
| **Hold'em river hint (DR-042): dealer outs over 45 unseen cards**, each a 6-card `evaluate` + `compare` vs the player's 7-card value | **228 ms** (5.1 ms per card); player 7-card evaluate 16.6 ms; the both-hole-cards-unknown version (990 7-card evaluates at 17.9 ms) would be 17.7 s, not viable (`outs_bench.py`) |
| **Hold'em AI seats (DR-044)** | `poker.evaluate` 5/6/7 cards 0.9 / 5.9 / **28 ms**; four seats at the flop 29 ms; **showdown, six 7-card hands 134 ms** (run before the first flip); four seats' state 352 B; gc pause in this scene 25 ms |
| **Stud AI seat rail (DR-041)** | five seats decide (evaluate + `advice`) in **5.3 ms** total; settle 4.6 ms; rail draw 1.75 ms, with 12-row push 3.1 ms; bottom band with rail 8.7 ms; five seats' state 496 B (`stud_rail_bench.py`, HR-041) |
| **Integrated build, step 1n (`machine.freq`, Stud seats, Hold'em), benched from the mount** | `first show us=18042`, repr `62500000`; boot 68.0 KB; blackjack in play 54 KB after gc; Stud (5 seats) ready 52.6 KB, in play 51.7; Hold'em (4 seats) ready 49.5 KB, in play 47.6–49.0; enter/leave cycling drifts −0.5 KB (Stud, 3 cycles) and −0.8 KB (Hold'em, 9 cycles); gc 11–12.3 ms; the `clocks.py` tripwire never fired (`stage_bench*.py`) |
| **DR-050 as built (`machine-freq`)** | first `show()` **18,013 µs**, repr `baudrate=62500000`; `FAST_SPI=False` 46,109 µs, `24000000`; boot 68.1 KB, unchanged by deleting `clocks.py`; tripwire import never fired (HR-050). HR-015's "request 12 MHz for 31.25" is obsolete from this build |
| **Hold'em after the two fixes (`holdem` 7972568)** | ready **49.6 KB** right after entry (44.9 KB before the first gc); in play 47.6–49.0 KB after gc; **river key→prompt 378 ms** (was 628; hint 312 ms inside the pause); deal 72 ms; raise→first flip 200 ms; player balance identical with 4 and 0 seats (`stage_bench_holdem.py`, `holdem_play_bench.py`) |
| **Ultimate Hold'em as built (step 1m), four seats, real code** | deal redraw **73 ms**; check→flop 307 ms (push + 300 ms pause); check→river 628 ms incl. **outs hint 321 ms** after the pause; raise→first flip **183 ms** (seats settled first); raise→result 0.60 s; fold→result 0.66 s; next 55 ms; save 50 / 96 ms; help 215 ms, 256 B retained; **player balance identical with 4 and 0 seats**; real program: `import holdem` leaves 37 KB garbage, ready 49.5 KB after gc, **in play 42 KB after gc**, menu 48.8 KB, gc pause 12.3 ms (`holdem_play_bench.py`, `stage_bench_holdem.py`, HR-043/044/047 addenda) |
| **Stud with five AI seats (step 1k), benched from the mount, real code** | boot 68.0 KB (scripted); Stud ready 52.7 KB after gc (1j: 54.0); after hands 1 / 6: 51.7 / 51.5 KB; paytable load/drop clean; back at menu 57.5 KB; gc 11.6 ms; deal redraw **94 ms** drawn / 80 ms sheet (+5 ms over 1j for the rail and the seats' deal); flips 304–307 ms; raise→result 1.04 s; fold→result 163 ms; save 35 / 94 ms; **player's results unchanged**: same seed, same balance (1980) with and without seats (`stage_bench_stud.py`, `stud_play_bench.py`) |
| **Caribbean Stud as built (step 1j), real `games/stud.py`** | 10-card deal redraw **89 ms** drawn / **72 ms** with a card sheet (backs stay code-drawn, HR-026 limit 1); reveal flips **303–307 ms** apart (target 300), 3 dealer-band pushes per raise; raise key→result 1.08 s; fold→result 175 ms (258 max incl. save); next hand 40 ms; paytable show (`stud_pay` import + draw) 201 ms, 112 B retained over 5 shows, `sys.modules` clean; save 67 / 153 ms; RAM after gc 54.0 KB ready, 53.3 / 52.7 / 52.3 KB after hands 1 / 10 / 20; 10 enter/leave cycles drift −1.3 KB; gc pause 11.4 ms (`stud_play_bench.py`, `stage_bench_stud.py`) |
| **Caribbean flop game as built (`flop-game` 3fb0dbf), real program scripted** | ready **52.1 KB** after gc, in play flat at 50.1–50.2 KB over 20 hands (no leak), import 15.3 KB, back at menu 56.4 KB; deal redraw 18 ms, flop visible ~340 ms after the key, dealer flip 285–293 ms after the river push (300 by the clock), showdown 0.8–0.9 s total, save 57 ms mean / 149 max, help 200 ms, gc pause 12 ms (`caribbean_play_bench.py`, `stage_bench_car.py`, HR-066) |
| **Baccarat (DR-052/055/060), real card and rail primitives, step 1n lib** | full redraw six cards + boxes + prompt + history + rail **68 ms** drawn / 63 ms sheet (dev estimated 50); deal-step band 13/18/22 ms for 1/2/3 cards; clocked deal 297–309 ms spacing; bottom band push 12 ms; history 0.93 ms; rail 1.7 ms; five seats' habit + settle 0.18 ms, ~92 B (`baccarat_bench.py`, HR-052/055/060) |
| **Caribbean Stud layout (DR-026) and reveal (DR-029), real card primitives, step 1i lib** | 10-card full redraw **93.6 ms** drawn / 91.4 ms from a card sheet (10 cards ≈ 39 ms, three size-2 strings ≈ 21 ms, push 18.5 ms); reveal step (72-row dealer band, 5 cards) 25.8 / 28.4 ms; raise/fold two bands 22.4 / 32.7 ms; **a face-down card from the sheet ≈ 3.5 ms vs ≈ 0.5 ms drawn**; gc pause with a blackjack-class heap 11.5 ms; `poker.evaluate` 1.0 ms (5 cards), 22.4 ms (7 cards); two 5-card hands 80 B (`stud_bench.py`, HR-026, HR-029) |
| **Step 1i (slots removed, trimmed sheets/art/lcd)** | boot **78.0 KB** free in the real live run (`pocket.py` run plain; the scripted-bench figure of 66.9–68.3 KB includes the mount and the fake-buttons module, so compare scripted with scripted: 1h 65.1, 1g 75.9 scripted); blackjack in play ~54 KB after gc; no leak; **gc pause 11 ms** without slots; `draw_all` 47.6–48.3 ms; key→banner 94 ms with no sheet, **83.6 ms with a card sheet present**; card from sheet 3.4–3.9 ms; `sheets.member()` 0.15 ms; blit miss 0.3 ms after the first probe (`stage_bench.py`, `stage_pocket_bench.py`, `stage_micro.py`) |
| **`gc.collect()` pause, in game** | **28–29 ms with slots loaded, 21 ms at the menu** (`pocket_scripted.py` + instrumented `fakes/buttons.py`). Longer than a 20 ms animation frame: an automatic collection mid-spin is a visible hitch, so collect before an animation starts and allocate nothing inside it |
| **Step 1h (sheets, no sheet files) vs step 1g, real program** | boot 75.9 → 65.1 KB; after `import slots` 46.5 → 36.9; mid-spin print 36.4 → 9.5–13.0 (mostly garbage); after a spin + gc 28.3–28.9 KB stable over three spins (no leak); **garbage per spin ~7 KB**; blackjack `draw_all` +2 ms, banner +5 ms (HR-F04) |
| **RAM, real program end to end** (`pocket_scripted.py`, scripted keys, nothing else loaded) | boot 75,920; after `import slots` 46,496; **mid-spin 36,432**; back at the menu 67,328. Fallback B (three 6,272-byte window buffers) holds with 16 KB over the 20 KB alarm line |
| Sprite sheet vs per-file (DR-024, `sheet_bench.py`) | card from an open sheet **2.9 ms** (0.9 read + 2.0 keyed blit); per-file card 6.6 ms cached (was 5.6 with fewer files in `/assets`); reel 8 rows from an open sheet **0.26 ms** vs 3.7 ms open per symbol change; sheet open 3.2 ms; writing a 237 KB sheet to flash 4.2 s |
| Five-item scrolling menu (DR-022, step 1e), real `pocket.py` code | entry 124 ms; move within the window 55 ms (max 58); move that scrolls 63 ms (max 66); 66.8 KB free after (`menu_scroll_bench.py`) |
| Menu with photo background (D-007, step 1d), real `pocket.py` code | image read **once** on entry, 20.9 ms; menu entry 92–104 ms total (read 21 + show 18 + ~60 ms plates and size-2 text); joystick move 45.6 / 49 ms (two 48-row slices re-read from flash ≈ 4.5 ms each + two band pushes); 68.5 KB free after (`menu_bench.py`) |
| Split as built (step 1c), scripted play | Y redraw 51.5 ms; hit/double on a split hand 40–42 ms; key→banner 99.6 / 103 ms; round-ending stand incl. save 213 / **256 ms**; 59.6 KB free after (`split_play_bench.py`, HR-016) |
| Split layout (DR-016), two hands in the 142-row player band, code-drawn cards | 2+2 cards 38 ms; 3+2 42 ms; **4+4 worst 52.6 ms** vs 36.6 ms for one 4-card hand today; one code-drawn card 3.9 ms; second hand 64 bytes RAM (`split_bench.py`, HR-016) |

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
