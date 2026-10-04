# hwtest: board measurement scripts

Run from the Mac, from the repo root, with Viper IDE disconnected **and its tab closed** (Chrome holds the port otherwise; `lsof /dev/cu.usbmodem*` shows who has it). Nothing is stored on the board: the folder is mounted read-only over the serial link and the scripts import from it.

    P=/dev/cu.usbmodem112301
    mpremote connect $P mount hwtest exec "import board_info"

Finish with `mpremote connect $P soft-reset`. Each script prints `RESULT key=value` lines; the figures live in `hw/BUDGET.md`.

| Script | Measures | Touches |
|---|---|---|
| board_info.py | firmware, CPU clock, filesystem size, flash block device, RAM | read-only |
| flash_probe.py | whether the flash chip is bigger than the 2 MB the stock firmware maps | read-only (XIP reads) |
| pins_idle.py | all 9 inputs at idle with pull-ups; ADC3/GPIO29 | read-only |
| spi_clock.py | SPI baud granted for each request, bytes/s on the wire | LCD |
| frame_full.py | full-frame push time, fps; Python fill vs wire; busy scene | LCD |
| frame_partial.py | partial redraw fps: scratch window, full-width band, 8x8 | LCD |
| ram_free.py | free RAM before/after framebuffer, largest block, second buffer, sprite cache headroom | RAM only |
| flash_read.py | `readinto` speed from the filesystem at 480 B, 4800 B, 32 KB chunks | read-only (reads /main.py) |
| flash_write.py | save time, plain and tmp+rename | writes and removes `/_hwtest_tmp.json`, `/_hwtest_tmp.new` |
| core2.py | `_thread`: core 1 pushing frames while core 0 draws | LCD |
| byteorder.py | **visual, needs John**: which byte order the panel shows as red; orientation | LCD, leaves pattern on screen |
| bounce.py | **needs John pressing keys for 8 s**: edges, bounce within 5 ms, press lengths, pin-to-key mapping | read-only |

`lcdbench.py` is the shared driver: same pins and init sequence as `main_monolith.py`, plus window writes. It is a bench tool, not for the dev to import.

Results so far: 2026-10-03, MicroPython v1.22.2 stock Pico build. See `hw/BUDGET.md`.
