# Parts shortlist, spin 1

Written 2026-10-04 (phase 2 of `pcb/STAGE2.md`). One line per part or group. Columns: what it is, the manufacturer part number (MPN), package, the KiCad symbol and footprint we will use (`library:name`; "custom" means we draw it from the datasheet), where its facts come from, and what is still to check. **Stock** is checked on PCBWay's quote page and the distributors (Digi-Key, Mouser) at phase 9; until then every line says "stock: to check".

Design rules behind the list: surface-mount only (the 18650 holder was dropped 2026-10-04, John's choice: flat board, JST LiPo); nothing smaller than 0402 (PCBWay's 0201 lines carry a 100-piece minimum); every optional block in its own group so spin 2 can drop it. **Owner's rule (2026-10-04): standard, common, stocked parts with standard footprints wherever possible; anything unusual carries its reason in its row.** "Custom" in the KiCad column means only that KiCad's bundled library lacks the drawing and we draw it from the datasheet; the part itself is still a standard catalogue part.

Rows with a stated reason for a non-generic choice: Y1 and L1 (the exact parts the Raspberry Pi design guide says to use, with its warning that others are at your own risk); U-RF (the RM2 is the standard pre-certified way to add this radio; a bare radio chip would be the unusual choice); SW-JOY (a 5-way navigation switch is a standard part, but KiCad has no footprint for it; the zero-custom alternative is five ordinary tactile buttons as a direction pad, which John said he would accept).

## Block 1: core (RP2350A, flash, PSRAM, crystal, regulator parts)

| Ref | Part | MPN | Package | KiCad symbol / footprint | Source | To check |
|---|---|---|---|---|---|---|
| U1 | RP2350A microcontroller | RP2350A (Raspberry Pi) | QFN-60, 7 x 7 mm, 0.4 mm pitch | `MCU_RaspberryPi:RP2350A` / `Package_DFN_QFN:QFN-60-1EP_7x7mm_P0.4mm_EP3.4x3.4mm` | `refs/rp2350-datasheet.pdf`; design guide | pad and paste design against the datasheet's land pattern; stock |
| U2 | 16 MB QSPI flash | W25Q128JVSIQ (Winbond) | SOIC-8, 208 mil (5.3 x 5.3 mm) | `Memory_Flash:W25Q128JVS` / `Package_SO:SOIC-8_5.3x5.3mm_P1.27mm` | `refs/W25Q128JV-datasheet.pdf`; design guide 3.1 and 3.3 (supported chip) | stock |
| U3 | 8 MB PSRAM | APS6404L-3SQR-SN (AP Memory) | SOP-8 | `Memory_RAM:APS6404L-3SQRx-SN` / `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` (**verify** the SN package is the 150 mil body) | Pimoroni Pico Plus 2 W uses it; design guide 3.2 | datasheet download (official AP Memory); package; stock |
| R9, R13 | PSRAM chip-select link and pull-up | 0 Ω, 10 kΩ | 0402 | `Device:R` / `Resistor_SMD:R_0402_1005Metric` | design guide 3.2: GPIO0 is XIP_CS1n; "the pull-up on the chip select pin is definitely needed" | |
| R-QSPI | flash chip-select 1 kΩ series to BOOT button, optional 10 kΩ pull-up | 1 kΩ, 10 kΩ | 0402 | same | design guide 3.1 (R6 1 kΩ to USB_BOOT) | |
| Y1 | 12 MHz crystal | ABM8-272-T3 (Abracon) | 3.2 x 2.5 mm | `Device:Crystal_GND24` / `Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm` | design guide 4.1: "we highly recommend using this crystal"; 10 pF load, 30 ppm, 50 Ω ESR max | stock |
| C3, C4 | crystal load capacitors | 15 pF, C0G | 0402 | `Device:C` / `Capacitor_SMD:C_0402_1005Metric` | design guide 4: 15 pF each gives 10.5 pF with trace parasitics | |
| R2 | crystal series resistor | 1 kΩ | 0402 | `Device:R` | design guide 4: prevents over-driving | |
| L1 | core regulator inductor | AOTA-B201610S3R3-101-T (Abracon, 3.3 µH, polarity dot) | 0806 (2016 metric) | `Device:L` / `Inductor_SMD:L_0806_2016Metric` (**verify** against the Abracon drawing) | design guide 2.1: the exact part, oriented per the dot | stock (the guide says newly available); footprint |
| C6, C7, C9 | regulator input, output, AVDD caps | 4.7 µF | 0402 | `Device:C` | design guide 2.1 | |
| R3 | VREG_AVDD filter | 33 Ω | 0402 | `Device:R` | design guide 2.1 (33 Ω + 4.7 µF) | |
| C-dec | decoupling, one per power pin, pins 53/54 share one | 100 nF | 0402 | `Device:C` | design guide 2.2.1 | count after the symbol is placed |
| C-bulk | 3.3 V bulk | 10 µF | 0603 | `Device:C` / `Capacitor_SMD:C_0603_1608Metric` | general practice | |
| SW-BOOT, SW-RESET | tactile buttons | PTS645SM43SMTR92 (C&K) | 6 x 6 mm SMD | `Switch:SW_Push` / `Button_Switch_SMD:SW_SPST_PTS645Sx43SMTR92` | design guide 5.4 | stock |
| D-LED, R-LED | user LED and 1 kΩ | 0603 LED | 0603 | `Device:LED` / `LED_SMD:LED_0603_1608Metric` | | GPIO: none free; LED driven from the RM2's wireless GPIO as on the Pico 2 W (HR-033) or omitted |
| TP1.. | test points | pad | 1.5 mm | `Connector:TestPoint` / `TestPoint:TestPoint_Pad_D1.5mm` | PLAN phase 7 | 3V3, VBAT, VSYS, GND x2, RUN, SWD |
| J-SWD | debug header | 2 x 5, 1.27 mm (ARM 10-pin) | SMD | `Connector:Conn_ARM_JTAG_SWD_10` / `Connector_PinHeader_1.27mm:PinHeader_2x05_P1.27mm_Vertical_SMD` | design guide 5.3 (any SWD header); ruling item 5 | |

