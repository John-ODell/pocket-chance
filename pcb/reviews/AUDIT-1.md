# Independent PCB audit 1

Date: 2026-10-04. Scope: the files present in this checkout, inspected independently before reading the designer's notes.

**Disposition: BLOCKED. The supplied schematic and PCB are empty placeholders, not an implemented handheld circuit. No claim about electrical correctness, battery safety, or readiness for fabrication can be made.** This is a missing-design finding, not evidence that a particular implemented circuit is faulty.

## What I opened and read first

- Read the entire `pcb/kicad/pocket-chance-board.kicad_sch` directly. It contains an A3 root sheet, title block, an empty `lib_symbols` section, and one root sheet instance. There are no component instances, wires, labels, junctions, power symbols, or child sheets. Its title-block comment explicitly calls it empty.
- Attempted to access `pcb/kicad/exports/pocket-chance-board-schematic.pdf` and `pcb/kicad/exports/erc.rpt`. Neither exists; the `exports` directory itself is absent. Consequently I could not open or visually inspect the requested PDF or read the requested historical ERC report.
- Attempted to inventory `pcb/refs/`. That directory is absent, including ignored files. None of the requested official RP2350/RP2040 datasheets or hardware design guides, Pico W/Pico 2 W datasheets, RM2 datasheet, flash datasheet, or other part datasheets could be read there. No external sources were downloaded or substituted.
- Read the entire `pcb/kicad/pocket-chance-board.kicad_pcb`. It contains layers and setup metadata, only the unnamed net 0, and no footprints, tracks, vias, zones, board outline, or antenna keep-out.
- Read `docs/HARDWARE.md`, as specifically requested for the pin comparison. It documents an existing Waveshare RP2040-Plus with a 1.3-inch HAT, rather than the proposed RP2350A handheld with a 1.54-inch module. Its GPIO map is recorded below as the requested compatibility target, not evidence of wiring in this design.
- Exported a KiCad XML netlist and fresh all-severity ERC report using `/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli`, exclusively to `/tmp/pocket-chance-audit-1.S9e6di/`. The exporter identifies itself as Eeschema 10.0.6; the source files identify their generator as 9.0. The netlist has empty `components`, `libparts`, `libraries`, and `nets` elements. ERC reports 0 messages, 0 errors, and 0 warnings. It lists four ignored checks: a global label appearing only once, four connection points joined together, SPICE model issues, and footprint filter mismatches.
- Checked working-tree status before and after these exports: no repository changes at either point. No design editor, save operation, fabrication export, or circuit modification was performed.

The independent findings and checklist below were written before reading `pcb/requirements/REQUIREMENTS.md`, `pcb/STAGE2.md`, `pcb/bom/PARTS.md`, or existing review files. No other planning summaries were used to establish these findings.

## Numbered findings

1. **BLOCKER — The circuit has not been implemented.** Exact component reference: none exist. Exact net: none exist. Affected files: `pcb/kicad/pocket-chance-board.kicad_sch` and `pcb/kicad/pocket-chance-board.kicad_pcb`. The source and exported netlist contain no actual circuit; the PCB contains no physical implementation. It cannot perform any of the described handheld functions as supplied. Source: direct inspection of those files and the scratch XML netlist; these are native design files without PDF page numbers. Suggested fix: implement the complete schematic with actual parts, values, pin connections, and power circuitry, then implement the PCB and submit both for a new independent audit before fabrication or power-up. This finding does not authorize changes in this audit.

2. **MAJOR — Required audit evidence is missing.** Exact component reference and net: not assignable; this is a project-wide evidence gap. The requested schematic PDF, historical ERC report, and entire local reference directory are absent. There is no source-backed way to verify symbol pin numbers, supply requirements, charge settings, crystal/load choices, or RM2 integration. Source: direct filesystem checks; no datasheet page is available. Suggested fix: supply the matching PDF/ERC exports and official documents for the exact selected part variants, with document revisions identified, alongside the implemented design. A subsequent review must cross-check the exports against the native schematic.

