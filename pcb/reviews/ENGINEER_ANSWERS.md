# Early answers from the microcontroller expert (2026-10-04)

Measured or reasoned on the real board by the expert. Each line says what is verified and what is not. The PCB maker should treat these as inputs to `pcb/CONSTRAINTS.md`.

| # | Question | Answer | Status |
|---|---|---|---|
| 1 | Does the screen-speed fix depend on the Waveshare firmware build? | The register fix is plain RP2040 (`CLOCKS.CLK_PERI_CTRL`, `AUXSRC`) and is independent of the build. What depends on the build is the **need** for it: the Waveshare v1.29.0 build sources `clk_peri` from the 48 MHz USB PLL, and the stock Pico v1.22.2 build used `clk_sys`. A custom board should expect either and the firmware should set the source explicitly | Measured on both builds |
| 2 | GPIO29 / ADC3 | Reads the equivalent of 1.17 to 1.42 V, which is not a believable VSYS/3. The Pico's VSYS divider is evidently not wired the same way on this board. No schematic-level confirmation yet | Measured; cause unverified |
| 3 | Is the flash 8 MB or 16 MB? | The read-only probe cannot tell them apart. The firmware's 16 MB filesystem comes from the board definition, not from the chip. Needs the chip's JEDEC ID (read-only) or the part marking | **Open** |
| 4 | 3.3 V rail under load | The board cannot measure its own reference. Needs the owner with a multimeter at the 3V3 pin with the backlight at full PWM. The expert can set up and script the load | **Open**, needs the owner |
| 5 | USB stability | The USB serial console was stable across hundreds of connects over a day. The only wedges came from killed host programs (raw-REPL state), fixed by `hwtest/unwedge.py` | Measured |

## PM note on question 3
Do not use a write-and-readback test on high flash addresses. The filesystem spans most of the chip, so if the chip were smaller than the firmware believes, writes would alias onto earlier data and corrupt it. Prefer a read-only identification: the flash chip's JEDEC ID (command 0x9F, capacity code in the third byte) or the part marking read from the chip with a loupe.
