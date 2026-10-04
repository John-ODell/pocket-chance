# DR-050: Replace the clk_peri register poke with machine.freq(125 MHz, 125 MHz)

- **Status:** pending
- **Filed by:** senior dev
- **Date:** 2026-10-05
- **Blocks:** nothing (the poke works); a clean-up that removes a trap
- **Needs HW review:** no. Already measured by the expert (hw/reviews/HR-F05.md): same 17.9 ms full frame as the poke, `CLK_PERI_CTRL` 0x820, `SPI` repr honest, PWM and USB unaffected.

## The decision
Whether `lib/clocks.py` (three raw register writes, DR-015) is replaced by the supported MicroPython call `machine.freq(125_000_000, 125_000_000)`, which on v1.29.0 points the peripheral clock at the 125 MHz system PLL.

## Why it matters
The poke works but leaves MicroPython's idea of the peripheral clock wrong, so `SPI(1, 62_500_000)` prints `baudrate=24000000` and every requested baud is really 2.6x (HR-015). With `machine.freq(125_000_000, 125_000_000)` the cached clock follows: the repr says 62,500,000 and means it, and a fallback of 31.25 MHz is simply `31_250_000`. One supported line instead of a module of register addresses.

## Options
### A. `machine.freq(125_000_000, 125_000_000 if FAST_SPI else 48_000_000)` in `pocket.py`, delete `lib/clocks.py` (recommended)
- Called exactly where `fast_peripherals()` is called now, before `LCD()`. `FAST_SPI = False` gives the shipped 48 MHz source (24 MHz SPI, 46 ms frame), so the off switch keeps its meaning. `SPI_BAUD` stays `62_500_000`; the documented fallback becomes `31_250_000`.
- Boot prints the measured first `show()` time (`RESULT first show us=...`) instead of `is_fast`, which is what actually tells us the speed.
- Tests: the fake `machine.freq` accepts the two arguments; the `clocks` test goes; `check_upload`'s record drops `/lib/clocks.py` and the step says to delete it from the board.
- Docs: `docs/HARDWARE.md` "The one trap" is rewritten (no 2.6x rule, no register addresses; the one line and the off switch), `SETUP.md` drops `lib/clocks.py` from the copy list, `README.md` line about `lib/clocks.py` changes.
- Pros: supported API, honest repr, less code on the board, one fewer file for John.
- Cons: a power cycle resets it like the poke (so it stays a boot-time call); behaviour on other MicroPython versions is the expert's HR-F05 finding, not a guarantee.

### B. Keep the poke
- Cons: keeps the 2.6x trap and raw register writes.

## Recommendation
Option A. Bench from the mount first, as the expert offers.

## What John would have to do or accept
After the upload, `lib/clocks.py` is deleted from the board; nothing visible changes. `FAST_SPI = False` still exists if the screen ever looks wrong.
