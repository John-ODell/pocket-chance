# Hardware reference sheet

Waveshare RP2040-Plus (16 MB) with the Waveshare Pico LCD 1.3" HAT, running MicroPython. This sheet is what we **measured and verified on a real board**. It replaces reading the manufacturer docs for everything this project touches. Detailed numbers and the scripts that produced them are in [`hw/BUDGET.md`](../hw/BUDGET.md), [`hw/BOARD.md`](../hw/BOARD.md) and [`hwtest/`](../hwtest/README.md).

Nothing here needs wiring. The HAT plugs onto the board.

## The parts

| Part | Facts |
|---|---|
| Board | Waveshare RP2040-Plus. RP2040, two Cortex-M0+ cores, **264 KB RAM**, **16 MB flash** (a 4 MB version exists), USB-C, LiPo charge header. Not a plain Pico: the pinout matched for everything we used, but GPIO29 is not wired to VSYS like on a Pico |
| Firmware | MicroPython **v1.29.0** (2026-08-24), build `WAVESHARE_RP2040_PLUS-FLASH_16M`. About **15 MB** of filesystem (LittleFS, 4 KB blocks). The stock *Raspberry Pi Pico* build also runs, but only maps **1.4 MB** of the flash |
| CPU clock | 125 MHz |
| Screen | ST7789, **240 x 240**, RGB565, on **SPI1**. 1.3" IPS |
| Input | 4 buttons (A, B, X, Y) and a 5-way joystick. All **active low** with internal pull-ups. No contact bounce seen at a 240 µs sample period |

## Pin map (all verified on the board)

| Function | GPIO |
|---|---|
| LCD DC | 8 |
| LCD CS | 9 |
| LCD SCK | 10 |
| LCD MOSI | 11 |
| LCD RST | 12 |
| LCD backlight (PWM) | 13 |
| Button A / B / X / Y | 15 / 17 / 19 / 21 |
| Joystick up / down / left / right / press | 2 / 18 / 16 / 20 / 3 |

Holding the board **landscape with USB-C and the joystick on the left** and the buttons on the right, the framebuffer's top-left pixel (0, 0) is the screen's top-left. The init commands are `0x36 = 0x70` (orientation) and `0x3A = 0x05` (16-bit colour).

Which physical button (top to bottom) carries which letter was never tied down. The code uses the pin numbers, so it does not matter.

## Colour

The panel wants **big-endian RGB565**. MicroPython's `framebuf.RGB565` stores the low byte first, so a colour value in code is the **byte-swapped** 16-bit number:

| Colour | Value in code |
|---|---|
| Red | `0x00F8` |
| Green | `0xE007` |
| Blue | `0x1F00` |
| White / black | `0xFFFF` / `0x0000` |

Use one helper (`lib/pixfmt.py`, `rgb(r, g, b)`) and never write raw 565 numbers. Image files hold big-endian pixels, so they copy into the framebuffer and out to the panel with no byte swapping. That is also the fastest path. (Waveshare's own demo calls this "BRG". It is the same byte swap, described wrongly.)

How we checked: a test pattern put bytes `F8 00` on the left half and `00 F8` on the right. The left half showed red.

## Screen speed (SPI)

| | Value |
|---|---|
| Frame size | 240 x 240 x 2 = 115,200 bytes |
| Best SPI clock | **62.5 MHz** (the RP2040 divides a 125 MHz clock by an even number, so asking for 100 MHz silently gives 62.5) |
| One full frame on the wire | **17 to 18 ms** at 62.5 MHz (about 58 fps ceiling), 46 ms at 24 MHz |
| Full redraw, simple scene | about 22 ms in practice |
| One 48-row band | about 4 to 7 ms on the wire |

### The one trap: v1.29.0 clocks SPI from the USB clock
On MicroPython v1.29.0 the peripheral clock `clk_peri` is fed from the 48 MHz USB PLL, which caps SPI at **24 MHz**. The older stock Pico build (v1.22.2) did not have this. Re-pointing `clk_peri` at the 125 MHz system clock fixes it with three register writes (`lib/clocks.py`). Only SPI and UART baud rates depend on that clock, so USB, PWM and the CPU are untouched.

Things to know about the fix:
- Call it **before** creating the SPI object.
- MicroPython remembers the old clock, so `print(spi)` still says `baudrate=24000000`. Time a frame to see the real speed. After the fix every requested baud is really about 2.6 times larger. Request `12_000_000` for a real 31.25 MHz.
- A soft reset does not undo it. Unplugging the board does.
- `FAST_SPI = False` at the top of `pocket.py` switches it off.
- A different board or a different MicroPython build may behave differently. If the screen is dark or garbled, turn it off first.

## Memory

| Item | Value |
|---|---|
| RAM free at boot (nothing imported) | about 222 KB |
| After the 115 KB framebuffer | about 104 KB. A second full framebuffer does **not** fit |
| Free while playing the whole game | roughly **50 to 55 KB** |
| Flash free for files | about 15 MB |
| Each imported module | 2 to 14 KB of RAM. Games are imported when chosen and dropped on exit |
| Garbage collector pause | about 11 ms for a forced collection |

The project is built to stay inside that. Do not load full-screen images into RAM. They stream from flash into the framebuffer.

## Flash and files (LittleFS quirks)

| Operation | Cost |
|---|---|
| `os.stat` on a file | about 3.7 ms |
| `open()` on a file | about 3 ms |
| Read speed, `readinto` | 4.4 to 5.6 MB/s. A 115 KB full-screen image: 21 to 26 ms |
| One draw of a card from its own file | about 6 ms. From a packed sprite sheet: about 3 ms |
| Atomic save (write temp, rename) | 55 to 150 ms, so save once per round, not per frame |
| Flash write endurance | about 100,000 erase cycles per 4 KB block. One save per round is harmless |

Because opening a file is slow, art is packed one file per family (cards, chips, banners, icons) and read with `seek`.

**Module name trap:** on MicroPython 1.29 an empty folder named the same as a module hides the module. `lib/art.py` is not called `assets.py` because the `/assets` folder would shadow it. A test fails if any module shares a name with a board folder.

## Useful measurements for design

| Thing | Time |
|---|---|
| Full redraw of ten cards (code-drawn) | about 94 ms |
| Redraw of the player band after a hit | about 30 to 45 ms |
| Blackjack key press to result banner | about 85 to 100 ms |
| Two hands side by side after a split | adds about 16 ms |
| Poker hand evaluation, 5 cards / 7 cards | 1 ms / 22 ms |

## Things that bite during development

- **Only one program can hold the serial port.** Viper IDE (Chrome) holds it even when the tab is idle. Close it before using `mpremote`.
- **"Could not enter raw repl"** after a killed `mpremote` run: the board is fine. Send Ctrl-C, Ctrl-B, Ctrl-D over the serial port (`hwtest/unwedge.py`) or unplug it.
- **Sprites with transparency** use magenta (`#FF00FF`), which converts to the key `0x1FF8`. The converter nudges any real pixel that would land on that value so nothing disappears by accident.
- **Unplugging resets the clock fix**, the file system keeps everything.

## Re-running the measurements

Every number above came from a script in [`hwtest/`](../hwtest/README.md). Run them with the board connected and Viper closed, from the repo root:

```bash
mpremote connect <port> mount hwtest exec "import board_info"
```

Each script prints `RESULT key=value` lines. Some need a person at the board (a screen look, button presses): the table in `hwtest/README.md` says which.