3. **NOTE — The fresh zero-violation ERC result is vacuous.** Exact component reference and net: none exist. ERC can parse this sheet but has no circuit to check. Its zero count is not a safety or functionality pass; four checks are also reported as ignored. Source: scratch `erc.rpt`, text report without page numbers, and scratch `audit.net`. Suggested fix: rerun ERC on the implemented circuit, inspect configured checks and every exclusion, and independently verify circuit behavior against datasheets. Review the ignored checks for relevance rather than assuming they represent existing defects.

4. **NOTE — The pin-map document describes a different physical platform.** Exact component reference and net: none exist in the proposed schematic. `docs/HARDWARE.md` describes the existing RP2040-Plus/HAT setup; it provides the requested GPIO targets but cannot establish RP2350A wiring or screen-module compatibility. Source: `docs/HARDWARE.md`, “The parts” and “Pin map” sections; Markdown has no page numbers. Suggested fix: preserve the specified compatibility map where intended, and document the new board's actual MCU package pins and module connections once implemented. Do not infer that the older platform's measured behavior validates the new hardware.

There are no supported findings about particular reversed diodes, incorrect resistor values, misnumbered pins, or faulty named nets: none of those components or nets are present. Assigning references, values, datasheet pages, or circuit faults here would invent evidence.

## CHECKED AND FOUND CORRECT

- The supplied schematic parses and exports through KiCad CLI. The netlist corroborates the direct source inspection, including the single root sheet and absence of components/nets.
- The fresh ERC report accurately records zero reported violations for this empty input. This is only a tool-result check, not electrical approval.
- The GPIO targets transcribed from `docs/HARDWARE.md` match the user's requested map: screen DC 8, CS 9, SCK 10, MOSI 11, RST 12, backlight 13; buttons A/B/X/Y 15/17/19/21; joystick up/down/left/right/press 2/18/16/20/3. These assignments are distinct within that list. No actual schematic pin assignment is verified.
- No floating or double-driven net, wrong named net, or incorrectly placed power flag was observed, because the design has no nets or power flags. This does not mean the intended board has passed those checks.

**No implemented electrical subsystem was found correct.**

## Could NOT verify, and why

In every row below, **actual component reference: absent; actual net: absent**. Functional names are audit topics supplied by the user, not names discovered in the schematic. The common impediments are an empty design and absent official references. No numerical component values or package pin numbers are inferred.

