# HR-P02: Review of DR-033 appendix I and requirements §11a/11c, RTC, IMU, GPS header, low power

- **Verdict: fits, with the cautions below.** The pin changes are consistent with the GPIO function table; the coin-cell choice is right; the low-power expectation is honest.
- Reviewer: microcontroller expert, 2026-10-04. Desk review; the official datasheets are now in `pcb/refs/` (RP2040, RP2350, Pico W, Pico 2 W, RM2, W25Q128JV), so every function below can be confirmed there; I worked from the RP2040 table and my knowledge of the parts.

## Pin changes since HR-P01
| Change | Check |
|---|---|
| Card-detect dropped; **GP14 = IMU interrupt** (LSM6DSOX INT1) | Any GPIO takes an interrupt; GP14 is fine. Without card-detect, mount the card lazily and handle `OSError` on access; a pulled card then costs an error, not a crash |
| **GP1 = UART0 RX** for a listen-only GPS | Correct and forced: UART0 RX is on GP1, GP13 (LCD BL), GP17 (button B), GP29 (radio). GP1 is the only one left. Listen-only is right for a first board: no TX, no level questions |
| **GP28 stays the battery divider**, noted as the only remaining UART0 TX | Correct: UART0 TX is on GP0 (PSRAM CS), GP12 (LCD RST), GP16 (joystick), GP28. So the one trade left is "battery ADC on GP28" versus "a UART0 TX on GP28 with the fuel gauge over I2C for battery state". My preference for spin 1: keep the divider on GP28 (it cannot fail) and accept no debug TX; a debug print still has the USB REPL |
| **RTC (DS3231 family) and IMU share I2C1 on GP26/27** with a STEMMA QT connector | Correct; I2C is a bus. Pull-ups: one set on the board (4.7 kΩ at 3.3 V); STEMMA QT modules often carry their own, two sets in parallel at 3.3 V are still fine, three or more start to be stiff for a 400 kHz bus. Addresses: DS3231 0x68, LSM6DSOX 0x6A or 0x6B (SA0 pin), no clash |
| All 30 GPIO used | Fine, but it means **no spare for a wake source from the RTC** (DS3231 INT/SQW is the natural one for timed wake). If timed wake matters, the RTC's INT could share GP14 with the IMU through a wired-OR (both open-drain, active low, one pull-up) and the firmware asks each chip who fired. Cheap to leave as an option: a solder jumper from RTC INT to the GP14 net |

## Coin cell
**CR1220 primary cell on the RTC backup input, never charged: agreed, and it is the safer of the two.** The DS3231's VBAT input is a plain backup input with no charger, so a primary cell is correct by construction. The PCF8523 is cheaper and smaller but carries a trickle charger whose register default must be set to "off" and stays off only while the firmware says so; a mistake there charges a primary cell, which is the one failure that matters. So: **DS3231 (DS3231MZ, SOIC-8, built-in crystal, TCXO accuracy) with the CR1220**, and the cell's holder on the back where the cell can be changed. Expect a CR1220 to run the DS3231 backup for several years.

## IMU
LSM6DSOX: an official micropython-lib driver exists (`lsm6dsox`), the pedometer and significant-motion engines are in hardware, INT1 wakes on motion. Fine. Mount it near the board's centre of mass, away from the speaker and the buck-boost inductor; step counting is forgiving, but the magnetometer it does not have is not missed. Power: ~0.5 mA active, microamps in its low-power modes.

## Low power
Agree with "milliamps, not microamps, on a first board": the buck-boost's quiescent current, the PSRAM's standby, the RM2's leakage with REG_ON low, the panel's sleep current and the RP2350 in `machine.lightsleep` all add up to a few mA at best in MicroPython today; `deepsleep` on rp2 is not a true shutdown. The hooks listed (backlight off, REG_ON low, switched card supply, IMU or button wake) are the right ones; measure on the first board and only then promise a standby time. The 3.3 V load measurement (`hwtest/load_hold.py`) remains the number the regulator and the battery life both wait on.

## Fab
PCBWay, assembly minimum 5, 0.25 mm pitch fine: the RP2350A's 0.4 mm pitch and the RM2's 1.5 mm castellations are comfortably inside that. Five boards is right: one for bring-up, one clean, three spares for the mistakes a first board teaches.

## What I could not verify
Any datasheet in this appendix by reading it (DS3231, PCF8523, LSM6DSOX, CR1220 capacity); the actual standby current, which needs the board.
