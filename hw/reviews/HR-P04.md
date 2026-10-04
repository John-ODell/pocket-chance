# HR-P04: Phase 4 check, schematic pins against the software's verified pin map

- **Verdict: pass.** Every GPIO the software uses today lands on the same GPIO on the RP2350A in `pcb/tools/gen_sch.py`; the new functions sit on the pins REQUIREMENTS §11a assigns. Two items stay "verify" as the PCB maker marked them.
- Reviewer: microcontroller expert, 2026-10-04. Method: the U1 pin table in `pcb/tools/gen_sch.py` (pin number → net) checked against the pin-number → GPIO map of KiCad's own `MCU_RaspberryPi:RP2350A` symbol (read from the installed library), and against the software pin map verified on the RP2040-Plus (`hw/BOARD.md`, 2026-10-04).

## U1: the thirty GPIO, pin by pin
| QFN-60 pin | KiCad symbol says | `gen_sch.py` net | Software today | Check |
|---|---|---|---|---|
| 2 | GPIO0 | PSRAM_CS | unused | ok (design guide: XIP CS1) |
| 3 | GPIO1 | EXP_GP1 (UART0 RX) | unused | ok |
| 4 | GPIO2 | JOY_UP | joystick up GP2 | **ok, verified pin** |
| 5 | GPIO3 | JOY_PRESS | joystick press GP3 | **ok** |
| 7 | GPIO4 | SD_MISO (SPI0 RX) | unused | ok |
| 8 | GPIO5 | SD_CS | unused | ok |
| 9 | GPIO6 | SD_SCK (SPI0 SCK) | unused | ok |
| 10 | GPIO7 | SD_MOSI (SPI0 TX) | unused | ok |
| 12 | GPIO8 | LCD_DC | LCD DC GP8 | **ok** |
| 13 | GPIO9 | LCD_CS | LCD CS GP9 | **ok** |
| 14 | GPIO10 | LCD_SCK (SPI1 SCK) | LCD SCK GP10 | **ok** |
| 15 | GPIO11 | LCD_MOSI (SPI1 TX) | LCD MOSI GP11 | **ok** |
| 16 | GPIO12 | LCD_RST | LCD RST GP12 | **ok** |
| 17 | GPIO13 | LCD_BL (PWM) | backlight GP13 | **ok** |
| 18 | GPIO14 | IMU_INT | unused | ok |
| 19 | GPIO15 | BTN_A | button A GP15 | **ok** |
| 27 | GPIO16 | JOY_LEFT | joystick left GP16 | **ok** |
| 28 | GPIO17 | BTN_B | button B GP17 | **ok** |
| 29 | GPIO18 | JOY_DOWN | joystick down GP18 | **ok** |
| 31 | GPIO19 | BTN_X | button X GP19 | **ok** |
| 32 | GPIO20 | JOY_RIGHT | joystick right GP20 | **ok** |
| 33 | GPIO21 | BTN_Y | button Y GP21 | **ok** |
| 34 | GPIO22 | AUDIO_PWM | unused | ok |
| 35 | GPIO23 | WL_REG_ON | unused (floats on the Plus) | ok (Pico 2 W pin) |
| 36 | GPIO24 | WL_DATA | unused (VBUS sense on the Plus) | ok (Pico 2 W pin) |
| 37 | GPIO25 | WL_CS | unused | ok (Pico 2 W pin) |
| 40 | GPIO26/ADC0 | SDA (I2C1) | unused | ok |
| 41 | GPIO27/ADC1 | SCL (I2C1) | unused | ok |
| 42 | GPIO28/ADC2 | VBAT_SENSE | unused | ok |
| 43 | GPIO29/ADC3 | WL_CLK | unconnected on the Plus | ok (Pico 2 W pin) |

Service pins also match the symbol: 21 XIN, 22 XOUT, 24 SWCLK, 25 SWDIO, 26 RUN, 51 USB_DM, 52 USB_DP, 55–60 QSPI_SD3/SCLK/SD0/SD2/SD1/SS.

**Result:** the game's `lib/lcd.py` and `lib/buttons.py` run on this board with no pin change, as DR-033 appendix A claimed. The only software change remains the clock call (already `machine.freq` after DR-050) and the firmware board definition.

## Items that stay "verify"
1. **LCD socket J4 order (VCC, GND, DIN, CLK, CS, DC, RST, BL → +3V3, GND, LCD_MOSI, LCD_SCK, LCD_CS, LCD_DC, LCD_RST, LCD_BL):** consistent with the Waveshare LCD-module convention as I know it, and the signal mapping (DIN = MOSI, CLK = SCK) is right. Not verifiable from the repo: the local Waveshare folders are the HAT's code, not the module's pinout. **Verify on the physical module's silkscreen before the footprint is final**; a swapped VCC/GND is the one fatal case, so consider a 1x8 socket with the module's own pin 1 marked on both.
2. **BQ24074 resistor values** (ISET, ILIM, TS, the EN pin logic): placeholders until the datasheet is read, as marked; HR-P03's addendum lists what to confirm.
3. **SA0 tied to GND on the IMU** (ERC warning): fine electrically; it fixes the LSM6DSOX address at 0x6A, which the driver default expects. Just document it.

## Notes
- The three custom footprints (RM2, LSM6DSOX, Alps joystick) are the expected ERC warnings; draw them from the datasheets in `pcb/refs/`.
- The RTC-INT-to-GP14 solder jumper (JP2) is in, as suggested in HR-P02.