| Requested check | Specific verification that remains impossible |
|---|---|
| Power-up and reset | RUN biasing/reset behavior, BOOTSEL action, flash CS connection to BOOTSEL, startup timing and power sequencing. No MCU, switches, resistors, or wiring. |
| XOSC | Crystal specification, its connection to the oscillator pins, load capacitors, grounding and placement. No crystal or capacitors; RP2350 guide/datasheet absent. |
| Every MCU supply pin and decoupling | Package pin enumeration, supply domains, per-pin capacitors, bulk capacitance, capacitor types and placement against the hardware guide. No MCU/package pinout or supply nets. |
| 1.1 V core regulator | Regulator topology and all required support parts, switching connections, inductor/capacitors and ratings. No circuit or source document; neither compliance nor absence of a required individual part can be established. |
| USB-C | Connector pin mapping, both CC resistors, D+/D- connections and any series resistors, ESD selection/placement, VBUS path, shield and ground connections. No USB connector or protection circuitry. |
| 16 MB QSPI flash | Exact flash variant/capacity, voltage, bus pin order, chip select and pull-up/BOOTSEL interaction, power and decoupling. No flash part or wiring; flash datasheet absent. |
| 8 MB PSRAM | Exact variant, interface, supply, shared-bus connections, dedicated chip-select choice and its supported MCU function. No PSRAM or wiring; PSRAM datasheet absent. |
| Charger and power path | Charger part, battery/system/USB terminal connections, charge-current programming, input limit, thermistor-pin handling, status-output drive type/pull-ups, thermal requirements and behavior with battery absent/present. No charger or programming parts. |
| Battery protection | Protection IC and FET arrangement, cell connections, voltage/current thresholds, fault recovery and whether every intended charge/discharge path is protected. No protection circuit or cell specification. |
| Reverse-polarity guard | Device orientation, body-diode paths, voltage/current ratings, leakage/backfeed paths and behavior when the JST battery is plugged in backwards, both with and without USB. No guard or connector wiring; cannot predict whether the cell or board would be damaged. |
| 3.3 V buck-boost | Selected IC, inductor specification, input/output capacitors, feedback network/output voltage, enable state and switch/power-path behavior. No regulator or support components. |
| RM2 module | Module pin mapping, supplies/decoupling, host interface/control signals, firmware integration requirements and antenna clearance/keep-out. No module, connections, outline or placement; RM2 and Pico wireless references absent. |
| microSD | Socket mapping, interface voltage, power/decoupling, required pull-ups and their values, card detect and interaction with shared buses. No socket or nets. |
| I2C and STEMMA QT | Pull-up presence, aggregate resistance, voltage domain, connector order and address conflicts among actual selected device variants. No devices or addresses can be established. |
| IMU / RTC interrupt and solder jumper | Exact output types and polarities, whether sharing is electrically safe, pull-up, jumper default and alternate routing, and firmware distinction between sources. No IMU, RTC, interrupt net or jumper. |
| DS3231 and coin cell | Exact device/package, main/backup supply connections, coin-cell polarity/type, any unintended charging path and isolation. No RTC/coin-cell circuit. |
| Speaker amplifier | Exact amplifier, power, decoupling, input/control bias, output topology, speaker connections/ratings and shutdown default. No amplifier or speaker circuit. |
| Screen | Module-specific pin order, supply, SPI/control mapping, reset and backlight drive/current. No module connection or drive circuit. The user's 1.54-inch module is not established by the 1.3-inch HAT documentation. |
| Buttons and joystick | Actual GPIO mapping to the documented targets, polarity, pull-ups and ground connections. No switches or MCU pin assignments. |
| SWD header | Pin mapping, reference voltage, ground, reset accessibility and power/backfeed exposure. No debug header. |
| Net integrity / ERC completeness | Floating pins/nets, double drivers, naming collisions, wrong net names, missing power flags or hidden supply connections. No circuitry to analyze; zero violations cannot answer these questions. |
| First-power-up damage risks | Cell shorting/overcharge, reversed battery current paths, regulator overvoltage, USB backfeed, incorrect rail connections, part ratings and PCB thermal/current capacity. All remain unverified. No safe-to-power conclusion is possible. |

The missing reference set includes all official sources named in the request, plus exact-part sources for the PSRAM, USB protection, charger, protection IC/FETs, reverse guard, buck-boost, crystal, display module, amplifier, IMU, RTC, connectors and selected cell. A part selection in a prose BOM would not substitute for an implemented circuit or its datasheets. Layout-dependent checks also require footprints, copper, planes, placement and an outline; the empty PCB cannot support them.

## Compared with the designer's notes

After recording the independent audit above, I read `pcb/requirements/REQUIREMENTS.md` in full, `pcb/STAGE2.md`, `pcb/bom/PARTS.md`, and both existing substantive reviews in `pcb/reviews/`: `ENGINEER_ANSWERS.md` and `INTAKE_REPORT.md`. The `.gitkeep` file contains no review. I did not follow their links to additional planning files or hardware reviews; those cited reports are not independent evidence in this audit.

