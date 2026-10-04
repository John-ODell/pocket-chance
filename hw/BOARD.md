# Board and bench notes

_Maintained by the microcontroller expert. State what is on the desk and how you know._

| Item | Value | How verified |
|---|---|---|
| Board | Waveshare RP2040-Plus, 16 MB flash | USB VID:PID 2e8a:0005, unique id `e46320366357502c`. Flash reads at 2, 4, 8 and 15 MB offsets return erased 0xFFFFFFFF and do not mirror the start, so the chip is larger than 2 MB (`hwtest/flash_probe.py`, 2026-10-03). 16 MB exactly is from the box; the probe cannot distinguish 8 from 16 |
| Display HAT | Waveshare Pico LCD 1.3", ST7789, 240x240 | John; driver init from `main_monolith.py` produced timed frames at 62.5 MHz (`hwtest/frame_full.py`); John's visual check of the colour pattern pending |
| Firmware | **MicroPython v1.29.0 (2026-08-24), build `WAVESHARE_RP2040_PLUS-FLASH_16M`**, `machine='Waveshare RP2040-Plus 16MB with RP2040'`, mpy 4870, `_thread='unsafe'`. John flashed it 2026-10-03 (HR-F01). Before that: stock Pico build v1.22.2 | `os.uname()`, `sys.implementation` (`hwtest/board_info.py`, 2026-10-03) |
| CPU clock | 125 MHz on both firmwares (not the 133 MHz in README) | `machine.freq()` |
| Peripheral clock | **48 MHz from the USB PLL on v1.29.0** (`CLK_PERI_CTRL=0x840`), which caps SPI at 24 MHz. v1.22.2 used the 125 MHz system clock. Fix measured in `hwtest/clk_peri_fix.py`; see `hw/BUDGET.md` | `hwtest/clk_peri.py` |
| Filesystem | LittleFS, **15,728,640 bytes total (15 MB)**, 15,720,448 free, 4 KB blocks (3840 blocks). Was 1,441,792 bytes (1.4 MB) on the stock build | `os.statvfs('/')`, `rp2.Flash().ioctl` |
| Files on board | **none** since 2026-10-04 (ruling D-003). The old `/main.py` (32,768 bytes, sha1 `37f2d3f1…49f6`) was erased after its hash matched `backups/2026-10-03/main.py`, `main_monolith.py` and git commit `40dcfc0`. **The screen stays dark at boot until the dev's program is uploaded; that is expected.** | `mpremote fs rm :main.py`; `os.listdir('/') == []` after soft reset |
| Serial port | `/dev/cu.usbmodem112301` ("MicroPython Board in FS mode") | `mpremote connect list` |
| Host tool | mpremote 1.29.0 at `~/.local/bin/mpremote` | `mpremote version` |
| Last backup | `backups/2026-10-03/main.py` | `mpremote fs cp -r : backups/2026-10-03/` |
| Free RAM at boot | 222,720 bytes free, largest allocatable block 199,129 | `hwtest/ram_free.py` |
| ADC3 / GPIO29 | reads 7770/65535 = 1.17 V after the Pico's x3 divider. Not a believable VSYS, so this board probably does not wire GPIO29 to VSYS like a Pico. Check the schematic in `../Pico_Reference/` before relying on it | `hwtest/pins_idle.py` |

## Pin map: VERIFIED on this board, 2026-10-04
All nine inputs idle high with pull-ups (`pins_idle.py`), and every one answered on its own GPIO when John pressed it (`bounce.py` 45 s capture; `pin_hunt.py` 30 s scan of all free GPIOs for up/down). The LCD pins are confirmed by the display: pattern shown, orientation and colour order read by John (`byteorder.py`). `main_monolith.py` runs unchanged on the RP2040-Plus.

