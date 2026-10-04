# DR-015: Adopt the expert's peripheral-clock fix so the screen runs at full speed

- **Status:** pending
- **Filed by:** senior dev
- **Date:** 2026-10-04
- **Blocks:** nothing now. It decides whether the screen driver (`lib/lcd.py`, after DR-001) contains the fix.
- **Needs HW review:** yes. The expert found, measured and proposed this fix; the data is in `hw/BUDGET.md` ("READ FIRST" section and the SPI clock table) and `hw/reviews/HR-F01.md`. Script: `hwtest/clk_peri_fix.py`.

## The decision
Whether the game applies a three-line register write at start-up that makes the screen connection 2.6 times faster, or whether we live with the slower speed the new firmware ships with.

## Why it matters
The new MicroPython (v1.29.0, which gave us the 15 MB filesystem) runs the board's peripheral clock from a 48 MHz source instead of the 125 MHz system clock. That caps the screen link (SPI) at 24 MHz: a full-screen redraw takes **46 ms (about 20 frames per second)** instead of **18.5 ms (about 44)**. Cards are fine at 20 fps. Slot reels and smooth animation later would not be. The fix recovers the old speed in software, with nothing to solder or reflash.

## What the fix does
It writes to one hardware register (`CLK_PERI_CTRL`, the control for the peripheral clock), telling the chip to feed the peripherals from the 125 MHz system clock. The RP2040 datasheet documents this (section 2.15.3.2). Three writes: switch the clock off, pick the new source, switch it on. That is what the chip's own SDK does in C; MicroPython v1.29.0 just chose the other source.

What depends on this clock: **only SPI and UART**. USB (which Viper IDE uses), I2C, PWM (backlight), timers and the CPU do not. This project uses no UART. So the only visible effect is the screen getting faster.

## Options
### A. Apply the fix at boot, in one small function, with an off switch (recommended)
- What it is: a module `lib/clocks.py` with one function, `fast_peripherals()`. It reads the register first and only writes if the source is not already the system clock, so it is safe to call twice or after a soft reset. It is called once, at the top of start-up, before the screen driver is created. One constant at the top of the entry file (`FAST_SPI = True`) turns it off; set it to `False` and the game runs at 24 MHz with no other change.
- Pros: 44 fps full redraw instead of 20; 138 fps band redraws instead of 79 (measured). One place to look if anything is ever odd. Easy to disable.
- Cons: a raw register write in Python. If a future MicroPython changes how this register works, the function might need updating (it checks the value it reads, so a changed layout would be noticed rather than silently poked).
- Cost: about 15 lines. No RAM to speak of.

### B. Do not touch the register; design for 24 MHz
- Pros: no low-level code.
- Cons: screen redraws take 2.6 times longer forever. Blackjack still works (20 fps is playable, says the expert). Slot animation later would be limited.

### C. Switch to a firmware that does not have the issue
- Cons: the stock Pico build (which had the fast clock) only sees 1.4 MB of flash. Building our own firmware is out of scope. Rejected.

## Risks, and what a failure looks like
- **Wrong write:** the screen would stay blank or show garbage, but the board would still talk to Viper IDE over USB (USB has its own clock), so John can always upload a fixed file or set `FAST_SPI = False`. The expert ran the exact write on the board; the screen worked and a 50-frame timing run measured 17.2 ms per frame.
- **The panel at 62.5 MHz:** the old program already drove it at 62.5 MHz for years on the old firmware, and the expert's new runs showed no errors. John's visual confirmation of the screen test is still pending (same screen check as DR-003). If the picture looks wrong at full speed, we request 31.25 MHz instead; that is one number in the driver.
- **Soft reset keeps the fast state, unplugging resets it:** because the function runs at every start and checks before writing, both cases end the same way. No surprise.
- **MicroPython reports the wrong speed:** `SPI(...)` will print `baudrate=24000000` even when it really runs at 62.5 MHz, because it caches the old clock. We never rely on that print. The hardware test notes time a frame with `ticks_us()` instead, as the budget says.
- **Any other peripheral:** only UART is also affected, and we use none. Backlight PWM, buttons, USB and the CPU clock are untouched. `machine.freq()` stays at 125 MHz.

## Recommendation
Option A. The gain is large and measured, the write is documented chip behaviour, and the off switch is one word. I would change my mind if John's screen check shows a bad picture at full speed that 31.25 MHz does not cure, or if the expert finds a peripheral we use that depends on this clock.

Regardless of the ruling, I follow the budget's rule of thumb: the game is designed to be fine at 24 MHz and only looks smoother at 62.5 MHz.

## What John would have to do or accept
Nothing extra. If the screen ever looks wrong after an upload, the first thing to try is changing `FAST_SPI = True` to `False` in the entry file.

## Appendix
Measured by the expert (`hw/BUDGET.md`, 2026-10-03, v1.29.0): full frame on the wire 46.2 ms as shipped, 17.2 ms after the fix; `CLK_PERI_CTRL` reads `0x840` as shipped (source = USB PLL), `0x800` after (source = system clock). Register address `0x40008048`. Sketch of the function:

```python
CTRL = 0x40008048          # CLOCKS.CLK_PERI_CTRL
ENABLE = 1 << 11
AUXSRC = 7 << 5            # 0 = clk_sys

def fast_peripherals():
    v = machine.mem32[CTRL]
    if v & AUXSRC == 0:
        return False       # already on clk_sys
    machine.mem32[CTRL] = v & ~ENABLE
    utime.sleep_us(10)
    machine.mem32[CTRL] = v & ~ENABLE & ~AUXSRC
    machine.mem32[CTRL] = (v & ~AUXSRC) | ENABLE
    utime.sleep_us(10)
    return True
```
