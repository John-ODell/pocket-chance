# HR-F01: Finding. The board runs stock Pico firmware and uses 1.4 MB of its 16 MB flash

- **Raised by:** microcontroller expert, 2026-10-03
- **Type:** finding (PM treats as a decision request)
- **Urgency:** low. Nothing planned so far needs more than 1.4 MB. Decide before John makes a lot of art, not before the dev writes code.

## STATUS: DONE, with one follow-up
**John reflashed on 2026-10-03** (his own action, BOOTSEL drag-and-drop) with `WAVESHARE_RP2040_PLUS-FLASH_16M-20260824-v1.29.0.uf2` (kept, uncommitted, at `backups/firmware/`, sha256 `654744…c1ba`). Verified afterwards with `hwtest/board_info.py`: MicroPython **v1.29.0**, machine "Waveshare RP2040-Plus 16MB with RP2040", filesystem **15,728,640 bytes (15 MB)**. `main.py` restored from `backups/2026-10-03/` and verified on the board (sha1 `37f2d3f1…49f6`); the old menu runs.

**Regression found on the new firmware: SPI dropped from 62.5 MHz to 24 MHz**, so a full frame takes 46 ms instead of 18.5 ms. Cause, measured with `hwtest/clk_peri.py`: v1.29.0 feeds the peripheral clock from the 48 MHz USB PLL (`CLK_PERI_CTRL = 0x840`), and SPI can only divide that by 2. `machine.freq(125 MHz)` and `machine.freq(133 MHz)` do not change it.

**Fix found and measured, `hwtest/clk_peri_fix.py`:** three register writes at boot re-source the peripheral clock from the 125 MHz system clock; a full frame then takes 17.2 ms (58 fps). Two cautions: MicroPython's `SPI` repr keeps reporting the old 24 MHz (it caches the clock), and a soft reset does not undo the register change (a power cycle does). Full detail and the two-column frame table are in `hw/BUDGET.md`.

**Open for a ruling:** whether the dev adopts the three-line fix in `lib/lcd.py` (recommended; it needs a decision request because it is a raw register write), or designs for 24 MHz (20 fps full redraw, still playable). Also still pending from before the reflash: John's visual check of the byte-order pattern (`hwtest/byteorder.py`) and the button capture (`hwtest/bounce.py`); both are firmware-independent.

**Board state at hand-over, 2026-10-03 late:** v1.29.0, `/main.py` only, old menu running after a soft reset. The `clk_peri` register is currently in the fixed state (`0x800`) from my last test because a soft reset does not clear it; the menu therefore runs at the old speed. The next unplug returns it to the shipped state (`0x840`). Nothing else is changed.

## What I found
The board runs **MicroPython v1.22.2, the stock build for the original Raspberry Pi Pico** (`os.uname().machine` = "Raspberry Pi Pico with RP2040"). That build lays the filesystem out for a 2 MB chip. `os.statvfs('/')` reports **1,441,792 bytes total (1.4 MB), 1,388,544 free**. The flash chip itself is bigger: reads at 2, 4, 8 and 15 MB come back erased (0xFFFFFFFF) rather than mirroring the start, so the firmware is simply not using the space. 14.6 MB sits idle.

Measured with `hwtest/board_info.py` and `hwtest/flash_probe.py` (both read-only).

Also from the same probe: CPU runs at 125 MHz, not the 133 MHz in README.md. A board-specific build may or may not change that; it does not matter for this project.

## Does it matter now?
- The dev's full asset plan (DR-006) is about 0.62 MB. It fits in 1.4 MB with 0.77 MB spare.
- `main.py` is 32 KB. Code for the whole project will be well under 200 KB.
- So the project **works on today's firmware**. The 16 MB only matters for future art, sound, or many more games.

## Options
### A. Reflash with a 16 MB RP2040-Plus build (recommended, when convenient)
MicroPython publishes an official build for this exact board: https://micropython.org/download/WAVESHARE_RP2040_PLUS/ . Take the **16 MB** variant, not "Standard". Latest stable on 2026-10-03: **`WAVESHARE_RP2040_PLUS-FLASH_16M-20260824-v1.29.0.uf2`** (MicroPython v1.29.0). That jumps from v1.22.2 to v1.29.0; `framebuf`, `machine.SPI`, `os`, `json` and `_thread` are unchanged in the ways this project uses them, and I will re-run every `hwtest/` script after the flash to confirm the numbers in `BUDGET.md` still hold. Steps:
1. I back up the board again (already done today: `backups/2026-10-03/main.py`, identical to `main_monolith.py`).
2. John unplugs the board, holds **BOOTSEL**, plugs it in, releases. A drive named `RPI-RP2` appears.
3. John drags the `.uf2` onto `RPI-RP2`. The board reboots by itself into MicroPython with an empty 16 MB filesystem.
4. I restore `main.py` with `mpremote fs cp backups/2026-10-03/main.py :main.py` and re-run `board_info.py` to confirm `fs_total_bytes` is about 16 MB.
Cost: 10 minutes. The filesystem is wiped, so this must happen before John uploads art, or everything gets re-uploaded.

### B. Stay on the stock build
Works for the whole current plan. Revisit if the project grows past 1.4 MB.

## Recommendation
A, scheduled **before John starts uploading assets** so nothing is uploaded twice. Not urgent; B is safe in the meantime. I will not flash anything. Flashing is John's action, after a ruling.

## Appendix
```
RESULT sysname=rp2 release=1.22.2 version=v1.22.2 on 2024-02-22 (GNU 13.2.0 MinSizeRel) machine=Raspberry Pi Pico with RP2040
RESULT cpu_hz=125000000
RESULT fs_total_bytes=1441792 fs_free_bytes=1388544 block=4096
RESULT flash_block_dev_bytes=1441792 (ioctl count=352 size=4096)
RESULT off=2MB words=['-0000001', ...] mirrors_start=False   (same at 4, 8, 15 MB)
```
