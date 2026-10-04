# Board and bench notes

_Maintained by the microcontroller expert. State what is on the desk and how you know._

| Item | Value | How verified |
|---|---|---|
| Board | Waveshare RP2040-Plus, 16 MB flash | USB VID:PID 2e8a:0005, unique id `e46320366357502c`. Flash reads at 2, 4, 8 and 15 MB offsets return erased 0xFFFFFFFF and do not mirror the start, so the chip is larger than 2 MB (`hwtest/flash_probe.py`, 2026-10-03). 16 MB exactly is from the box; the probe cannot distinguish 8 from 16 |
| Display HAT | Waveshare Pico LCD 1.3", ST7789, 240x240 | John; driver init from `main_monolith.py` produced timed frames at 62.5 MHz (`hwtest/frame_full.py`); John's visual check of the colour pattern pending |
| Firmware | **Stock Raspberry Pi Pico build** of MicroPython v1.22.2 (2024-02-22, GNU 13.2.0 MinSizeRel), `machine='Raspberry Pi Pico with RP2040'`, mpy 4614 | `os.uname()`, `sys.implementation` (`hwtest/board_info.py`, 2026-10-03) |
| CPU clock | 125 MHz (not the 133 MHz in README) | `machine.freq()` |
| Filesystem | LittleFS, **1,441,792 bytes total (1.4 MB)**, 1,388,544 free, 4 KB blocks. The stock Pico build only maps 2 MB of flash; 14.6 MB is unused. See `hw/reviews/HR-F01.md` | `os.statvfs('/')`, `rp2.Flash().ioctl` (352 blocks x 4096) |
| Files on board | `/main.py` only, 32,768 bytes, **byte-identical** to `main_monolith.py` (sha1 `37f2d3f1…49f6`) | `mpremote fs ls`, `cmp` after backup |
| Serial port | `/dev/cu.usbmodem112301` ("MicroPython Board in FS mode") | `mpremote connect list` |
| Host tool | mpremote 1.29.0 at `~/.local/bin/mpremote` | `mpremote version` |
| Last backup | `backups/2026-10-03/main.py` | `mpremote fs cp -r : backups/2026-10-03/` |
| Free RAM at boot | 222,720 bytes free, largest allocatable block 199,129 | `hwtest/ram_free.py` |
| ADC3 / GPIO29 | reads 7770/65535 = 1.17 V after the Pico's x3 divider. Not a believable VSYS, so this board probably does not wire GPIO29 to VSYS like a Pico. Check the schematic in `../Pico_Reference/` before relying on it | `hwtest/pins_idle.py` |

## Pin map
Verified at idle: all nine inputs read high 200/200 samples with pull-ups, so no shorts and no stuck key (`hwtest/pins_idle.py`). The LCD pins are confirmed by the display driving. **Which button is which GPIO is only confirmed when John presses them** (`hwtest/bounce.py`, pending).

| Function | GPIO | Status |
|---|---|---|
| LCD DC / CS / SCK / MOSI / RST / BL | 8 / 9 / 10 / 11 / 12 / 13 | working (frames timed; visual check pending) |
| Buttons A / B / X / Y | 15 / 17 / 19 / 21 | idle-high verified; press mapping pending |
| Joystick up / down / left / right / press | 2 / 18 / 16 / 20 / 3 | idle-high verified; press mapping pending |

## Serial port lock
Viper IDE (Chrome) holds `/dev/cu.usbmodemXXXX` even when its tab is only open. `lsof /dev/cu.usbmodem*` shows the holder. John must Disconnect **and** close the tab before mpremote can connect.

## Log
- 2026-10-03 (early): mpremote present. Board not visible over USB. Nothing done.
- 2026-10-03: board appeared; Chrome held the port until John closed Viper. Backed up `/main.py` to `backups/2026-10-03/`. Ran read-only `board_info.py`, `flash_probe.py`, `pins_idle.py`; benches `spi_clock.py`, `ram_free.py`, `frame_full.py`, `frame_partial.py`, `core2.py`, `flash_read.py`; `flash_write.py` created and removed `/_hwtest_tmp.json` and `/_hwtest_tmp.new` only, `os.listdir('/')` afterwards shows `main.py` alone. `byteorder.py` left a red/colour test pattern on the screen for John to read. **Board state:** filesystem unchanged (`/main.py` only), no soft reset yet, test pattern on screen, awaiting John's visual answer and the button-press capture.
