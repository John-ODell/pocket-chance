# hwtest: board measurement scripts

Run from the Mac, from the repo root, with Viper IDE disconnected. Nothing is stored on the board.
The scripts import `lcdbench.py`, so mount this folder (read-only use) when running:

    mpremote connect <port> mount hwtest exec "import board_info"
    mpremote connect <port> mount hwtest exec "import spi_clock"
    mpremote connect <port> mount hwtest exec "import frame_full"
    mpremote connect <port> mount hwtest exec "import frame_partial"
    mpremote connect <port> mount hwtest exec "import ram_free"

Finish with `mpremote connect <port> soft-reset`. Each script prints `RESULT key=value` lines to paste into hw/BUDGET.md.

| Script | Measures |
|---|---|
| board_info.py | firmware, clock, filesystem size, flash size |
| spi_clock.py | SPI baud actually granted vs requested, and real bytes/s on the wire |
| frame_full.py | full-frame push time, fps; Python fill time vs wire time |
| frame_partial.py | partial redraw (rect window, full-width band) fps |
| ram_free.py | free RAM before/after the framebuffer, largest free block, second-buffer test |

They draw to the panel (colour bars, a moving box) and leave it black. They touch only the LCD pins from the pin map.
