# First power-up of a new board (spin 1)

Written for John. Based on the auditor's bring-up plan (team channel, 2026-10-04 19:13), the expert's readings (HR-P05) and `pcb/BATTERY.md`. This plan is for an **assembled board from a released, reviewed revision**. The current layout drafts are unrouted and must never be powered.

Every step is supervised, on a clear non-flammable surface, with the expert on the line. The bench current limits below are cautious test settings, not chip ratings.

## What you need
- A **current-limited bench power supply** (your decision whether to buy one: AUDIT-3, item for John). It must let you set both the voltage and a current limit.
- A multimeter.
- A USB-C lead for the bench supply's 5 V (a USB power breakout), or the supply's leads on the USB test fixture the expert suggests.
- Later: the approved protected cell (`pcb/BATTERY.md`).

## Test points on the board
| Pad | Rail | Expected (once powered) |
|---|---|---|
| TP1 | VBUS (USB 5 V) | about 5.0 V |
| TP2 | VSYS (charger output) | about 4.4 V on USB with no cell |
| TP3 | +3V3 | 3.3 V |
| TP4 | 1V1 (chip core) | 1.1 V |
| TP5, TP6 | GND | 0 V reference |
| TP7 | BAT+ | the cell's voltage; may pulse with no cell while the charger looks for one |
| TP8 | RUN (reset line) | 3.3 V when running |

**BAT- (socket pin 2) is not the same as GND.** The battery protection switches sit between them. Measure cell voltages between the socket's two pins, not to TP5/TP6.

## Before any power: inspection with everything unplugged
1. The board's revision and commit match the files that were ordered.
2. No solder bridges on the fine-pitch chips (the RP2350, the charger, the regulator).
3. Pin 1 of every chip on its mark, the LEDs the right way round.
4. **The small core inductor L1: its dot sits on pad 2, the 1V1 end** (RP2350 datasheet Figures 26 and 28; the assembly drawing shows it).
5. The fuse F1 is the 1.5 A Bourns part.
6. With a meter on continuity: socket pin 1 connects to the fuse, socket pin 2 to BAT-. The **+ RED** mark on the board is beside pin 1.
7. Each rail (TP1, TP2, TP3, TP4, TP7) to GND: no dead short. Capacitors make the reading drift upward at first; that is normal.
8. Screen, microSD card, speaker and battery all **disconnected**. Jumper JP2 left open.

The speaker socket J5 is a bridge output: neither wire is ground. Never clip a scope or meter ground to either speaker wire.

Never put a meter in current mode across two rails. To measure current, the meter goes in series, with everything switched off while you rewire.

## The steps
Do them in order. If anything in the "stop if" column happens, follow "If something goes wrong" at the bottom before going on.

| Step | Set up | Read | Stop if |
|---|---|---|---|
| 1. USB only | No cell. Power switch SW3 **off**. Bench supply 5.0 V, **100 mA limit**, into the USB socket. | TP1 about 5 V. TP2 about 4.4 V. TP3 off (it may take a moment to fall). TP7 may pulse. | The supply sits at its current limit, anything gets warm, or 3.3 V appears with SW3 off. |
| 2. USB, switched on | Still no cell. SW3 **on**. | TP3 3.3 V and TP4 1.1 V, both steady (within about 5 %). Note the input current and feel for heat. | A rail is low, wobbles or collapses. If the 100 mA limit causes a brown-out, find out why before raising it, and never above 500 mA. |
| 3. Boot | Rails steady. Hold BOOT, press RESET. | The RP2350 boot drive appears on the Mac. Load an **RP2350** MicroPython build (not the RP2040 one). Check the chip identity, the 16 MB flash and the PSRAM start-up before using them. For the PSRAM, read its ID after ten or so cold power-ups (unplug, wait, replug): its datasheet wants its chip-select held high during start-up, and the board's 10 k pull-up is the Raspberry Pi reference value but marginal on paper against the chip's reset pull-down. Read the rails again after boot. | It does not boot: do not raise any voltage; ask the expert. |
| 4. Bench supply in place of the battery (not a real cell yet) | **Unplug USB completely.** Bench supply **off**, set to 3.7 V with a **0.2 A limit**. Check its output polarity with the meter. Connect **+ to socket pin 1** and **- to socket pin 2** (not to TP6). SW3 off. Turn the supply on, then SW3 on. | Cell voltage across the socket pins; TP7 to BAT-; TP2, TP3, TP4; the supply's current. | Current limit reached, a rail collapses, anything heats. Do not raise the 0.2 A limit to force it to start. |
| 5. Add the parts one at a time | Still on the bench supply. Add the screen, then the card, the motion sensor and clock, the speaker, the radio, one at a time, each with its test program. | 3.3 V and 1.1 V stay steady; current goes up a little with each part; F1, the charger and the regulator stay cool. Raise the current limit only to a figure the expert has worked out. | As above. Note: the existing load script tests only the CPU and screen. |
| 6. The real protected cell | **Everything off and unplugged.** Inspect the pack: no swelling or damage. Do the plug check in `pcb/BATTERY.md` (red to +, then **meter the plug contacts**). Plug in the cell alone, SW3 off; then SW3 on. | The board runs; rails as before; current and temperatures. | Anything above. A real cell's fault current is **not** limited by the earlier 0.1 A or 0.2 A settings: unplug it at once if anything is wrong. |
| 7. Cell and USB together | Only after step 6 works. Add USB, light load first. **Never plug USB in while the bench supply is on the battery socket** (an ordinary bench supply cannot absorb the charge current). | The charge LED is usually on for the first charge. Read TP7 to GND, the DW01A supply (U7 pin 5) to BAT-, and the cell across the socket. USB input stays under 500 mA. | Heat, a rail fault, the LED flashing about twice a second. |
| 8. A full charge, then the load test | Supervised, at room temperature, on a non-flammable surface. Never leave the first charges unattended. | Log the time, current, voltage and LED. The timer allows 6.7 to 11.4 h; check the charge actually ends (LED off) rather than assuming it. Run the full-load tests separately. | The LED flashes about twice a second (timer fault): unplug and investigate; do not keep re-plugging USB. |

## If something goes wrong
1. Turn the bench supply off. **Unplug USB and the battery.** The power switch alone does not disconnect the battery or the charger.
2. Stop for: wrong polarity, a supply stuck at its current limit, a rail fault, anything heating fast, a smell or smoke, a swollen or damaged pack, a hot wire or contact, or a timer fault.
3. Let it cool. Write down what was connected and the voltages, current and temperatures you saw.
4. Inspect the board unpowered and ask the expert and the PCB maker before trying again.
5. A tripped fuse is not fully open, and its reset time is not guaranteed.
6. Never try to wake a 0 V pack by bypassing its protection, and never create a short or a reversed connection on purpose.

Sources: BQ2407x datasheet pp.10, 12-13, 27-29, 40; Pingjing DW01A pp.2-5; FS8205A pp.3-4; Bourns MF-MSMF pp.2, 10; RP2350 datasheet pp.401-414; the board's test-point nets. The procedure and the bench limits are general practice, not a safety approval of the board or the pack.
