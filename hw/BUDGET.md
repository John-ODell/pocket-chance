# Hardware budget

_Maintained by the microcontroller expert. The dev designs against this file. Every number carries its source: `measured` (script + date), `datasheet`, or `estimate`. Nothing here is measured yet (2026-10-03: board not reachable). Scripts for each row are in `hwtest/`; see `hwtest/README.md`._

## Fixed facts
| Item | Value | Source |
|---|---|---|
| CPU | RP2040 dual Cortex-M0+, up to 133 MHz | product description |
| SRAM | 264 KB | product description |
| Flash | 16 MB on board | John (verified on the box) |
| Display | 240 x 240, RGB565 | old driver |
| One full frame | 240 x 240 x 2 = **115,200 bytes** | arithmetic |
| Framebuffer | one frame in RAM: ~115 KB, which is about 44% of SRAM | arithmetic |

## To be measured
| Item | Value | Source |
|---|---|---|
| Firmware / MicroPython version | ? | |
| Filesystem size actually available | ? (stock Pico builds use 2 MB) | |
| SPI clock the panel accepts | ? (old code requests 100 MHz) | |
| Full-frame push time | ? | |
| Sustainable fps, full redraw | ? | |
| Sustainable fps, partial redraw | ? | |
| Free RAM after framebuffer | ? | |
| Flash read speed (streaming) | ? | |
| Flash write time and safe frequency | ? | |
| Button and joystick bounce | ? | |
| Idle and backlight battery draw | ? | |

## Rules of thumb for the dev until numbers exist
- Assume nothing about frame rate. Design so the game works at 10 fps and looks better at more.
- Do not allocate in the draw loop. Preallocate buffers.
- Full-screen assets stream from flash. They do not live in RAM.