## Block 2: USB

| Ref | Part | MPN | Package | KiCad symbol / footprint | Source | To check |
|---|---|---|---|---|---|---|
| J-USB | USB-C receptacle, USB 2.0, 16 pins | USB4085-GF-A (GCT) | SMD with through-board pegs | `Connector:USB_C_Receptacle_USB2.0_16P` / `Connector_USB:USB_C_Receptacle_GCT_USB4085` | KiCad library footprint is vendor-specific; GCT drawing to verify | stock; datasheet (official GCT) |
| R-CC1, R-CC2 | CC pull-downs | 5.1 kΩ | 0402 | `Device:R` | USB-C sink requirement (general; **the Pico 2 W schematic in `refs/pico-2-w-datasheet.pdf` to confirm**) | |
| R7, R8 | D+ and D- series | 27 Ω | 0402 | `Device:R` | design guide 5.1: "27 Ω series termination resistors, placed close to the chip" | |
| U-ESD | USB ESD array | USBLC6-2SC6 (ST) | SOT-23-6 | `Power_Protection:USBLC6-2SC6` / `Package_TO_SOT_SMD:SOT-23-6` | general practice | stock |
| F/D-VBUS | input protection | optional polyfuse or none (BQ24074 has 28 V OVP) | | | PCB-001 | decide at schematic |

## Block 3: power (PCB-001, pending)

