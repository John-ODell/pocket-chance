# Board and bench notes

_Maintained by the microcontroller expert. State what is on the desk and how you know._

| Item | Value | How verified |
|---|---|---|
| Board | Waveshare RP2040-Plus, 16 MB | John (box); not yet confirmed from the board |
| Display HAT | Waveshare Pico LCD 1.3" | John |
| Firmware | not yet measured | board not reachable yet |
| Serial port | none seen | `mpremote connect list` 2026-10-03 showed only Bluetooth/debug-console ports: board not plugged in or not enumerating |
| Filesystem layout on board | not yet measured | script ready: hwtest/board_info.py |
| Last backup | none yet (`backups/`); nothing on the board has been touched | |
| Host tool | mpremote 1.29.0 at ~/.local/bin/mpremote | `mpremote version`, 2026-10-03 |

## Pin map (from `main_monolith.py`, unverified on hardware)
| Function | GPIO |
|---|---|
| LCD DC / CS / SCK / MOSI / RST / BL | 8 / 9 / 10 / 11 / 12 / 13 |
| Buttons A / B / X / Y | 15 / 17 / 19 / 21 |
| Joystick up / down / left / right / press | 2 / 18 / 16 / 20 / 3 |

## Log
_Date, what you did on the board, what state you left it in._

- 2026-10-03: installed check only (mpremote already present). Board not visible over USB, so no connection was made, nothing read, written or reset. Board state unchanged. Viper was never contended by me.
