# Setup guide: from a bare board to a playing casino

A follow-along guide. Do the steps in order and check each "You should see" line before moving on. If something does not match, jump to [Troubleshooting](#troubleshooting).

Every number in here was measured on a real board, see [`docs/HARDWARE.md`](docs/HARDWARE.md).

## Items needed
- Waveshare **RP2040-Plus**, the **16 MB** version (the 4 MB version works too, but the firmware file is different)
- Waveshare **Pico LCD 1.3" HAT** (240 x 240 screen, joystick, four buttons) plugged onto the board
- A USB-C **data** cable (a charge-only cable shows nothing on your computer)
- A computer with Python 3.9 or newer. The commands below are for macOS. Linux is nearly the same. On Windows use `py` instead of `python3` and see the note at the end of Step 2
- Chrome, only if you want to use Viper IDE (the website editor). Optional if you use `mpremote`

There is nothing to wire. The screen and buttons are on the HAT. The pin map is in [`docs/HARDWARE.md`](docs/HARDWARE.md) in case you want to reuse it.

## Step 1: Put MicroPython on the board

This wipes everything on the board. If it has files you want, copy them off first.

1. Go to <https://micropython.org/download/WAVESHARE_RP2040_PLUS/>.
2. Download the **16 MB** build. The file name looks like `WAVESHARE_RP2040_PLUS-FLASH_16M-<date>-v1.29.0.uf2`.
   - Do **not** use the plain Raspberry Pi Pico build. It runs, but it only uses 2 MB of the 16 MB.
3. Unplug the board.
4. Hold the **BOOTSEL** button on the board, plug in the USB-C cable, then let go.
5. A drive named **RPI-RP2** appears on your computer.
6. Drag the `.uf2` file onto that drive.
7. Wait about 10 seconds. The drive disappears by itself and the board restarts.

You should see: no drive any more, and the screen stays dark. That is normal, nothing runs yet.

Check it worked (after Step 2 you can run this):

```bash
mpremote exec "import os; print(os.uname().machine); print(os.statvfs('/')[0]*os.statvfs('/')[2])"
```

You should see `Waveshare RP2040-Plus 16MB with RP2040` and a number near **15,700,000**. If the second number is near 1,400,000 you installed the Pico build: repeat Step 1 with the right file.

## Step 2: Install the tools on your computer

```bash
pip install mpremote pillow
```

- **mpremote** copies files to the board and runs scripts. (`pipx install mpremote` also works.)
- **Pillow** is only needed to convert your art into files the board can read.

Check it:

```bash
mpremote connect list
```

You should see a line with `MicroPython Board in FS mode`. Write down its port (on macOS it looks like `/dev/cu.usbmodem112301`). If nothing is listed, see Troubleshooting.

**Windows:** the port is `COM3` or similar. Use `mpremote connect COM3 ...`. Everything else is the same.

### Prefer a website to a terminal?
**Viper IDE** works in Chrome: go to <https://viper-ide.org>, click connect, pick the board, and use its file panel to copy files. The terminal route below is faster for the 14 files, but Viper is fine. Never have Viper and `mpremote` connected at the same time. Only one program can use the board's USB port.

## Step 3: Get the project and run the tests

```bash
git clone https://github.com/John-ODell/pocket-chance.git
cd pocket-chance
python3 -m unittest discover -s tests
```

You should see `OK` at the end. The tests run on your computer with stand-in versions of the board's modules, so no board is needed for them.

## Step 4: Copy the game onto the board

Run these from the `pocket-chance` folder (replace the port with yours, or leave it out if only one board is plugged in):

```bash
mpremote fs mkdir :lib
mpremote fs mkdir :games
mpremote fs mkdir :assets

mpremote fs cp lib/pixfmt.py lib/lcd.py lib/font.py lib/buttons.py lib/sheets.py lib/art.py lib/save.py lib/bankroll.py lib/cards.py :lib/
mpremote fs cp games/blackjack_rules.py games/blackjack_table.py games/blackjack.py :games/
mpremote fs cp pocket.py :pocket.py
```

Notes:
- If a `mkdir` says the folder exists, that is fine.
- Do **not** copy `lib/poker.py` yet. It is for the next game and not needed to play blackjack.
- The exact, always-current file list is [`UPLOAD.md`](UPLOAD.md). If the two ever disagree, trust `UPLOAD.md`.
- Do not rename `lib/art.py`. A folder called `/assets` hides a module of the same name on MicroPython, so the loader has an odd name on purpose.

## Step 5: Run it

```bash
mpremote run pocket.py
```

This runs the game from your computer without saving anything extra. You should see the menu (title "Pocket Chance", your chips, rows for the games) and the terminal prints a `RESULT boot ...` line.

Controls (landscape, USB-C and joystick on the left, buttons on the right):

| Where | Control | Does |
|---|---|---|
| Menu | Joystick up / down | Move the box |
| Menu | **A** | Pick a game. "Off" stops the program |
| Blackjack, betting | Joystick up / down, **A**, **B** | Change the bet (5 to 500), deal, back to menu |
| Blackjack, playing | **A** hit, **B** stand, **X** double, **Y** split a pair | |

To stop it, press Ctrl-C in the terminal.

## Step 6 (optional): Make it start by itself

```bash
mpremote fs cp pocket.py :main.py
```

Unplug the board and plug it back in. The menu should appear on its own.

To undo that and go back to running by hand:

```bash
mpremote fs rm :main.py
```

## Step 7 (optional): Add your own art

The game runs with code-drawn shapes and needs no art. To use your own images, read [`assets/ASSETS.md`](assets/ASSETS.md). In short:

1. Draw each picture as a 24-bit BMP at the exact size listed there. Transparency is pure magenta (255, 0, 255).
2. Put them in `assets/src/<family>/` (cards, chips, ui).
3. Run the converter. It checks names and sizes and tells you what is missing:

   ```bash
   python3 tools/convert_assets.py
   ```

4. Copy the files it writes in `assets/out/` to `/assets/` on the board with `mpremote fs cp`.

A full-screen menu background goes in `assets/src/ui/menu_background.bmp` (240 x 240). Without it the menu uses a plain dark colour. This repo does not ship one, so bring your own.

## Get back to a clean board

To wipe every project file and start over: do Step 1 again (the firmware flash erases the filesystem). To just remove the project files:

```bash
mpremote fs rm -r :lib
mpremote fs rm -r :games
mpremote fs rm -r :assets
mpremote fs rm :pocket.py
mpremote fs rm :save.json
```

## Troubleshooting

| What you see | What to do |
|---|---|
| `mpremote connect list` shows no board | Use a data cable. Try another USB port. Unplug and replug **without** holding BOOTSEL |
| "could not open port" or "busy" | Another program has the board. Close Viper IDE and its tab, or quit Chrome. On macOS, `lsof /dev/cu.usbmodem*` names the program holding it |
| "could not enter raw repl" | The board is fine. A killed `mpremote` run left it in a half state. Run `python3 hwtest/unwedge.py` (needs `pip install pyserial`) or unplug and replug |
| Dark screen after `run pocket.py` | Open `pocket.py`, set `FAST_SPI = False` near the top, copy it again and rerun. Then open an issue with what you saw. This is the one known-unknown on other boards |
| `no module named 'something'` | A file is missing or in the wrong folder. Compare with the file list in Step 4 |
| Out of memory or it crashes after a few hands | The board has about 50 KB of RAM left while playing. Do not add more modules to `/lib` than the list above |
| The colours look wrong (red and blue swapped) | Your screen uses the other byte order. See `docs/HARDWARE.md`, "Colour". The Waveshare 1.3" HAT is big-endian, as this project assumes |
| Everything is dark after Step 1 | Normal. The board starts the firmware and nothing else. Continue to Step 4 |
| The board will not leave BOOTSEL mode | Drag the `.uf2` again. If the drive never appears, hold BOOTSEL a bit longer while plugging in |

Still stuck? Open an issue on the repo. Say which step, what you saw, and paste the full terminal output. Do not post anything private.
