# HR-F01: Finding. The board runs stock Pico firmware and uses 1.4 MB of its 16 MB flash

- **Raised by:** microcontroller expert, 2026-10-03
- **Type:** finding (PM treats as a decision request)
- **Urgency:** low. Nothing planned so far needs more than 1.4 MB. Decide before John makes a lot of art, not before the dev writes code.

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
MicroPython publishes a build for the Waveshare RP2040-Plus (there are 4 MB and 16 MB variants; take the 16 MB one). I will fetch the exact file, check its name and size, and write the steps into this file before John does anything. The steps will be, in outline:
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
