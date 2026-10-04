# Early answers from the microcontroller expert (2026-10-04)

Measured or reasoned on the real board by the expert. Each line says what is verified and what is not. The PCB maker should treat these as inputs to `pcb/CONSTRAINTS.md`.

| # | Question | Answer | Status |
|---|---|---|---|
| 1 | Does the screen-speed fix depend on the Waveshare firmware build? | The register fix is plain RP2040 (`CLOCKS.CLK_PERI_CTRL`, `AUXSRC`) and is independent of the build. What depends on the build is the **need** for it: the Waveshare v1.29.0 build sources `clk_peri` from the 48 MHz USB PLL, and the stock Pico v1.22.2 build used `clk_sys`. A custom board should expect either and the firmware should set the source explicitly | Measured on both builds |
| 2 | GPIO29 / ADC3 | **Unconnected on the RP2040-Plus.** It floats and reads the same ~0.6 V leakage as the other free ADC pins. The earlier 1.17 to 1.42 V readings were a floating input, not a VSYS divider. The Plus has no VSYS divider on GPIO29 like a Pico | Measured read-only (`hwtest/pins_reserved.py`) |
| 3 | Is the flash 8 MB or 16 MB? | **16 MB, by aliasing evidence.** NOR flash ignores address bits above its capacity, so an 8 MB chip read at offset 8 MB would show the firmware image again. Reads at 8 MB and 15 MB came back erased (0xFF), not a mirror of the start, so the chip is larger than 8 MB. High confidence for W25Q-class parts. The formal JEDEC ID was not read (it needs a careful RAM-only routine with the flash off; nothing it sends can erase). Read the real marking from the chip or the schematic if the exact part matters | Evidence in hand; JEDEC not read |
| 4 | 3.3 V rail under load | The board cannot measure its own reference. Needs the owner with a multimeter at the 3V3 pin with the backlight at full PWM. The expert can set up and script the load | **Open**, needs the owner |
| 5 | USB stability | The USB serial console was stable across hundreds of connects over a day. The only wedges came from killed host programs (raw-REPL state), fixed by `hwtest/unwedge.py` | Measured |

## PM note on question 3
Do not use a write-and-readback test on high flash addresses. The filesystem spans most of the chip, so if the chip were smaller than the firmware believes, writes would alias onto earlier data and corrupt it. Prefer a read-only identification: the flash chip's JEDEC ID (command 0x9F, capacity code in the third byte) or the part marking read from the chip with a loupe.

## Pin survey of the RP2040-Plus (read-only, `hwtest/pins_reserved.py`)

| Pin | Finding |
|---|---|
| GP24 | Held **high** on the board: VBUS sense, as on a Pico |
| GP23, GP25 | Float. No evidence of an LED on GP25. An output test would need a ruling |
| GP29 | Unconnected (see question 2) |
| GP0, 1, 4 to 7, 14, 22, 26 to 28 | All free |

A load script for the 3.3 V measurement is ready (`hwtest/load_hold.py`: backlight at 100%, full-frame pushes, 60 s). It needs the owner with a multimeter at the 3V3 pin.