| Function | GPIO | How verified |
|---|---|---|
| LCD DC / CS / SCK / MOSI / RST / BL | 8 / 9 / 10 / 11 / 12 / 13 | frames timed; John read the pattern: upright, left half red |
| Buttons A / B / X / Y | 15 / 17 / 19 / 21 | each pressed, each landed on its pin; 3–7 presses each |
| Joystick up / down | 2 / 18 | `pin_hunt.py`: only GP2 then GP18 went low, 3 presses each |
| Joystick left / right / press | 16 / 20 / 3 | `bounce.py`: 1 press each on the expected pin |

Orientation: holding the board landscape with USB-C and joystick on the left, buttons on the right, framebuffer (0,0) is the player's top-left. Physical top-to-bottom order of the four buttons is not yet tied to A/B/X/Y (John's note "A B C D top to bottom" is unconfirmed; `bounce.py` now prints press order for a future check).

## Serial port lock
Viper IDE (Chrome) holds `/dev/cu.usbmodemXXXX` even when its tab is only open. `lsof /dev/cu.usbmodem*` shows the holder. John must Disconnect **and** close the tab before mpremote can connect.

## Log
- 2026-10-03 (early): mpremote present. Board not visible over USB. Nothing done.
- 2026-10-03: board appeared; Chrome held the port until John closed Viper. Backed up `/main.py` to `backups/2026-10-03/`. Ran read-only `board_info.py`, `flash_probe.py`, `pins_idle.py`; benches `spi_clock.py`, `ram_free.py`, `frame_full.py`, `frame_partial.py`, `core2.py`, `flash_read.py`; `flash_write.py` created and removed `/_hwtest_tmp.json` and `/_hwtest_tmp.new` only, `os.listdir('/')` afterwards shows `main.py` alone. `byteorder.py` left a red/colour test pattern on the screen for John to read. **Board state:** filesystem unchanged (`/main.py` only), no soft reset yet, test pattern on screen, awaiting John's visual answer and the button-press capture.
- 2026-10-03 (late): visual check and button capture cancelled for the night. John reflashed to v1.29.0 16 MB (HR-F01). I restored `/main.py` from the backup and verified its sha1 on the board, reran every bench (RAM, flash, pins unchanged; SPI regressed to 24 MHz), diagnosed and tested the `clk_peri` fix, soft-reset. **Board state at hand-over:** v1.29.0, `/main.py` only, old menu running, USB serial free. `CLK_PERI_CTRL` is left at `0x800` (the fixed state) because a soft reset does not clear it; the next unplug returns it to the shipped `0x840`. Pending: John's byte-order/orientation look (`byteorder.py`), button capture (`bounce.py`), ruling on the `clk_peri` fix.
- 2026-10-04: board power-cycled by John, `CLK_PERI_CTRL` back to `0x840`, port now `/dev/cu.usbmodem212301`. Ran `byteorder.py` (John: TOP on top, L on left, LEFT half red → upright, big-endian), `bounce.py` 45 s (all buttons + left/right/press mapped, zero bounce), a second `bounce.py` run that crashed on my edit error and recorded nothing, then `pin_hunt.py` 30 s (up=GP2, down=GP18). Soft reset at the end. **Board state:** v1.29.0, `/main.py` only, old menu running, clocks at shipped defaults, nothing written to the filesystem.
- 2026-10-04 (later): ruling D-003. Verified sha1 `37f2d3f1…49f6` on four copies (backup, tree, git `40dcfc0`, board), then `mpremote fs rm :main.py`, nothing else removed. After soft reset `os.listdir('/')` is `[]`, 15,720,448 bytes free, `CLK_PERI_CTRL` back at `0x840`. Then ran `fast_pattern.py`: applied the clk_peri fix and drew colour bars, a 1-px checker band, text and a border at a real 62.5 MHz, 100 frames at 18.3 ms (54.5 fps); left on screen for John's eyeball check. **John: clean**, no speckles, tearing or wrong colours at 62.5 MHz on v1.29.0. Soft reset afterwards. **Board state at hand-over:** v1.29.0, empty filesystem (15,720,448 bytes free), idle at the REPL with a dark screen, USB serial free. `CLK_PERI_CTRL` is `0x800` (fixed state) until the next unplug, which is harmless; the dev's program will set it anyway under DR-015.
