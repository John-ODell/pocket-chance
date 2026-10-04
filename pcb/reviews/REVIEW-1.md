# Review 1: schematic draft 0.2 against the official RP2350 design guide and the rulings

Reviewer: PCB maker, 2026-10-04. Companion to the expert's HR-P04 (pins vs the software: PASS). Source of truth: `pcb/refs/hardware-design-with-rp2350.pdf` (section numbers below), `rp2350-datasheet.pdf`, `rm2-datasheet.pdf`, the Pico 2 W datasheet, and the rulings DR-033 and PCB-001. The schematic is `pcb/kicad/pocket-chance-board.kicad_sch`, generated from `pcb/tools/gen_sch.py`.

## Checked and matching the guide

| Guide section | What it requires | In the schematic | Status |
|---|---|---|---|
| 2.1 on-chip regulator | L1 3.3 µH AOTA-B201610S3R3-101-T; C6, C7, C9 4.7 µF; R3 33 Ω on VREG_AVDD; VREG_PGND to GND | L1, C13, C14, C15, R2 as listed; PGND pin 47 to GND | match (footprint for L1 to be checked against the Abracon drawing, phase 5) |
| 2.2.1 decoupling | 100 nF per power pin; pins 53/54 may share one | C1 to C10: six IOVDD, one shared 53/54, three DVDD | match |
| 3.1 primary flash | W25Q128JVS on QSPI; QSPI_SS 1 kΩ to the BOOT button (R6); optional 10 kΩ pull-up | U2, R5 1 kΩ, SW1, R4 10 kΩ | match |
| 3.2 PSRAM | second device on the QSPI bus, CS on GPIO0 (XIP_CS1n), 0 Ω link, 10 kΩ pull-up "definitely needed" | U3 APS6404L, GPIO0 net PSRAM_CS, R6 10 kΩ | match (the 0 Ω link is omitted: GPIO0 is wired straight; PARTS notes it) |
| 4.1 crystal | ABM8-272-T3, 15 pF each side, 1 kΩ series on XOUT | Y1, C16, C17, R3 | match |
| 5.1 USB | 27 Ω series on D+ and D-, close to the chip; no pull-ups needed; 90 Ω differential pair over solid ground (layout) | R10, R11 27 Ω | match; the 0.8 mm/0.15 mm pair geometry is for a 1 mm board; ours is 1.6 mm, see risks |
| 5.3 debug | SWCLK and SWDIO on a header | J1 ARM 10-pin, 1.27 mm | match |
| 5.4 buttons | BOOT to QSPI_SS through R6; RESET pulls RUN low; RUN pulled up | SW1, SW2, R7 10 kΩ | match |
| Pico 2 W: ADC supply | ADC_AVDD from 3.3 V through an RC filter (201 Ω, 2.2 µF) | R1 200 Ω, C12 2.2 µF | match |
| Pico 2 W / RM2 Table 2 | REG_ON GP23 to pins 12 and 13; DATA GP24 to pin 5, pin 6 via 470 Ω, pin 10 via 10 kΩ; CS GP25 pin 9; CLK GP29 pin 3; VDDIO and Vin 3.3 V; LED on WL_GPIO0; VBUS sense on WL_GPIO2 | U11, R33, R34, R35, D2, R36, R37 | match (HR-033 confirmed the GPIO numbers) |
| PCB-001 / HR-P03 | BQ24074 power path, EN1 high EN2 low, TS 10 kΩ, TPS63001 with 10 µF at VIN, EN switch with pull-down, DW01A + FS8205A on the negative lead, 0 Ω ammeter link, test points | U5, R13, R12, U6, C23, SW3, R19, U7, Q1, R22, TP1 to TP8 | match |
| PCB-001 revised | one JST-PH socket, reverse-polarity P-FET with the gate on the connector's negative | J3, Q2 AO3401A, gate on BAT- | match (HR-P03 addendum: correct) |

## Open items (VERIFY in the schematic comments), closed only by reading the datasheet or measuring

1. BQ24074: the EN1/EN2 input-limit table (a swap silently gives 100 mA), K_ISET for R14, the ITERM and TMR resistor meanings (R16, R17), the ILIM resistor (R15), the TS pin's fixed-resistor acceptance, the thermal pad. **Needs the TI datasheet (download pending John's approval).**
2. TPS63001: inductor value (2.2 µH assumed), VINA decoupling, PS/SYNC to GND for power-save, layout per datasheet. **TI datasheet.**
3. FS8205A pin order (drawn as S1 G1 S2 G2 D2 D2 D1 D1) and continuous current rating. **Datasheet.**
4. APS6404L package: SN = 150 mil SOIC-8 assumed. **AP Memory datasheet.**
5. L1 footprint vs the Abracon 0806 drawing; PAM8302AAS package (SOP-8 assumed); Keystone 3001 fits a CR1220 (12.5 mm). **Datasheets.**
6. ~~LSM6DSOX pin map~~ **Closed 2026-10-04** from the ST datasheet (owner-fetched): pin map identical to the symbol used; SDx/SCx now tied to GND as the pin table asks; address 0x6A. Land pattern compared at phase 5.
7. The LCD module's BL pin: the module has its own backlight transistor on most Waveshare modules; if BL drove the LED string directly, GP13 would need a transistor. **Check on the module page or the real module.**
8. USB differential pair on a 1.6 mm board: the guide's 0.8/0.15 mm geometry is for 1 mm. Full-speed USB is forgiving; at layout we use the PCBWay stack-up calculator or accept the guide's "likely to work" note. **Layout decision, phase 6.**

## Risks I cannot verify from the desk
- The 62.5 MHz SPI link to the screen on a new layout (keep it short, ground beside it; fallback 24 MHz exists).
- The RM2 antenna keep-out and placement at the board edge (RM2 datasheet section 2.4, read at layout).
- The regulator inductor's orientation dot (guide 2.1): a layout and assembly note, not a schematic item.
- Nothing has been measured: current draw, cell behaviour, PSRAM placement of the framebuffer (HR-033's bring-up test).

## Verdict
The schematic matches the official reference circuits and the rulings. It is **not** ready to freeze: the eight open items above depend on datasheets not yet read. Freeze after the datasheet pass and the expert's look at the power resistor values.
