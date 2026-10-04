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
| bounce.py | **needs John pressing keys for DUR_S (30) s**: edges, bounce within 5 ms, press lengths, pin-to-key mapping, press order | read-only |
| pin_hunt.py | **needs John pressing one key**: every free GPIO as a pulled-up input for 30 s, reports which went low; finds a key's real pin. Skips LCD pins 8-13 and power pins 23-25, 29 | read-only |
| clk_peri.py | which clock feeds the peripherals (why SPI is 24 MHz on v1.29.0); tries `machine.freq()` | reads `CLK_PERI_CTRL`; `machine.freq()` |
| clk_peri_fix.py | re-sources `clk_peri` to `clk_sys` and times a frame at the real 62.5 MHz | **writes `CLK_PERI_CTRL`**; survives soft reset, cleared by power cycle |
| slots_spin_bench.py | DR-020 as described: per frame, two `Assets.blit` reads from flash per reel into a 56x56 compose, copy to framebuffer, `show_rect`; 3 reels and 1 reel; DR-021 blink; same at 24 MHz | writes and removes `/assets/_bench_sym0/1.565`; LCD; toggles clk_peri and restores it |
| slots_spin_bench2.py | DR-020 fixed path: symbols held in RAM, reads only when a symbol scrolls in, compose pushed directly; parts (open+read, stat, keyed blit); 62.5 and 24 MHz | same as above |
| slots_play_bench.py | slots AS BUILT (step 1g): scripted bet and spins with the real `games/slots.py`; shims its `utime` to log per-frame spent time, tags symbol-change frames, times spin, save, blink, paytable; RAM at each step | writes and removes `/_bench_save.*`; LCD |
| sheet_bench.py | DR-024: temp sprite sheets (8 symbols, 53 cards); per-card seek+read+blit from an open sheet vs today's per-file blit; reel rows from a sheet vs an open per symbol change | writes and removes `/assets/_bench_symbols.565`, `_bench_cards.565`, `_bench_card1.565`; LCD |
| blit_bench.py | HR-F03 re-check on the real `art.py`: card blit first vs cached, `background_rows`, `Assets.load`, `LCD.show_buf`; RAM headroom probe | writes and removes `/assets/_bench_card.565`; LCD |
| slots_ram_bench.py | DR-020 rev 2: real menu set up, a game module imported, then option A (6 slots) vs B (2 slots) vs 3 slots allocated; free RAM and largest block at each step | RAM only |
| menu_scroll_bench.py | DR-022: real `/pocket.py` menu code, walks the five-item list down and back, times moves within the window and moves that scroll, RAM | LCD; applies the clk_peri fix |
| menu_bench.py | D-007: runs the real `/pocket.py` menu code (its final `main()` stripped), times menu entry and joystick moves, counts image reads, RAM. Needs step 1d uploaded | LCD; applies the clk_peri fix; reads `/assets/menu_background.565` |
| split_play_bench.py | DR-016 as built: scripted deals until a pair, Y to split, plays both hands with a double, rigs an A-A split; times every redraw and key→banner | writes and removes `/_bench_save.*`; LCD; applies the clk_peri fix |
| split_bench.py | DR-016: draws two player hands side by side (2+2, 3+2, 4+4 cards) with the dev's real code and times the 142-row band; RAM of a second hand; leaves the 4+4 layout on screen | LCD; applies the clk_peri fix |
| unwedge.py | **Mac-side** (pyserial): recovers from "could not enter raw repl" after a killed mpremote run. Ctrl-C, Ctrl-B, Ctrl-D over the serial port | board soft reboot only |
| pocket_bench.py | plays 8 blackjack hands with scripted keys using the dev's real `lib/` and `games/` on the board; times every redraw path and the save; per-module RAM. Needs UPLOAD.md step 1 uploaded | writes and removes `/_bench_save.*`; LCD; applies the clk_peri fix |
| fast_pattern.py | **visual, needs John**: applies the clk_peri fix and shows colour bars, a 1-px checker band, text and a border at a real 62.5 MHz, times 100 frames, leaves it on screen | **writes `CLK_PERI_CTRL`**; LCD |

`lcdbench.py` is the shared driver: same pins and init sequence as `main_monolith.py`, plus window writes. It is a bench tool, not for the dev to import.

Results so far: 2026-10-03, MicroPython v1.22.2 stock Pico build. See `hw/BUDGET.md`.