| Ref | Part | MPN | Package | KiCad symbol / footprint | Source | To check |
|---|---|---|---|---|---|---|
| U-CHG | power-path charger | BQ24074RGTR (TI) | VQFN-16, 3 x 3 mm | `Battery_Management:BQ24074RGT` / `Package_DFN_QFN:VQFN-16-1EP_3x3mm_P0.5mm_EP1.68x1.68mm` (**verify** EP size vs RGT drawing) | ti.com product page 2026-10-04 | datasheet download; stock; ISET/ILIM/TMR resistor values |
| U-BB | 3.3 V buck-boost | TPS63001DRCR (TI) | VSON-10, 3 x 3 mm | `Regulator_Switching:TPS63001` / `Package_SON:VSON-10-1EP_3x3mm_P0.5mm_EP1.2x2mm` (**verify** EP vs DRC drawing) | ti.com product page 2026-10-04 | datasheet; inductor value (2.2 µH typical, **verify**); stock |
| L-BB | buck-boost inductor | 2.2 µH, 2 A class, 3 x 3 mm | | `Device:L` / `Inductor_SMD:L_1210_3225Metric` or vendor | TPS63001 datasheet | pick after datasheet |
| U-PROT | cell protection | DW01A (Fortune) | SOT-23-6 | `Battery_Management:DW01A` / `Package_TO_SOT_SMD:SOT-23-6` | HR-033, HR-P01 | datasheet (official); stock |
| Q-PROT | protection dual MOSFET | FS8205A | TSSOP-8 or SOT-23-6 per vendor | `Transistor_FET_Dual:` generic dual N-MOSFET / per package | HR-033 | datasheet; package; stock |
| J-BAT | pouch cell socket, pin 1 = +, polarity on the silkscreen | S2B-PH-SM4-TB (JST PH, 2 mm, SMD) | SMD | `Connector:Conn_01x02_Socket` / `Connector_JST:JST_PH_S2B-PH-SM4-TB_1x02-1MP_P2.00mm_Horizontal` | PCB-001 | stock |
| Q-RPP | reverse-polarity guard, P-MOSFET in the cell's positive lead | AO3401A (Alpha & Omega; -30 V, 4 A, about 50 mΩ; the most common hobby P-FET) | SOT-23 | `Transistor_FET:AO3401A` / `Package_TO_SOT_SMD:SOT-23` | PCB-001 revised (JST-only, John 2026-10-04) | datasheet (official Diodes); pin order; stock |
| SW-PWR | power switch on the regulator enable | PCM12SMTR (C&K) slide | SMD | `Switch:SW_SPDT` / `Button_Switch_SMD:SW_SPDT_PCM12` | HR-033 | stock |
| R-DIV | battery divider to GP28 | 100 kΩ + 100 kΩ, 100 nF | 0402 | `Device:R`, `Device:C` | HR-P01: 100 kΩ or more total | |
| R-TS | thermistor-pin resistor | 10 kΩ (or a 10 k NTC footprint) | 0402 | `Device:R` | PCB-001 | |
| U-GAUGE | fuel gauge (optional, footprint only) | MAX17048G+T10 | TDFN-8, 2 x 2 mm | custom symbol / `Package_DFN_QFN:` 2x2 DFN-8 to verify | HR-P01: optional | deferred unless time allows |

## Block 4: screen and input

| Ref | Part | MPN | Package | KiCad symbol / footprint | Source | To check |
|---|---|---|---|---|---|---|
| J-LCD | socket for the 1.54" 240 x 240 ST7789 module. **The module has a PH2.0 8-pin cable** (Waveshare wiki, 2026-10-04), so the board gets the matching JST-PH 2.0 mm 8-pin surface-mount socket; pin order VCC, GND, DIN, CLK, CS, DC, RST, BL | S8B-PH-SM4-TB (JST) | SMD | `Connector:Conn_01x08_Socket` / `Connector_JST:JST_PH_S8B-PH-SM4-TB_1x08-1MP_P2.00mm_Horizontal` | Waveshare 1.54inch LCD Module wiki (pin table read 2026-10-04) | whether the module ships the cable; BL drive (module has its own transistor: Unverified); stock |
| SW-A..Y | four game buttons | PTS645SM43SMTR92 (6 mm) default; a 12 mm SMD tactile as the "bigger button" option | SMD | `Switch:SW_Push` / `Button_Switch_SMD:SW_SPST_PTS645Sx43SMTR92` | ruling: button size is John's | John's choice of size before footprints (phase 5) |
| SW-JOY | 5-way joystick switch | SKRHABE010 (Alps) | SMD | `Switch:SW_Push` x5 / **footprint drawn from the Alps datasheet** (reason: KiCad ships none; the part is a standard stocked item). Alternative with no custom work: five PTS645 tactile buttons as a direction pad | today's HAT has a similar part; John accepts buttons instead of a joystick | datasheet (official Alps); footprint; stock; John's preference |

## Block 5: audio

| Ref | Part | MPN | Package | KiCad symbol / footprint | Source | To check |
|---|---|---|---|---|---|---|
| U-AMP | class-D mono amplifier | PAM8302AASCR (Diodes) | SOP-8 | `Amplifier_Audio:PAM8302AAS` / `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` | HR-033, HR-P02 | datasheet (official Diodes); package; stock |
| R/C-AUD | PWM to analog filter from GP22 | 1 kΩ + 100 nF (approx.) | 0402 | `Device:R`, `Device:C` | general practice | values at schematic |
| J-SPK | speaker connector | JST PH 2-pin SMD (same as J-BAT, different silkscreen) | SMD | as J-BAT | ruling item 4 | |