1. **Agree with the actual stage status.** `STAGE2.md` phase 1 calls this an empty project, and phases 3 (schematic), 4 (electrical review), and 6 (layout) are not started. This matches the files exactly. Its “ERC runs clean” statement is credible as a tooling check, but must not be presented as a completed electrical review. A previous PDF export may have worked elsewhere; the requested PDF is absent in this checkout.

2. **Agree that the parts list is provisional.** `PARTS.md` calls itself a shortlist and explicitly leaves numerous datasheets, package drawings, programming values and custom symbols/footprints to check. Its proposed references, such as U1/U2/U3, U-CHG and JP-INT, are prose identifiers only; they are not schematic instances. I neither approve nor reject its listed values or pin-number claims without the missing official sources and an implemented circuit.

3. **The reference availability claims cannot be reproduced here.** `REQUIREMENTS.md` and the intake report's second-pass update say reference PDFs were read, and the shortlist cites RP2350, flash and RM2 PDFs. `pcb/refs/` is absent now. I cannot independently verify those citations, page references, quotations or conclusions. This could be a different checkout or missing ignored files; it is not proof that the prior reader misrepresented their work.

4. **The requirements combine an older baseline with the new scope.** Early sections describe an RP2040/1.3-inch platform and choices not yet decided; section 11a and `STAGE2.md` introduce the RP2350A handheld. I agree that the old GPIO targets should be preserved where required. I disagree with treating older hardware measurements or generic RP2040 assumptions as validation of the new MCU, crystal, core regulator, wireless interface or display. They need independent RP2350A and exact-module verification. The shortlist specifically proposes DS3231MZ+, not an unspecified DS3231 variant; the eventual audit must use that exact part's document and pinout if retained.

5. **NOTE — Pin-plan count is inconsistent.** `REQUIREMENTS.md` section 11a first says the plan uses 29 of 30 GPIO, then says all 30 are used. Its table assigns GPIO0 through GPIO29, including GP1 as a spare/expansion function and GP28 as battery sensing/expansion. No duplicate assignment is apparent in that planning table, and its screen/input map agrees with the requested map. Suggested fix: distinguish assigned, actively consumed and available GPIO explicitly. This is a documentation finding; actual MCU connections, alternate functions and firmware compatibility remain unverified.

6. **MAJOR planning gap — No reverse-polarity guard is identified.** `PARTS.md` block 3 proposes U-PROT (DW01A), Q-PROT (FS8205A), J-BAT and a second cell connector with JP-CELL, but does not identify a separate reverse-polarity guard or demonstrate that the proposed topology provides one. Actual net: absent. I cannot infer backwards-battery protection from the words “cell protection” alone. Source: `PARTS.md` block 3; the distinction between fault protection and demonstrated reverse-polarity tolerance is **from general practice, unverified** for these proposed parts. Suggested fix: explicitly document the guard and trace all reversed-battery current paths, with USB both present and absent, against the exact protection/FET/charger/regulator datasheets. Also verify the cell-selector topology if both connectors are retained. This is not a claim that an existing guard is wired incorrectly: no circuit exists.

7. **Agree with the named safety topics, not with any implied verification.** The notes call for battery protection, coin-cell isolation, microSD pull-ups, source-based footprint checks and shared-interrupt review. These are appropriate items for the next audit. `PARTS.md` describes JP-INT as an open jumper connecting the RTC alarm and IMU INT1 to GP14; the phrase “wired-OR” does not establish that both outputs can safely share the line. Exact output modes, reset defaults, pull-ups and any required configuration must be demonstrated using the exact RTC/IMU sources. This requirement is **from general practice, unverified** for the proposed parts. The proposed charger thermistor arrangement likewise needs verification against its datasheet and the actual cell; a draft resistor entry is not a verified charging-safety design.

No design, requirement, shortlist or existing review was edited. The only new repository file is this audit. No orders, purchases, downloads or messages to third parties were made. Scratch exports remain outside the repository. **The next meaningful electrical audit requires the populated design and matching official sources; this report grants no fabrication or first-power-up approval.**
