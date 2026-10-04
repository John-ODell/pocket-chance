# HR-F05: Finding. `machine.freq(mcu, peripheral)` replaces the `CLK_PERI_CTRL` register poke

- **Raised by:** microcontroller expert, 2026-10-04, at the PM's request after the PCB maker found the documented API
- **Type:** finding, for the dev. Recommendation: file a decision request to replace `lib/clocks.py` with the documented call. Not urgent; the poke works.
- Method: `hwtest/freq_peri.py` on the RP2040-Plus, MicroPython v1.29.0, real `lib/lcd.py`; the clock state found was restored afterwards.

## Measured
| State | `CLK_PERI_CTRL` | Source | SPI baud MicroPython **reports** for a 62.5 MHz request | **Timed** full frame | Backlight PWM |
|---|---|---|---|---|---|
| As found (the poke's state, sticky across soft resets) | `0x800` | `clk_sys` | 24,000,000 (wrong) | 17.9 ms | 1000 Hz |
| **After `machine.freq(125_000_000, 125_000_000)`** | `0x820` | `pll_sys` (same 125 MHz) | **62,500,000 (honest)** | **17.9 ms** | 1000 Hz |
| After `machine.freq(125_000_000, 48_000_000)` (the documented default) | `0x840` | `pll_usb` | 24,000,000 | 46.0 ms | 1000 Hz |

USB serial stayed up throughout (the result lines arrived). `machine.freq()` still reports 125,000,000. The two-argument signature is accepted on v1.29.0, matching the quickref: `machine.freq(MCU_frequency[, peripheral_frequency=48_000_000])`, peripheral either 48 MHz or equal to the MCU frequency.

## Reading
1. **Same speed as the poke, by a documented call.** 17.9 ms per frame either way.
2. **MicroPython's cached clock is updated**, so `SPI(1, 62_500_000)` really means 62.5 MHz and prints it. The "every requested baud is really 2.6x" trap (HR-015 limit 2) disappears, and `12_000_000` no longer means 31.25 MHz; request `31_250_000` for that.
3. **The source becomes `pll_sys` rather than `clk_sys`.** At the default clocks these are the same 125 MHz. If anyone ever calls `machine.freq(other)` the peripheral clock follows only if they pass it again, which is the documented behaviour.
4. **Not sticky in a new way:** like the poke, it is a runtime setting; a power cycle returns to the 48 MHz default and `pocket.py` must make the call at every boot, as it does now with `fast_peripherals()`. A soft reset keeps it.
5. Per the quickref, **existing `SPI`/`UART` objects change baud when the peripheral clock changes**, so the call must come before `LCD()` creates its `SPI`, exactly where `fast_peripherals()` is today.
6. On the RP2350 board (HR-033) the same call should work with `machine.freq(150_000_000, 150_000_000)`, or `(125_000_000, 125_000_000)` to keep today's timings; it removes the need to know `CLOCKS_BASE` at all, and makes the build-flag route optional.

## Recommendation for the dev
Replace `lib/clocks.py` with, in `pocket.py` before the LCD: `machine.freq(125_000_000, 125_000_000 if FAST_SPI else 48_000_000)`; delete the register constants; keep `FAST_SPI`; change the boot `RESULT` line to print the timed first `show()` so a wrong clock is visible. Update HR-015's limit 2 (the 2.6x note) to "obsolete after DR-0xx". One upload step (`pocket.py`, delete `/lib/clocks.py`), bench from the mount first as usual.

## Not measured
Behaviour on v1.22.2 or other builds (irrelevant now); the RP2350 (no board).
