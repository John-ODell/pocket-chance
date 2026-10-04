# hwtest: board measurement scripts

**Note (step 1n onward):** `lib/clocks.py` no longer exists on the board (DR-050). Benches that `from clocks import fast_peripherals` need `machine.freq(125_000_000, 125_000_000)` instead, or a staged `clocks.py`; `baccarat_bench.py` and `pico2_check.py` already use `machine.freq`.

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
| pins_reserved.py | read-only: GPIO 0,1,4-7,14,22-29 with pull-up then pull-down (floating vs driven), ADC on 26-29; which pins the Plus reserves | inputs only |
| load_hold.py | for John's multimeter: backlight 100 %, full-frame pushes for 60 s, then backlight back to 20000 | LCD |
| freq_peri.py | HR-F05: does `machine.freq(125_000_000, 125_000_000)` replace the `CLK_PERI_CTRL` poke? State found, reported SPI baud, timed frame, backlight PWM, then back to (125M, 48M), then restores the state found | clock settings only; LCD |
| pico2_check.py | **Pico 2 / RP2350 only**: firmware, clock, flash, RAM, clk_peri source at the RP2350 register (read-only), SPI granted and full-frame time as shipped / freq(125M,125M) / freq(150M,150M), restores the shipped clocks. Never run clk_peri_fix.py or lib/clocks.py on an RP2350 | reads a register; LCD; `machine.freq` |
| clk_peri.py | which clock feeds the peripherals (why SPI is 24 MHz on v1.29.0); tries `machine.freq()` | reads `CLK_PERI_CTRL`; `machine.freq()` |
| clk_peri_fix.py | re-sources `clk_peri` to `clk_sys` and times a frame at the real 62.5 MHz | **writes `CLK_PERI_CTRL`**; survives soft reset, cleared by power cycle |
| slots_spin_bench.py | DR-020 as described: per frame, two `Assets.blit` reads from flash per reel into a 56x56 compose, copy to framebuffer, `show_rect`; 3 reels and 1 reel; DR-021 blink; same at 24 MHz | writes and removes `/assets/_bench_sym0/1.565`; LCD; toggles clk_peri and restores it |
| slots_spin_bench2.py | DR-020 fixed path: symbols held in RAM, reads only when a symbol scrolls in, compose pushed directly; parts (open+read, stat, keyed blit); 62.5 and 24 MHz | same as above |
| outs_bench.py | DR-042 river hint: 45 unseen cards x 6-card `evaluate` + `compare` against the player's 7-card value; bounds the 990-pair version | RAM only |
| holdem_bench.py | DR-043/044/047 before the Hold'em screen exists: nine cards in three rows, four 60x56 seat boxes (text strips and 24x24 chip blits), 36 px bottom band; full redraws, community/dealer band pushes, strip draws, `poker.evaluate` per seat on 5/6/7 cards, a six-hand showdown; drawn and with temp card and chip sheets | LCD; writes and removes `/assets/cards.565`, `/assets/chips.565` |
| stud_rail_bench.py | DR-041: five Stud AI seats, `poker.evaluate` + `stud_rules.advice` per seat, the 12-row chip rail draw and push, seat RAM | LCD |
| holdem_play_bench.py (+ fakes_holdem/, stage_bench_holdem.py) | Hold'em as built: real `holdem.Screen` with scripted keys; deal, flop/river pushes, outs hint, seats-before-first-flip, fold, next, help load/drop, save; same seed with 4 and 0 seats. Create `Assets` BEFORE importing the game (the import fragments the heap). Key script note: the showdown drains one press | writes and removes `/_bench_save.*`; LCD |
| stage_from.sh | `./hwtest/stage_from.sh <ref> <paths…>`: copies files from a git ref into `hwtest/stage/` for a bench-before-upload | local |
| stud_play_bench.py | Caribbean Stud as built: real `stud.Screen` with scripted keys; deal redraw, reveal flip spacing (stamps `show_band`), raise/fold/next, paytable load/drop retention, save; drawn and with a temp card sheet | writes and removes `/_bench_save.*` and `/assets/cards.565`; LCD |
| stage_bench_stud.py (+ fakes_stud/) | real `pocket.py` end to end with a Stud key script (enter, hands, paytable, back), RAM and gc pause at chosen pauses; staged files if `hwtest/stage/` exists, else the board's. **Note:** a reveal drains one press, so do not script a key right after a raise | LCD; snapshots/restores John's saves |
| menu_style_a_bench.py | the BUILT style-A menu from the stage (`pocket_nomain.py` = staged pocket.py minus its `main()` call, made by hand; import it, do not exec the source string: that fragments the heap before the framebuffer): entry, moves, scroll, retained RAM, style A then photo | LCD; needs the stage |
| menu_style_bench.py | DR-072 menu styles before the menu code exists: A's shade/pills/labels/entry and two-band scroll, B's bulbs, chase bands and show_rect sides, C's panels; ellipse costs | LCD |
| caribbean_play_bench.py | the Caribbean flop game Screen from `hwtest/stage/` (branch flop-game): deal, call high/low/fold showdowns, next, help, RAM per hand, stamped band/show/save times, 0-vs-4-seat identity. Saves to `/_bench_save.*` | LCD; needs the stage |
| stage_bench_car.py + fakes_car/ | the REAL pocket.py from the stage with scripted Caribbean keys (deal and showdown each eat one press: LEFT fillers), RAM at chosen polls, John's saves restored | LCD; needs the stage |
| baccarat_bench.py | DR-052/055/060 before the baccarat screen exists: Stud's bands, three cards per hand, bet boxes, prompt, history squares, seat rail; full redraw, deal-step bands, clocked deal cadence, bottom band, seats' habit/settle; drawn and with a temp card sheet. Uses `machine.freq` (no `clocks.py` on the step-1n board) | LCD; writes and removes `/assets/cards.565` |
| stud_bench.py | DR-026/029 before the Stud screen exists: ten cards in DR-026's bands with the real blackjack card primitives; full redraw, reveal step with a forced gc in the 300 ms gap, raise/fold bands, `poker.evaluate`; code-drawn and with a temp card sheet. Stages `lib/poker.py` from `hwtest/stage/` | LCD; writes and removes `/assets/cards.565` |
| stage_bench.py, stage_pocket_bench.py, stage_micro.py (+ fakes_bj/) | bench a build BEFORE uploading it: copy the candidate `lib/*.py` and `pocket.py` into `hwtest/stage/` (not committed; create it per run), they go first on `sys.path` from the mount so the real program runs them while the board's files stay put. `stage_micro` writes and removes a temp `/assets/cards.565` | LCD; temp `/assets/cards.565` |
| pocket_scripted.py (+ fakes/buttons.py) | runs the REAL `/pocket.py` end to end with scripted keys in place of the pin reader, so the game's own RESULT lines are the true RAM figures with zero harness overhead. snapshots and restores `/save.json` and `/save.bak` around the run | LCD; writes `/save.json` via the game |
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