## Block 6: microSD

| Ref | Part | MPN | Package | KiCad symbol / footprint | Source | To check |
|---|---|---|---|---|---|---|
| J-SD | push-push microSD slot | 104031-0811 (Molex) | SMD | `Connector:Micro_SD_Card` / `Connector_Card:microSD_HC_Molex_104031-0811` | HR-P01 | datasheet (official Molex); stock |
| R-SD | pull-ups on CS, MOSI, MISO, DAT1, DAT2 | 10 kΩ x5 | 0402 | `Device:R` | HR-P01 | |
| C-SD | slot supply | 10 µF + 100 nF | 0603, 0402 | `Device:C` | HR-P01 | |
| U-ESD-SD | ESD on card lines (optional) | TPD4E05U06 | | `Power_Protection:TPD4E05U06DQA` | HR-P01 "ESD array" | decide at schematic |

## Block 7: sensors and connectors

| Ref | Part | MPN | Package | KiCad symbol / footprint | Source | To check |
|---|---|---|---|---|---|---|
| U-RTC | real-time clock | DS3231MZ+ (Analog Devices) | SOIC-8 | `Timer_RTC:DS3231MZ` / `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` | HR-P02 | datasheet (official ADI); stock |
| BT-RTC | CR1220 holder | 3001 (Keystone, 12 mm) | SMD | `Device:Battery_Cell` / `Battery:BatteryHolder_Keystone_3001_1x12mm` | DR-033 app. I.2 | **verify** 3001 takes a CR1220 (12.5 mm); Keystone drawing |
| U-IMU | 6-axis IMU | LSM6DSOXTR (ST) | LGA-14, 2.5 x 3 mm | **custom symbol** (KiCad has LSM6DSL/DSM; pin map to compare) / **custom footprint** from the ST drawing | HR-P02; micropython-lib driver | datasheet (official ST); stock |
| J-QT | STEMMA QT / Qwiic | SM04B-SRSS-TB (JST SH, 1 mm) | SMD | `Connector:Conn_01x04_Socket` / `Connector_JST:JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal` | DR-033 app. I.4 | stock |
| R-I2C | I2C pull-ups | 4.7 kΩ x2 | 0402 | `Device:R` | HR-P02 | |
| J-EXP | expansion header: GP1, GP28, SDA, SCL, 3V3, GND | 1 x 6, 2.54 mm | SMD or THT | `Connector:Conn_01x06_Pin` / `Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical` | DR-033 app. I.4 | |
| JP-INT | RTC alarm onto GP14 (wired-OR with IMU INT1) | 2-pad solder jumper, open | | `Jumper:SolderJumper_2_Open` / `Jumper:SolderJumper-2_P1.3mm_Open_Pad1.0x1.5mm` | HR-P02 | |

## Block 8: wireless

| Ref | Part | MPN | Package | KiCad symbol / footprint | Source | To check |
|---|---|---|---|---|---|---|
| U-RF | Raspberry Pi Radio Module 2 | RM2 (SC1169) | 21 castellated pads, 1.5 mm pitch, 14.5 x 16.5 mm | **custom symbol and footprint** from `refs/rm2-datasheet.pdf` | ruling item 3; HR-033 pins GP23/24/25/29 | pad map and antenna keep-out from the datasheet; stock (about 4 USD) |

## Custom library work (phase 5)
RM2 (symbol + footprint), LSM6DSOX (symbol + footprint), Alps 5-way joystick (footprint), MAX17048 (symbol, if kept), RP2350A land pattern check. All drawn from the official datasheets, saved in `pcb/kicad/lib/`.

## Datasheets to download next (official sources, John's approval needed)
BQ24074 and TPS63001 (ti.com), DW01A (Fortune), FS8205A, APS6404L (AP Memory), ABM8-272 and AOTA-B201610S3R3 (Abracon), USB4085 (GCT), USBLC6-2SC6 (ST), PAM8302A (Diodes), 104031-0811 (Molex), DS3231MZ (ADI), LSM6DSOX (ST), SKRHABE010 (Alps), Keystone 1042 and 3001, JST PH and SH drawings, PTS645 (C&K), PCM12 (C&K).
