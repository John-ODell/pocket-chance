# Hardware budget

_Maintained by the microcontroller expert. The dev designs against this file. Every number carries its source: `measured` (script + date), `datasheet`, or `estimate`. All measurements below: 2026-10-03, MicroPython v1.22.2 stock Pico build, CPU 125 MHz, SPI1 at 62.5 MHz, scripts in `hwtest/`._

## Fixed facts
| Item | Value | Source |
|---|---|---|
| CPU | RP2040 dual Cortex-M0+, running at **125 MHz** on this firmware | measured, `board_info.py` |
| SRAM | 264 KB; 222,720 bytes free to Python at boot | measured, `ram_free.py` |
| Flash chip | 16 MB (reads above 2 MB are erased, not mirrored) | measured, `flash_probe.py`; 16 vs 8 from the box |
| **Filesystem available today** | **1,441,792 bytes (1.4 MB)**, 1,388,544 free. Stock firmware. See HR-F01 | measured, `board_info.py` |
| Display | 240 x 240, RGB565 | old driver |
| One full frame | 240 x 240 x 2 = **115,200 bytes** | arithmetic |

## SPI clock
| Requested | Granted by RP2040 | Full frame on the wire | Throughput |
|---|---|---|---|
| 100 MHz (old code) | **62.5 MHz** | 18.2 ms | 50.6 Mbit/s = 6.33 MB/s |
| 62.5 MHz | 62.5 MHz | 18.2 ms | same |
| 40 MHz | 31.25 MHz | 35.7 ms | 25.8 Mbit/s |
| 20 MHz | 15.625 MHz | 70.7 ms | 13.0 Mbit/s |

measured, `spi_clock.py`. The peripheral clock is 125 MHz and SPI divides it by an even number, so 62.5 MHz is the ceiling. The panel took 62.5 MHz for every bench without error (visual confirmation from John pending). Request 62_500_000 explicitly; asking for 100 MHz gets the same thing and is misleading.

**Hard ceiling: 55 fps.** No drawing strategy beats 18.2 ms per full frame on the wire.

## Frame rate
| Strategy | Time per frame | fps | Source |
|---|---|---|---|
| Full redraw: `fill()` + `show()` | 4.2 ms Python + 18.5 ms wire = **22.7 ms** | **44** | measured, `frame_full.py`, 100 frames |
| Full redraw, busy scene (20 `fill_rect` + 10 `text` + `show`) | 26.4 ms | 38 | measured, `frame_full.py`, 50 frames |
| Full redraw with a 115 KB background streamed from flash first | 20.5–26 ms read + 4–8 ms sprites + 18.5 ms wire ≈ **45–50 ms** | **~20** | read and wire measured; sprite time is an estimate |
| Partial: 48x48 sprite over a 51x48 window, drawn in a scratch buffer and pushed | 3.9 ms (max 7.7) | 253 | measured, `frame_partial.py`, 150 frames |
| Partial: full-width band, 240x48 rows, pushed straight from the framebuffer (no copy) | 7.2 ms (max 19) | 138 | measured, `frame_partial.py` |
| Partial: 8x8 region (a digit) | 1.2 ms | 800 | measured, `frame_partial.py` |

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
| Save with tmp + `os.rename` (atomic) | **22 ms mean, 6–79 ms** | measured, 10 writes |
| Write endurance | ~100,000 erase cycles per 4 KB block, class figure for NOR flash; LittleFS spreads writes across free blocks | datasheet-class estimate |

Saving once per round is harmless (a round every 5 s for 10 hours is 7,200 writes). Saving on every button press or every frame is not.

## Second core
| Item | Value | Source |
|---|---|---|
| Baseline, one core: draw busy scene + push | 40.9 fps | measured, `core2.py`, 60 frames |
| `_thread`: core 1 pushes while core 0 draws | core 0 drew at 145 fps, core 1 pushed at 55.8 fps (wire-bound), thread exited cleanly | measured |

It works and it moves the 18.5 ms push off the drawing core, so drawing gets the full CPU. Costs: tearing (the push reads a buffer that is being drawn), the GIL in MicroPython (only one core runs Python bytecode at a time; the gain here is because `spi.write` releases it), and `_thread` is documented as experimental on rp2. Verdict: **real gain, not needed for a card game at 20–40 fps.** Recommend against it for phase 1; revisit for slots animation if needed.

## Input
| Item | Value | Source |
|---|---|---|
| All 9 inputs idle with pull-ups | high 200/200 samples each | measured, `pins_idle.py` |
| Bounce, press length, which GPIO is which key | **pending** John pressing keys during `bounce.py` | |
| Poll cost | reading 9 pins takes well under 100 µs (20 kHz sample loop in `bounce.py` reads all nine) | measured indirectly |

## Power
| Item | Value | Source |
|---|---|---|
| ADC3/GPIO29 | 1.17 V equivalent; probably **not** VSYS on this board | measured, `pins_idle.py`; check schematic |
| Backlight current at PWM levels | not measured, no meter in the loop | |
| Battery, charging | not measured; nothing on the charge circuit will be touched without John present | |

## Rules of thumb for the dev
- Request SPI at 62_500_000. Budget 18.5 ms per full push; 55 fps is the physical ceiling, 40 fps is the practical one for full redraws.
- Push bands or windows for anything that moves; full `show()` only on scene changes.
- Backgrounds stream from flash in ~21–26 ms. Do it on scene change, not every frame.
- Do not allocate in the draw loop. One 16 KB scratch buffer, preallocated, covers the largest sprite.
- Roughly 60–70 KB of RAM will be free in play. No second framebuffer.
- Save to flash once per round, atomically. Expect up to 80 ms; do it between hands, not mid-animation.
- Stay on one core.
