# HR-P05: Independent electrical check of AUDIT-2's engineering findings

- Reviewer: microcontroller expert, 2026-10-04. Written **after** reading `pcb/reviews/AUDIT-2.md` and the schematic's connection table (`pcb/tools/gen_sch.py`, head `ff0b75a`), and **before** opening the designer's response, as the PM asked. The comparison with the designer's response is in the last section, added afterwards.
- Each verdict is AGREE, DISAGREE (with a calculation or a datasheet point) or CANNOT TELL (what is missing). Where I quote a part's register default or constant from memory, I say so.

## #1 Reverse-polarity guard Q2: AGREE, BLOCKER
My own reading of the connection table, made before the audit: Q2 is drawn as an AO3401A (value DMG2305UX; both are SOT-23 P-FETs with pin 1 gate, pin 2 source, pin 3 drain) with pin 1 → BAT−, **pin 2 (source) → CELL_P (the cell's positive)**, pin 3 (drain) → CELL_G → R22 → BAT+. That is **source on the cell, drain on the board**, the opposite of PCB-001's text ("drain to the cell, source to BAT+").
- **Correct cell:** V_GS = V(BAT−) − V(cell+) = −V_cell, the channel is on at once, the cell powers the board. Works, which is why a bench test with a correct cell would never reveal the error.
- **Reversed cell** (cell+ on the connector's negative pin, cell− on CELL_P): V_GS = +V_cell, channel off, as intended. But the P-FET's body diode conducts **from drain to source**, i.e. from BAT+ toward CELL_P, which now sits at −V_cell. The diode is forward-biased and pulls the BAT+ node down to about −(V_cell − 0.7) V. Everything on BAT+ then sees a negative rail: U7's VCC through R20, U5's BAT pins, C22, R23 into GP28 (limited to ~30 µA by 100 kΩ, survivable), and with USB present U5 drives charge current into that path. The guard fails its only purpose.
- **Fix:** swap source and drain so the **drain is on the cell and the source on BAT+** (the textbook topology the request describes), gate still at the connector's negative pin. Then: correct cell → the body diode (drain→source, cell→board) lifts BAT+ first and V_GS = −V_cell turns the channel on, ~25 mV drop; reversed cell → the diode's anode is at cell− (negative) and blocks, V_GS = +V_cell keeps the channel off, nothing conducts, with or without USB (U5's BAT output then sits on the source with the drain floating at a negative potential it cannot reach). No cell → V_GS = −V(BAT+), channel on, the connector shows the charger voltage, normal.
- Also: the DMG2305UX's pin order should be confirmed from its datasheet when downloaded; it is G-S-D on every SOT-23 P-FET I know, so the fix is a net swap, not a part change.

## #2 Battery divider into GPIO28 with the board off: AGREE, MAJOR
With SW3 off, +3V3 and IOVDD are 0 V while BAT+ (3.0–4.2 V) still feeds R23/R24, so GP28 is offered 1.5–2.1 V. The RP2350's GPIO absolute maximum is IOVDD + 0.5 V, so the pad's protection diode to IOVDD conducts: about (2.1 − 0.6) V / 100 kΩ ≈ **15 µA** flows into the unpowered IOVDD rail. Not destructive at that current, but outside the datasheet limit and a faint back-powering of the chip; plus the divider drains the cell at ~19 µA always (1000 mAh lasts years, so that part is fine).
- Fixes, in order of preference: (a) measure the cell through the **fuel gauge over I2C** (powered from +3V3, so dead when the board is off) and drop the divider: the HR-P01 footprint; (b) a **switched divider**: a small P-FET in the divider's top leg whose gate is pulled to BAT+ by 100 kΩ and pulled low by an N-FET driven from +3V3, so the divider exists only when the board is on (two SOT-23s or one dual package); (c) if neither, raise both resistors to 1 MΩ (leak ≈ 1.5 µA) **and document the spec excursion** as accepted. Switching only the bottom leg does not help: the top resistor alone still presents BAT+ to the pin.
- J8 pin 6 is the same node; label it "battery sense ADC" on the silkscreen, not a GPIO.

## #7 Charge current for an unidentified cell: AGREE, MAJOR
R14 = 1.8 kΩ gives I_CHG = K_ISET / R_ISET = 890 / 1800 = 494 mA nominal, 443–542 mA over TI's K_ISET range (from the datasheet as the audit cites it; my earlier figure from memory agrees). That is 0.5 C for a 1000 mAh cell and **1 C for a 500 mAh cell**, above the 0.5 C most pouch cells allow. Since the cell is not yet chosen, **the fitted default should be the safe one: 3.6 kΩ (247 mA)**, which charges a 1000 mAh cell in about 4–5 hours and never over-rates a 500 mAh one; move to 1.8 kΩ only when a ≥ 1000 mAh cell is in hand and its datasheet read. ITERM: the audited rev 0.2 had R17 (25 mA); R17 was removed before the audit was read, so termination is the BQ24074's open-pin default of 10 % of I_CHG (≈ 49 mA), which is also fine. The 6.3 h timer (R16) is consistent with either cell.

## #8 Cell temperature not sensed (TS fixed 10 kΩ): AGREE, as a documented limitation
TI's sanctioned way to disable the check; it means the charger will charge a cell at any temperature, and its own thermal regulation protects the chip, not the cell. Acceptable for an indoor handheld with protected cells **only if written down as such** (PCB-001 says "treats the cell as always at a safe temperature", which is honest). Keep the NTC footprint; if the chosen cell comes with a thermistor lead, use a 3-pin connector and the NTC, and the limitation disappears. CANNOT TELL whether the cell's own protection board includes a thermal cut-off; most hobby PCMs do not.

## #9 Shared interrupt line (JP2): AGREE, conditional on closing JP2
From memory of the LSM6DSOX registers (CTRL3_C: PP_OD = 0 push-pull and H_LACTIVE = 0 active-high at reset): the IMU's INT1 is a **push-pull, active-high** output until firmware changes it, and the DS3231's INT/SQW is open-drain active-low. Closing JP2 with the IMU at its defaults puts a push-pull high against an open-drain low whenever the RTC alarms: contention within the two chips' drive limits, possibly damaging over time. And no pull-up exists on IMU_INT/RTC_INT; the RP2350's internal pull-up (~50 kΩ) only exists once firmware enables it.
- Fix: a 10 kΩ pull-up to +3V3 on IMU_INT (needed by the open-drain RTC output anyway); firmware sets PP_OD = 1 and H_LACTIVE = 1 on the IMU before JP2 is ever closed; and because the IMU's registers reset with its power, **leave JP2 open on spin 1** unless the firmware's init runs before any RTC alarm can fire. Separate pins would be better but there are none.

## #10 L2 selection and saturation: AGREE, MAJOR
A nominal "2.2 µH" with a 1210 footprint and no part number cannot be judged. The calculation that picks it: boosting from V_IN = 3.0 V (an empty cell) to 3.3 V at I_OUT = 0.5 A, average inductor current ≈ I_OUT × V_OUT / (V_IN × η) = 0.5 × 3.3 / (3.0 × 0.9) ≈ 0.61 A; ripple ΔI = V_IN × D / (L × f) with D ≈ 1 − V_IN·η/V_OUT ≈ 0.18 and f = 1.5 MHz gives ≈ 0.16 A, so the peak is ≈ 0.7 A at 0.5 A load and ≈ **1.4 A at a 1 A load** (screen at full backlight, a card write burst and radio TX together). The TPS63001's switch current limit is about 1.8 A typical, and TI's selection rule is an inductor saturation current at or above that limit. So: **2.2 µH ± 20 %, I_SAT ≥ 2 A, DCR ≤ ~70 mΩ, shielded, 3 x 3 mm class** (a Coilcraft XFL3012-222, TDK VLS3012 or Murata DFE322512 family part; confirm against the chosen one's datasheet). The 1210 footprint fits those. Capacitors: 10 µF X5R/X7R at ≥ 10 V for VSYS (up to 4.9 V) and ≥ 6.3 V for +3V3, with DC-bias derating in mind; the nominal values are right.

## #12 Amplifier start-up mute and bypass: AGREE, MINOR
SD (pin 1) tied straight to +3V3 enables the PAM8302A the instant the rail rises, before the PWM pin is driven, so a power-on pop is likely. Fix without a GPIO (none is free): an RC on SD, 10 kΩ from +3V3 and 1 µF to ground, so SD rises ~10 ms after the rail and the chip's own soft-start handles the rest; and add the datasheet's local 1 µF at VDD next to the 10 µF (C32). Both are cheap and standard. CANNOT TELL the pop's loudness without the speaker; it is a nuisance, not a hazard.

## #13 USB500 mode and R15: AGREE, NOTE
EN2 low and EN1 pulled to VBUS select USB500: a 500 mA input limit, and R15 (ILIM) is then inactive. That is the right mode for a board whose CC pull-downs ask for default power. Document it, and do not budget loads against R15. The only nuance: strict USB 2.0 allows 100 mA before enumeration; every practical host and every Type-C source gives 500 mA or more, and MicroPython enumerates within a second, so I would not change the design for it.

## Not in my brief but seen while reading
- U7 (DW01A) references BAT−, with R20/C27 from the guarded BAT+: after the #1 fix it never sees a negative rail. Its own reversed-cell tolerance is then moot.
- The PWM audio filter (1 kΩ, 10 nF: f_c ≈ 16 kHz) is right for a 20–30 kHz PWM carrier; keep the carrier above 20 kHz in firmware.

---

# Part 2: verification of the fixes in commit `808ccf1` (schematic rev 0.3)
Read from the connection-table diff (`pcb/tools/gen_sch.py`) **before** the designer's response, per the PM's instruction. John's decision: keep this commit as the working design and verify it; layout waits.

## #1 Q2 reverse-polarity guard: VERIFIED FIXED
Rev 0.3 wires Q2 (value now AO3401A, matching its symbol) as pin 1 gate → BAT−, **pin 2 source → CELL_G → R22 → BAT+ (board side)**, **pin 3 drain → CELL_P (cell positive)**: the textbook topology, exactly the swap Part 1 prescribed. Walking every case:
| Case | Channel (V_GS = V_gate − V_source) | Body diode (drain → source) | Result |
|---|---|---|---|
| Correct cell, no USB | gate at cell−, source rises to cell+ through the diode → V_GS = −V_cell → **on** | conducts cell → board at power-up, then shunted by the channel | board powered; ~25 mV drop at 0.5 A |
| Correct cell, USB present | same, source also held by the charger's BAT output | as above | charge current flows board → cell through the on channel (a P-FET channel conducts both ways) |
| Reversed cell, no USB | gate at cell+ (on BAT−), source at ~0 → V_GS positive → **off** | anode at drain = cell− (negative) → **blocks** | no current. The cell's other lead sits on BAT−, whose only paths to the board are the FS8205A pair: the DW01A has no supply (BAT+ undriven) so both FETs are off, and their body diodes both point source→drain (S1 BAT−→D, S2 GND→D), which blocks BAT−→GND and GND→BAT− alike. Nothing conducts in either direction |
| Reversed cell, USB present | source at the charger's BAT voltage (~4.2 V), gate at cell+ relative to a floating BAT− → V_GS not negative → **off** | drain negative → blocks | the charger drives BAT+ into an open; BAT− still has no return path (same FS8205A argument). No current |
| No cell, USB present | V_GS = 0 − V(BAT+) → on | | the connector shows the charger voltage: normal, and why a correct cell plugs in live |
The designer's comment block in the generator says the same thing in fewer words. Agreed, fixed. Residual: none electrical; the "red wire on +" silkscreen remains the human safeguard against a cell wired to a different standard.

## #2 Gated battery divider: VERIFIED FIXED
Q4 (P-FET: gate DIV_PG, source BAT+, drain DIV_TOP), R39 100 kΩ BAT+ → DIV_PG, Q3 (2N7002 N-FET: gate +3V3, source GND, drain DIV_PG), R23 100 kΩ DIV_TOP → VBAT_SENSE, R24 100 kΩ VBAT_SENSE → GND, C28 100 nF.
- **Board on:** +3V3 = 3.3 V drives Q3 on (2N7002 threshold 1–2 V), DIV_PG → 0, V_GS(Q4) = −V_BAT → Q4 on, DIV_TOP = BAT+, the divider reads V_BAT/2 (1.5–2.1 V) with ~18 µA in the divider and ~37 µA through R39: fine.
- **Board off:** +3V3 = 0, Q3 off, R39 holds DIV_PG at BAT+, V_GS(Q4) = 0 → Q4 off; DIV_TOP is then tied to ground only through R23 + R24, so **VBAT_SENSE sits at 0 V** and GP28 sees nothing with IOVDD at 0 V. Q4's body diode (DIV_TOP → BAT+) is reverse-biased, so it cannot lift DIV_TOP. Zero current anywhere in the branch when off.
- Matches the Pico W's gated VSYS divider in principle. Agreed, fixed. J8 pin 6 now labelled as the ADC node. Residual: the firmware must wait a few µs after boot before the first reading (Q4 turns on with the rail), which the game's boot order already guarantees.

## #7 and #8 Charge current and cell temperature: FIXED AS A DECISION, with the residual stated
Rev 0.3: J3 is a 3-pin JST-PH (1 = +, 2 = −, 3 = TS); R12 10 kΩ on TS is **fitted by default** (temperature check bypassed); R14 stays 1.8 kΩ (443–542 mA) with the assumed cell written down (protected pouch ≥ 1000 mAh, ≥ 0.5 C, charging 0–45 °C). John has chosen this, relying on the cell's own protection board and the 0.5 C rate. Plainly, the residual risk is two-fold:
1. **A smaller cell charged too hard.** If a 500 mAh cell is ever fitted with R14 unchanged, it is charged at 0.9–1.1 C. Most pouch cells rate 1 C as the maximum, 0.5 C as recommended; the cell's PCM does **not** limit charge current (it trips at 2–3 A). Consequence: shortened life and more heat, not a fire from that alone. Guard: the purchase rule ("1000 mAh or more, protected, JST-PH") on the silkscreen and in `PARTS.md`. My preference remains the safer default of 3.6 kΩ (247 mA) until a specific cell is in hand; a 1000 mAh cell then charges in 4–5 h, which a handheld can live with. This is a judgement call John has made the other way; the trade is charge time versus a margin for a wrong purchase.
2. **No cell-temperature stop while R12 is fitted.** The charger will charge a cell below 0 °C (lithium plating) or above 45 °C. The charger's thermal regulation protects its own die, not the cell; a typical PCM has no temperature cut-off. For an indoor handheld with a quality protected cell this is the standard hobby-board posture, and it is now honestly documented; it is not acceptable for a device left in a car or charged outdoors in winter. The 3-pin socket is the right hook: a cell with an NTC lead plus R12 removed restores real protection at zero board change.
Verdict: the design as fixed is consistent and honest; the residual is John's to accept, and he has.

## #9 Shared interrupt: VERIFIED FIXED, with the operating rule
R42 10 kΩ pull-up on RTC_INT (the DS3231M output is open-drain); R43 1 kΩ in series to RTC_INT_R; JP2 (open) joins RTC_INT_R to IMU_INT; the label now carries the rule "close only after firmware sets IMU INT1 open-drain, active-low". If JP2 is closed while the IMU is still push-pull high and the RTC pulls low, the contention current is 3.3 V / 1 kΩ ≈ 3 mA, inside both chips' limits (the DS3231's INT sinks 3 mA by spec), so a wrong order no longer risks damage. With the IMU set open-drain, the shared line's pull-up is R42 through R43 (11 kΩ), a low from the RTC reads ≈ 0.3 V at GP14: clean. Agreed, fixed. Residual: the IMU's open-drain setting does not survive a reset, so firmware must set it in init before any alarm can fire; spin 1 should ship with JP2 open.

## #10 L2 and the capacitors: VERIFIED IN FORM, one number outstanding
L2 is now a named part, Abracon ASPIAIG-F4020-2R2M (4 x 4 x 2 mm, shielded, 2.2 µH), with an Abracon footprint; C23 10 µF 16 V X5R 0805 on VSYS, C25/C26 10 µF 10 V X5R 0805 on +3V3. The voltage ratings and the 0805 body (less DC-bias loss than 0603) are right. **CANNOT TELL** the one thing that matters until the Abracon datasheet is read: I_SAT and DCR for the 2R2 member; from the family's class I expect I_SAT around 3–4 A and DCR a few tens of mΩ, which would clear my Part 1 requirement (≥ 2 A, ≤ ~70 mΩ) comfortably. The designer marks it "to confirm"; agreed.

## #11 Second DVDD capacitor: VERIFIED
C40 4.7 µF on 1V1 placed by intent at DVDD pin 23, away from LX/COUT, as the RP2350 datasheet asks. Correct; the placement itself is a layout check.

## #12 Amplifier mute and bypass: VERIFIED FIXED
SD now AMP_SD from R44 47 kΩ / C42 1 µF: τ = 47 ms, so SD crosses a ~1.4 V threshold about 26 ms after +3V3 is up (the designer says ~30 ms; the datasheet's 1–100 ms window is met), after the rail and the PWM pin have settled. C41 1 µF local at VDD beside C32 10 µF. Agreed, fixed. Residual: a brown-out that drops +3V3 briefly re-arms the delay, which is harmless.

## #13 R15: VERIFIED
R15 marked DNP with the reason (USB500 is the active limit). Correct and documented.

## #14 Symbols vs values: VERIFIED for Q2
Q2's value is now AO3401A, matching the symbol; U10's LSM6DSM-symbol-for-LSM6DSOX reuse was already pin-checked against the LSM6DSOX datasheet in `PARTS.md`.

## Still open after rev 0.3
1. L2's I_SAT/DCR from the Abracon datasheet (the only unverified number in the power path).
2. The DMG2305UX/AO3401A, DW01A, FS8205A, DS3231MZ, LSM6DSOX datasheets to be read by the designer for the pin facts I have given from memory (G-S-D order, DW01A thresholds, INT1 default modes).
3. The cell purchase rule on the silkscreen (or the 3.6 kΩ default), John's call.
4. Layout-dependent items the audit lists (antenna keep-out, regulator loop, decoupling placement) are not yet checkable.
5. The real board current (`hwtest/load_hold.py` with John's meter) still sizes nothing because nothing is fabricated yet; it remains the number the battery-life promise waits on.

---

# Part 3: three-way comparison (auditor, designer, expert) and what remains open
Read after Parts 1 and 2 were written. Designer's response: `pcb/reviews/AUDIT-2-RESPONSE.md`; the designer's final commit for the next audit is **`3134df4`**, which I checked differs from `808ccf1` only by an on-schematic battery note and document updates (no circuit change), so Part 2's verification applies to it.

| # | Auditor | Designer | Expert (me) | Agreement |
|---|---|---|---|---|
| 1 Q2 guard | BLOCKER: body diode conducts into a reversed cell | FIXED, real: drain/source swapped, four cases argued | AGREE on the defect (found it independently before reading the audit); fix VERIFIED with the five-case table incl. the FS8205A body-diode argument | **All three agree** |
| 2 divider off-state | MAJOR: 2.1 V on GP28 with IOVDD 0 | FIXED, real: P-FET gated by an N-FET on +3V3 | AGREE on the defect (15 µA into IOVDD, out of spec); fix VERIFIED in both power states | **All three agree** |
| 7 charge current | MAJOR: no identified cell | AGREE, documented: assumed cell ≥ 1000 mAh at 0.5 C; 1.8 kΩ stays; purchase rule | AGREE; **judgement difference**: I would fit 3.6 kΩ (247 mA) by default until a specific cell is bought, trading charge time for a margin against a wrong purchase. John decided for 1.8 kΩ with the rule; that is his call and it is safe for the stated cell | Agree on facts; one preference differs, settled by the owner |
| 8 temperature | MAJOR: not sensed | AGREE, owner decision: 3-pin socket, R12 fitted, warning on the schematic | AGREE; residual stated plainly in Part 2 (hot/cold cell not stopped; indoor use with a protected cell is the standard hobby posture) | **All three agree**, risk documented |
| 9 shared INT | MAJOR conditional: no pull-up, modes unverified | FIXED: 10 kΩ pull-up, 1 kΩ series, JP2 open with the rule | AGREE; VERIFIED: contention limited to ~3 mA, firmware rule needed; ship JP2 open | **All three agree** |
| 10 L2 | MAJOR: nominal only | AGREE, fixed in part: Abracon ASPIAIG-F4020-2R2M named, caps rated; I_SAT/DCR open | AGREE; calculation gives peak ≈ 1.4 A at 1 A load, need I_SAT ≥ 2 A; CANNOT TELL the part's figure until its datasheet | **All three agree**; one number open |
| 12 amp | MINOR: no mute, no local bypass | FIXED: 47 kΩ/1 µF on SD, 1 µF at VDD | AGREE; VERIFIED (~26 ms delay) | **All three agree** |
| 13 USB500 | NOTE: R15 inactive | FIXED/documented: DNP, mode stated | AGREE | **All three agree** |
| 11 DVDD cap (not in my brief) | MINOR | FIXED: C40 at pin 23 | VERIFIED against the datasheet's wording | agree |
| 14 symbols vs values | NOTE | FIXED (Q2 value; U10 pin-checked) | AGREE for Q2; U10 relies on the designer's pin check | agree |

**Disagreements to bring to the PM:** none on any electrical fact. One documented difference of preference on #7 (default charge resistor), already decided by John.

**Open after rev 0.3 / `3134df4`, jointly:**
1. L2 I_SAT and DCR from the Abracon datasheet (needed: ≥ 2 A, ≤ ~70 mΩ).
2. DW01A and DS3231M official datasheets (the designer could not fetch them; John can save them from a browser): DW01A thresholds and delays before the first cell test; DS3231M INT behaviour on backup power.
3. L1 (core inductor) winding-orientation dot relative to LX/COUT (audit #6): from the Pico 2 design files or the minimal-design KiCad example, download pending John's approval. Layout/assembly item.
4. The 1.54" module's backlight drive type (transistor on the module or raw LED): inspection of a physical module.
5. The Keystone 3001 coin-cell holder drawing.
6. Everything layout-dependent in the audit (antenna keep-out, regulator loop, decoupling placement, USB impedance), checkable only when a layout exists.
7. The real board current (`hwtest/load_hold.py` with John's meter) for the battery-life promise; it does not block the schematic.

**Verdict for AUDIT-3:** the circuit at `3134df4` has no known electrical defect; the audited blocker (#1) and the off-state ADC exposure (#2) are fixed and independently verified; the cell-temperature and charge-rate posture is a documented owner decision with the residual stated; what remains open is datasheet confirmation of ratings and layout work that has not started.

---

# Part 4: corrections after the AUDIT-3 questions (2026-10-04, design commit b64c59b9f55986d6c2e08b3fd7a0abdca8cecb1b)
The record above is kept as written; these corrections supersede it where they conflict. Full reasoning is in the team-channel answer files (`pcb/team/20261004-145137_from-expert_to-auditor_ilim-dnp.md`, `…_reverse-cell-usb.md`, `20261004-145316_…_rm2-land-coordinates.md`), which are not committed; the substance is here.

## #13 R15 DNP: I WAS WRONG; the auditor is right
BQ2407x SLUS810N Table 7-1 (PDF p.8), ILIM: "Leaving ILIM unconnected disables all charging." No USB500 exception exists. Part 2's "R15 DNP correct" would have produced a board that never charges. Correction: R15 must be FITTED (3.0 kΩ is inside the 1.1–8 kΩ range) with EN1 high / EN2 low still selecting USB500; the resistor is inert for the limit in that mode but required for charging to be enabled at all. Also, with the K_ISET range, the worst-case cell current is ≤ 0.54 C in both configurations (1.8 kΩ with ≥ 1000 mAh; 3.6 kΩ with 500 mAh): marginally above a strict 0.5 C, within the 1 C most pouch cells allow; the documents should say "≤ 0.55 C worst case", not "0.5 C".

## #1 Reversed cell WITH USB present: Part 2's "no current" row was WRONG
I assumed BAT− floats. With USB present and no cell, U5 drives BAT+ ≈ 4.2 V, the DW01A is supplied between BAT+ (via R20) and BAT− and, in its normal state, holds both FS8205A channels ON, so BAT− sits at board ground (general DW01A behaviour; its datasheet is still not in `refs/`, thresholds and delays unverified). Insert a reversed cell into that state: Q2's gate (BAT−) is at 0 V and its source (BAT+) at 4.2 V, V_GS ≈ −4.2 V, the channel turns ON regardless of the body diode, and the loop U5 BAT → Q2 → cell (backwards) → BAT− → Q1 (on) → GND closes. The charger sources up to its limit (443–542 mA by ISET, 500 mA by USB500) backwards through the cell, and the DW01A sees a normal 4.2 V so nothing opens the loop: a hazardous latched state until the cell is pulled or its own PCM reacts (unverified). The no-USB rows of Part 2's table stand (U7 unpowered, Q1 off, BAT− floating, cell isolated).
Why no P-FET referenced to BAT− can fix it: the charger holds the source high and Q1 holds BAT− low in both cell polarities. The guard must sense the cell's polarity. Proposal (a claim for the designer): keep Q2 as drawn (drain CELL_P, source BAT+ side) and drive its gate from a sensor: R45 100 kΩ BAT+ → Q2 gate (default off); Q5 N-FET, drain to Q2's gate, source to GND, gate to CELL_P through 100 kΩ. Correct cell: CELL_P ≈ +V_cell turns Q5 on, Q2's gate goes low, Q2 on, power and charge flow. Reversed cell: CELL_P ≈ −V_cell, Q5 off, Q2's gate at BAT+, Q2 off, body diode blocks: no path with or without USB. No cell: Q2 off and the connector is dead, which is also safer than today's live 4.2 V. Margin to check: Q5's threshold against a weak cell (a 2N7002's V_GS(th) up to 2.5 V vs a 3.0 V empty cell is tight; a logic-level N-FET with V_GS(th) ≤ 1.5 V, or an NPN, removes it). I will re-verify whatever the designer draws.

## AUDIT-3 #3 RM2 land pattern: the auditor is right on both shifts
From RM2 Datasheet Figure 6 (PDF p.10): the bottom row's first pad is 2.75 mm from the left body edge, so seven pads at 1.5 mm pitch run −4.50 … +4.50 (symmetric); the file has −4.00 … +5.00 (+0.5 mm in x). The side columns start at the RF keep-out's lower boundary, 5.0 mm below the body top, so the first side-pad centre is y = −2.75; the file has −1.75 (+1.0 mm in y), which on a 1.5 mm pitch with 1.0 mm pads puts each pad half on its castellation. Pad lengths (file 2.5 mm; figure 2.0 side / 1.8 bottom, 0.5 mm outside the edge) should follow the figure. Proposed pads: side x = ±6.75, y = −2.75 + 1.5k, 2.0 × 1.0; bottom y = 7.85, x = −4.50 + 1.5k, 1.0 × 1.8; then the 1:1 print against a real module.

## Updated verdict for AUDIT-3
Two items in Part 2 were wrong and are corrected above: R15 must be fitted (otherwise no charging), and the reversed-cell-with-USB case is NOT protected by the rev 0.3 guard (a design change is needed; proposal above). The RM2 footprint needs its pad centres moved. Everything else in Parts 1–3 stands.

---

# Part 5: verification of rev 0.5 (`fb7f350`, schematic content hash 9c68738622b49c3834cf49c85408a97a0885fea2)
Read from the committed generator and footprint, 2026-10-04.

## Guard: VERIFIED as walked
`pcb/tools/gen_sch.py` at `fb7f350`: Q2 AO3401A {1 G: GUARD_G, 2 S: CELL_G, 3 D: CELL_P}; R45 100 kΩ BAT+ → GUARD_G; Q5 AO3400A {1 G: GUARD_C, 2 S: GND, 3 D: GUARD_G}; R46 10 kΩ CELL_P → GUARD_C; R47 47 kΩ GUARD_C → GND (fitted); R48 1 MΩ BAT+ → CELL_P; R22 0 Ω CELL_G → BAT+; Q3 AO3400A; R15 3.0 kΩ fitted with the datasheet reason. Every value is the one agreed in the walk (`pcb/team/…_three-confirmations.md` and the direct exchange). The eight states hold as argued there: correct cell USB off (body-diode bootstrap, Q5 from the cell), correct cell USB on (channel on, charge S→D), insertion with USB (no diode pre-conduction, charger regulation), reversed cell USB on (Q5 off at −3.4 V, Q2 gate = source, diode blocks; 34 µA through R46/R47 only), reversed cell USB off (all floating), no cell USB on (CELL_P ≈ 0.23 V via R48 against 57 kΩ, Q5 off, connector dead; hot leakage 10 µA × 57 kΩ = 0.57 V < 0.65 V), tripped pack (R48 applies the charger voltage at ~4 µA; PCM wake behaviour UNVERIFIED for the chosen cell), cell removed with USB (dead again). AO3400A V_GS(th) 0.65/1.05/1.45 V per the datasheet the designer logged.

## BATTERY.md: VERIFIED
Carries the ~110 µA standby drain with a cell fitted and the board off, and the charge-rate wording the auditor required: USB500's 500 mA is the total input, so a ≥ 1000 mAh cell gets ≤ 0.50 C with 1.8 kΩ; a 500 mAh cell with 3.6 kΩ is ISET-bound at 247 nominal, up to 271 mA (a hair over 0.5 C).

## RM2 footprint: bottom row and pad geometry VERIFIED; side-column y has a 0.5 mm open discrepancy
- Bottom pads 8–14: x = −4.50 … +4.50 at 1.5 mm, y = 7.85, 1.0 × 1.8 mm: matches the Figure 6 chain.
- Side pads: x = ±6.75, 2.0 × 1.0 mm: matches.
- Keep-out: a footprint rule area on F&B.Cu from y = −21.75 to **−3.25**, x = ±17.75 (35.5 × 18.5): matches the figure, bottom edge 5.0 mm below the body top.
- **Side-pad centres: committed y = −2.25 … +6.75; my chain gives −2.75 … +6.25.** The chain: keep-out bottom at −3.25 (the designer's own zone uses it), first pad's top edge flush with it (the designer's crop reading too), 1.0 mm pad → centre −2.75. The committed −2.25 puts the first pad's top 0.5 mm below the keep-out line and the last pad's bottom 1.0 mm above the body bottom (my chain: 1.5 mm, matching the figure's spacing to the bottom row). Unresolved; to settle by one measurement on the figure (body top edge to first side-pad top edge: 5.0 mm per the chain) and, finally, by the 1:1 print against a real module. Not a registration hazard of the earlier kind (the earlier error was 1.0 mm; this is 0.5 mm, a third of a pad pitch), but it should be exact.
- Courtyard +0.25 mm beyond the pads: present. Keep-out enforcement by the footprint rule area is unproven in DRC, as the designer says; a board-level rule area at layout is the safe duplicate.

## Verdict for AUDIT-3 at rev 0.5
The reversed-cell path with USB present is closed by the polarity sensor, with the tripped-pack wake path added; R15 is fitted; the charge-rate wording is correct. One 0.5 mm question on the RM2 side-pad y remains between the designer and me, with the measurement that settles it named above. Everything else from Parts 1–4 is resolved or carried in the open list (L2 ratings, DW01A/DS3231M datasheets, L1 orientation, module BL drive, coin-cell holder drawing, layout items, board current).

**Part 5 follow-up:** the RM2 side-pad y is resolved. The designer measured the figure (body top to first side-pad top 5.2 mm, bottom margin 1.34, pitch 1.52, pad 0.98 at a 42.7 px/mm raster), agreed the +0.5 mm was an error in the generator, and committed the footprint with side pads at y = −2.75 + 1.5k, x = ±6.75, 2.0 × 1.0 (pcb-design 76949f0; schematic hash unchanged 9c68738…). Verified from the committed pad lines. Nothing open between the designer and me on rev 0.5; the 1:1 print against a real RM2 remains the final arbiter.

---

# Part 6: the rev 0.5 guard self-latches; Part 5's "eight states hold" is withdrawn in part (2026-10-04, audit commit 5046e926f08d0f7cb3467aad80228bdcf325cbc3)
The auditor traced the ON state and is right; the concession with evidence is in `pcb/team/20261004-151654_from-expert_to-auditor_guard-latch-conceded.md`.
1. **Self-latch.** With USB present and a correct cell, Q2 and Q5 are on. Remove the cell: Q2's channel is symmetric, so CELL_P stays at BAT+ (the channel supplies R46 + R47's 74 µA), GUARD_C = 0.824 × 4.2 = 3.46 V, Q5 stays on, GUARD_G stays low. The socket stays live at 4.2 V until USB is removed. My Part 5 state "cell removed with USB: GUARD_C collapses, Q2 off" was wrong. A reversed reinsertion into the latched state starts with Q2 ON: the cell drags CELL_P and, through the channel, BAT+ negative while the charger current-limits; Q5 then releases and the latch breaks, but only after a transient of C22's 42 µC plus up to the charger's limit for the R45·C_gs ≈ 0.1 ms gate rise, with BAT+ below U5 BAT's −0.3 V absolute minimum (BQ2407x p.10) and U7's supply collapsed. Not sustained, but unqualified: the auditor's BLOCKER stands.
2. **R48 wake path: withdrawn.** Loaded by R46 + R47 = 57 kΩ, R48 = 1 MΩ puts 0.226 V on a tripped pack, not the charger voltage; no DW01-class PCM releases at that. A small enough R48 would latch the guard on with no cell instead. The wake goal and the dead-socket goal conflict in this topology.
3. **Q5 margin: not guaranteed.** The AO3400A's V_GS(th) minimum (0.65 V) is specified at 250 µA; holding Q2 off needs Q5 to sink only R45's 42 µA, which happens in subthreshold at a lower V_GS. "0.57 V < 0.65 V, therefore off" is not a proof.
4. **No resistor-level fix exists.** A two-wire socket gives no presence signal, and any symmetric-channel guard sensed on its own cell-side node latches. Options filed, for the designer and the owner (DECISION-NEEDED sent to the PM): **(A)** engineered protection: an ideal-diode controller for the discharge path (LM66100/TPS2121 class, reverse-blocking by construction) plus a charge-path P-FET enabled by the charger's CHG output; two parts, a redesign of the battery sheet, a fresh state walk. **(B)** no on-board reverse guard: the keyed JST-PH, the "+ red wire" silkscreen, one approved cell listing, the current-limited first plug-in; what the Pico W, Pico 2 W and the Pimoroni boards ship with. **(C)** keep rev 0.5 with a GND→BAT+ Schottky clamp for the transient and the latch documented; weakest. **My recommendation: (B) for spin 1, (A) only if the owner wants true protection and accepts the parts.**
5. Unchanged: R15 fitted, the gated divider (#2), the interrupt pull-up (#9), the RM2 footprint (resolved at −2.75 + 1.5k, 76949f0, supported by the auditor's own measurement), the charge-rate wording.

---

# Part 7: verification of the rev 0.6 battery sheet (2026-10-04, design commit `92f61d2`, schematic content hash 2ecde3da743110b36845f2ab9d73e33e5267dd44; docs-only commits to `d678afc` checked to change no net)

Read from `pcb/kicad/exports/netlist.xml` at that commit. Battery sheet as built: J3 1 = CELL_P → R22 0 Ω → **BAT+** (U5 BAT pins 2–3, C22 10 µF, TP7, R20 100 Ω → U7 DW01A VCC with C27 100 nF, Q4 source, R39); J3 2 = **BAT−** (U7 GND, Q1 FS8205A S1); Q1 common drain FET_D, S2 = GND; U7 OD → G1, OC → G2, CS via R21 1 kΩ from GND, TD open; J3 3 = TS → U5 TS with R12 10 kΩ to GND; ILIM R15 3.0 kΩ, ISET R14 1.8 kΩ, EN1 via R13 10 kΩ to VBUS, EN2 low; the divider Q3/Q4/R39/R23/R24/C28 unchanged from rev 0.5. **Q2, Q5, R45–R48 are gone; no other net differs from rev 0.5.** John's option B is implemented as described.

## State by state
| State | What happens | Verdict |
|---|---|---|
| **Correct cell, USB off** | Cell → R22 → BAT+ → U5 BAT→OUT (battery mode) → TPS63001. Return GND → Q1 S2→D→S1 → BAT−, both FETs driven on by the DW01A (VCC = Vcell via R20, 3 µA). Drop across Q1 ≈ 2 × 25 mΩ × 0.45 A ≈ 25 mV at the heaviest board draw (TPS63001 at 3.0 V in). DW01A protects over-discharge (~2.4 V), over-charge (~4.3 V), over-current (~150 mV across Q1, ≈ 3 A with 50 mΩ) and short circuit (DW01A figures from memory, datasheet not yet in `pcb/refs/parts/`). Divider: +3V3 present → Q3 on → Q4 on → GP28 = Vcell/2 | **Works** |
| **Correct cell, USB on** | USB500: input capped at 500 mA total (R15 fitted, EN1 high/EN2 low); fast charge K_ISET/1.8 kΩ = 443–494 mA (K_ISET 797–890, datasheet p.12), pre-charge 39–49 mA below V_LOWV 2.9–3.0 V, termination at ~10 % I_CHG, safety timer from R16 47 kΩ. Charge return through Q1 (charging direction, the DW01A's charger-detect threshold releases an over-discharge latch when a charger is seen). TS at 10 kΩ = "25 °C" always (owner-accepted residual, Part 2). Nothing new since Part 5 | **Works** |
| **No cell, USB on** (the state John is in while swapping if he ignores rule 0) | OUT follows IN; BAT+ node sits at V_BAT(REG) 4.2 V on C22 while the charger runs battery detection: I_BAT(DET) 5–10 mA pulled for t_DET 250 ms, then pre-charge current for t_DET, repeating (9.3.5.4). The DW01A floats between BAT+ and an undriven BAT−; Q1's body diodes are back to back, so BAT− floats somewhere between GND and 4.2 V. **J3 pin 1 is live at up to 4.2 V, pin 2 undefined**: harmless to the board, but this is why rule 0 (USB out before a swap) exists | **Works, socket live** |
| **Reversed cell, USB off** (CELL_P = cell −, BAT− = cell +) | DW01A: VCC at cell −, GND pin at cell +: reverse-biased by the full cell voltage (rated −0.3 V, from memory). R20 100 Ω limits the substrate-diode current to ≈ (Vcell − 0.6)/100 ≈ 30–36 mA: ~0.13 W in a 0402 (rated 0.063–0.1 W: R20 will likely cook and may open, which ends that current), ~20 mW in the DW01A. Its OD/OC outputs are undefined; the most likely outcome is FET1 off (gate ≈ its own source), and Q1's back-to-back body diodes then carry nothing, so GND and BAT+ are not connected to the cell. If the DW01A does turn Q1 on, the "USB on" row below applies with OUT unpowered. Q4's body diode (drain→source) pulls DIV_TOP toward BAT+ = −Vcell; R23 100 kΩ limits GP28 to ≈ −0.5 V at ~30 µA through its pad diode (RP2350 unpowered) | **Fails: DW01A over-stressed, R20 heated; charger probably survives; nothing bounds the DW01A's fate** |
| **Reversed cell, USB on** (the serious case) | At seating, C22 is at +4.2 V and the cell's − terminal lands on it; the cell's + terminal is BAT−. The DW01A is reverse-biased (its GND pin is now the most positive node) and drives Q1 unpredictably; FET1's body diode conducts cell + → FET_D regardless, and FET2 (gate referenced to the DW01A's GND pin, now ≈ Vcell above board GND) is very likely **on**. The loop then closes: cell + → Q1 → GND → U5 VSS/BAT substrate diode → BAT+ node → R22 → cell −. **BAT+ is pulled to ≈ −(Vcell − 0.6 V) ≈ −3.5 to −4.5 V against U5 BAT's −0.3 V rating.** C22 equalises from +4.2 V to that negative value through the loop impedance only (cell ESR + PCM FETs + Q1 + R22 + traces, ~0.2–0.3 Ω: a peak of tens of amps for microseconds, ~0.4 mJ, as the auditor said). Then a steady fault current flows **from the cell, not from USB**: its size is set by the cell's PCM (typically 2–4 A over-current trip in ~10 ms, short-circuit trip in microseconds for the common 1000 mAh pouch PCMs; the auditor is right that this is pack-specific and unqualified) and by what the BQ24074's BAT pin does as it fails (opens or shorts). The DW01A again sees −Vcell via R20 (~36 mA). Q4's body diode puts ≈ −0.5 V on GP28 at ~35 µA while the RP2350 is powered (IOVDD 3.3 V) | **Fails: BQ24074 BAT pin and DW01A both beyond ratings; the fault current is bounded only by the cell's protection board, never by USB500** |

**Correction to my own earlier wording (Parts 4–6) and to the designer's proposal file:** "current bounded by the charger's limit" is wrong for the reversed cell with USB on. The charger's input limit bounds what USB supplies; the destructive loop is cell → Q1 → GND → U5 substrate → BAT+ → cell, powered by the cell. USB500 is irrelevant to it. The auditor's statement stands in full.

## What the rev 0.6 sheet does and does not bound
- Bounded: every correct-polarity state, by the charger (USB500, ISET, timers), the DW01A/FS8205A and the cell's PCM in series; the no-cell state (nothing to damage).
- Not bounded by the board: a reversed cell. Two chips exceed their negative ratings the instant the plug seats, and the follow-on current is the cell's. The protection is the procedure in `pcb/BATTERY.md` (one approved listing with wire colours recorded, "+ RED WIRE" silkscreen, USB out before a swap, supervised first power-ups). This is the residual John accepted with option B, and the sheet states it; I confirm it is stated correctly.

## Fault containment, the PM's question: a series polyfuse (designer's option D)
Confirming and correcting `…_from-designer_to-pm_fault-containment-polyfuse.md`:
1. **Shorts: confirmed.** A PPTC in the positive lead (between J3 pin 1 and R22, keeping R22 as the ammeter link) is a second layer behind the cell's PCM against a shorted lead, a shorted Q1, a shorted board node: it limits the steady current to roughly its trip level within seconds (slow at 1–2× trip, ~0.1–0.3 s at 8 A for the Bourns MF-MSMF class) and resets when the fault clears. If the PCM works, the PCM trips first (its thresholds are lower-latency); the PPTC earns its place only for a cell whose PCM is missing or dead, which `BATTERY.md` forbids but cannot enforce.
2. **Reversed cell: partly wrong as written.** A fuse cannot prevent the damage (the voltage breach is immediate), so it does not save U5 or U7: the designer is right there. But "does nothing" is too strong: after the first milliseconds the fault current is the cell's through failed silicon and copper (row 5 above). A PPTC bounds **that** current and therefore bounds the heat in the board; with a dead or absent PCM, it is the only thing that does. Honest label: *"contains the fire, not the chips"*.
3. **Sizing.** Steady cell current: ≤ 0.50 A charging (USB500 cap) or ≈ 0.45 A discharging at a 3.0 V cell with the full backlight. The designer's 0.75 A hold / 1.5 A trip works at 25 °C but PPTC hold current derates ~30 % at 60 °C (a warm pocket next to the charger), landing near the board's own draw: nuisance trips possible. I would size **1.1 A hold / 2.2 A trip** (MF-MSMF110-2 class, 6 V, 1812; ~0.05–0.15 Ω cold): no nuisance trip, still below the lead and trace ratings and inside a typical PCM's 2–4 A trip band. Cost: ~0.3 USD and 25–75 mV at 0.5 A; the charger regulates at its BAT pin, so the cell sees up to ~75 mV less at the end of charge and terminates a few minutes later; no safety effect.
4. **The alternatives are not better.** A one-shot chip fuse is cheaper and faster but sacrificial (fine after a reversed-cell event, which needs U5/U7 replaced anyway; annoying after a nuisance trip). A series Schottky blocks charging: agreed, not available here. Note that R22 (0 Ω, 0603) already behaves as an unrated fuse at several amps; the PPTC makes that behaviour deliberate and resettable.
5. **What no part on this board can do:** keep U5 and U7 inside their ratings with a reversed two-wire plug while still charging through the same two wires. That was Part 6's conclusion and it is unchanged.

**Verdict on rev 0.6:** the sheet does what option B says, nothing else changed, the correct-polarity states hold with the same margins as Part 5, and the reversed-cell residual is stated correctly in the documents, with one correction to carry into them: the fault current in that case is the cell's, bounded by the pack's protection board (unqualified), not by USB500. Option D as resized above is worth offering John as "second layer against shorts and against a fire after a wiring mistake; it does not save the chips".

## Not verified
DW01A ratings and thresholds (datasheet not in `pcb/refs/parts/`; John to save it); the pack's PCM trip figures (no cell chosen); PPTC figures from the Bourns MF-MSMF family data as I remember them, to be read from the datasheet if option D is taken.

---

# Part 8: verification of rev 0.7, F1 polyfuse (2026-10-04, design commit `7765383`, schematic content hash 1abae791d6e39b4e3c84039a20fcecd3686cf349; docs-only commit `a534d7d` after it)

Checked by a semantic diff of `netlist.xml` between `92f61d2` (rev 0.6) and `7765383`: **exactly two changes.** F1 `MF-MSMF110/16X-2` (Fuse_1812_4532Metric) inserted: net CELL_P is now J3 pin 1 + F1 pin 1, new net CELL_F is F1 pin 2 + R22 pin 1; R20 100 Ω moves from 0402 to 0603. Component count 131 → 132. No other net or value differs. "Nothing else changed" is confirmed.

## Placement
In the cell's positive lead only, ahead of the R22 ammeter link, so charge and discharge currents both pass through it and the USB → OUT path does not. The DW01A senses current on the negative lead (CS), unaffected. The gated divider taps BAT+, downstream of F1, so the battery reading on GP28 is the charger-side node: low by I·R_F1 while discharging (≤ 0.45 A × 0.20 Ω = 90 mV worst case, ~2 % of the reading), high by the same while charging. A gauge error, not a safety item; a cold F1 is 0.06–0.20 Ω per the designer's datasheet figures.

## Charge termination
The BQ24074 regulates its own BAT pin at V_BAT(REG) (4.16–4.24 V, datasheet p.12). The cell sits lower by I × (R_F1 + R22 + wiring): at the start of the constant-voltage phase, ≈ 0.49 A × 0.2 Ω ≈ 100 mV worst case; by termination (I_TERM ≈ 10 % of 494 mA ≈ 49 mA) the drop is ≈ 10 mV. Effect: the constant-voltage phase runs a few minutes longer and the cell terminates within ~10 mV of where it would without F1; the cell never sees more than the regulation voltage; the DW01A's over-charge threshold (~4.3 V, from memory) is untouched. The safety timer (R16 47 kΩ, ≈ 8 h at K_TMR 36–48) is far from the extra minutes. **No safety effect, as predicted in Part 7.**

## Derated hold vs the board's draw
| Current through F1 | Value | Against hold |
|---|---|---|
| Charging (USB present; the board's load comes from USB via the power path, the cell only receives charge) | ≤ 0.50 A (USB500 total cap) | 1.10 A at 25 °C, 0.77 A at 60 °C: margin ≥ 0.27 A |
| Discharging, worst case: 300 mA at 3.3 V, TPS63001 ~85 % at a 3.0 V cell, plus charger quiescent and a card-write burst | ≈ 0.40–0.45 A | margin ≥ 0.32 A at 60 °C |
| Both at once | not possible: the cell is either being charged or supplying OUT, not both | |
No nuisance trip up to 60 °C; at 85 °C the family's derating (~0.6 A) still clears 0.45 A. The 16 V rating and 100 A interrupt figure are far from a 4.2 V cell.

## What F1 does in the faults
- Shorted lead, shorted Q1, shorted board node, PCM working: the PCM trips first (2–4 A typical, ms). F1 sees the same current for those milliseconds and does not reach trip; it is the second layer only.
- Same faults with the PCM absent or dead: the cell's short-circuit current (tens of amps for a 1000 mAh pouch) trips F1 in well under 0.3 s (8 A → 0.3 s per the datasheet figure); at a 2–4 A fault it trips in seconds. Once tripped it stays high-resistance while voltage remains across it, passing ~0.1–0.2 A and sitting hot (~0.5–0.8 W is typical for the family); **the cell must be unplugged to reset it**. `BATTERY.md` should say so in a line.
- Reversed cell with USB: the microsecond C22 equalisation passes untouched (a PPTC is thermal, far too slow), U5's BAT pin and the DW01A are over-stressed as in Part 7, and the follow-on current from the cell through failed silicon is what F1 bounds, after the PCM if the PCM works. The documents' wording "does not save the DW01A or U5's BAT pin" is correct.

## R20 at 0603
36 mA × 100 Ω = 0.13 W against a standard 0603's 0.1 W: better than the 0402 (0.063 W) but still 30 % over rating for as long as a reversed cell sits there with USB absent; it survives seconds to minutes, not an afternoon. Two cheap ways to get inside the rating, either acceptable: an 0805 (0.125 W, nearly there) or **330 Ω** in the same 0603 (11 mA, 40 mW; 100 Ω–1 kΩ is the usual range for the DW01A's VCC filter, to be confirmed against the DW01A datasheet when John saves it). Not a blocker: R20 opening is itself a benign end to that fault current.

**Verdict on rev 0.7:** F1 is in the right place, the right size, and the only change besides R20's footprint; the correct-polarity states of Part 7 hold with a ≤ 100 mV shift at the start of constant-voltage charging and a ~2 % gauge offset; the fault behaviour matches the words John was given. Two notes for the documents: a tripped F1 stays hot until the cell is unplugged; R20 is still marginal at 0603, 330 Ω or 0805 would end that.

## Not verified
F1's datasheet itself (figures as the designer quoted them); DW01A datasheet (still to be saved); PCM figures (no cell chosen).

## Part 8 addendum: the hold-margin claim withdrawn pending a measured load (2026-10-04, after the auditor's `…160129` answer)
The auditor is right that "no nuisance trips" rested on an unmeasured 0.40–0.45 A. The 3.3 V rail's draw with every consumer on at once, from the sources in `pcb/refs/`:
| Consumer | Peak at 3.3 V | Source |
|---|---|---|
| RM2 transmit, MCS7 at 16 dBm | 271 mA | rm2-datasheet, features list |
| PAM8302A at full output (0.7–0.8 W into 8 Ω at 10 % THD, ~85 % efficient) | ≈ 250 mA | pam8302a p.4 (P_O at 3.6 V); the division is mine |
| RP2350 at 150 MHz with PSRAM and flash active | ≈ 50–80 mA | general practice, unmeasured |
| LCD module backlight at 100 % | ≈ 40–60 mA | unmeasured (the module's drive is still an open item) |
| microSD write burst | 100–200 mA | general practice, card-dependent |
| **Sum of peaks** | **≈ 0.7–0.85 A** at 3.3 V → **≈ 0.9–1.05 A from a 3.0 V cell** at 88 % | the TPS63001 switch limit is 1.6–2.0 A (tps63001 p.5), so the regulator does not cap this |
Against F1 at 1.10 A (25 °C) / 0.77 A (60 °C) hold, the all-at-once case sits in the hold-to-trip band; a PPTC there does not trip quickly, but whether it trips at all depends on how long the firmware keeps Wi-Fi transmit, full-volume audio and a card write going together. Nothing in the project's software does that today (no radio, no audio, no card use yet), so the bound is genuinely open. Three honest ways out, for the designer and John: (a) keep 1.1 A and measure on the first board before committing to the value (same 1812 footprint for every hold rating in the family); (b) fit 1.5 A hold / 3.0 A trip (MF-MSMF150/16X-2 class) and accept that the second layer trips at 3 A instead of 2.2 A, still far below a cell short and still inside what the DW01A (~3 A) and the JST-PH contacts (2 A continuous, jst-ph p.1) tolerate for the seconds to trip; (c) a firmware rule against Wi-Fi transmit during audio. My preference: (b), because a tripped PPTC that stays hot in a pocket is a worse outcome than containment at 3 A, and the PCM remains the first layer either way. Also conceded: "a 0603 is 0.1 W" is the common thick-film rating, not a universal one; the BOM should state the chosen R20 part's rating. Q4's body diode is a possible negative path to GP28, not a clamp I can certify. F1's trip curve and the DW01A's clamp current remain unsourced until their datasheets are in `pcb/refs/parts/`.

---

# Part 9: the DW01A and Bourns MF-MSMF datasheets read; every "from memory" figure replaced (2026-10-04, design commit `1252e0b`, rev 0.7)

Sources now in `pcb/refs/parts/`: `Datasheet-DW01A.pdf` (Pingjing Semi, "DW01A One Cell Lithium-ion/Polymer Battery Protection IC", revision 3.0, June 2023, 7 pages; saved by John) and `bourns-mf-msmf.pdf` ("MF-MSMF Series PTC Resettable Fuses", 16 pages; saved by the designer on John's approval).

## DW01A, what the datasheet says against the board
| Item | Datasheet | Board (rev 0.7) | Verdict |
|---|---|---|---|
| VCC absolute maximum | **−0.3 to 6 V** (p.4) | reversed cell puts −Vcell across VCC–GND | breach confirmed, as Parts 7–8 said |
| CS absolute maximum | VCC − 15 V to VCC + 0.3 V (p.4) | CS via R21 1 kΩ from GND | normal states inside |
| Reverse clamp current | **not specified** anywhere in the datasheet | — | the auditor's point stands: nothing qualifies the DW01A's behaviour under reversed supply; the only bound is the external resistor |
| **R1, the VCC series resistor** | **470 Ω typical, 470–1500 Ω allowed, "cannot be omitted, and R1 must be greater than or equal to 470 ohms"** (p.6, typical application circuit and note 1) | **R20 = 100 Ω** | **OUT OF THE DATASHEET'S RANGE. New finding.** R20 must become 470 Ω–1.5 kΩ. The 330 Ω floated earlier (by me and the designer) is also below the minimum |
| R2, the CS resistor | 2 kΩ typical, 1–3 kΩ (p.6) | R21 = 1 kΩ | inside, at the low edge; 2 kΩ would match the typical circuit |
| C1 on VCC | ≥ 0.1 µF (p.6) | C27 100 nF | matches |
| Over-charge protect / release | 4.28 V ±50 mV / 4.08 V (p.1, p.5) | cell charged to 4.16–4.24 V by the BQ24074 | the DW01A never trips on a normal charge; margin ≥ 40 mV worst case |
| Over-discharge protect / release | 2.40 V ±100 mV / 3.00 V (p.1) | TPS63001 runs to 1.8 V in, so the DW01A is what stops the cell at 2.3–2.5 V | fine; this is its job |
| Discharge over-current | 160 mV ±20 mV across the FETs, 10 ms (p.1, p.5) | FS8205A 2 × 21–25 mΩ at Vgs 4.5 V (fs8205a p.3) → **3.2–3.8 A** (2.8–3.3 A at the 35 mΩ, Vgs 2.5 V figure) | the "~3 A" I used from memory was right in band |
| Load short circuit | 1.0 V ±0.3 V across the FETs, 300 µs typ / 600 µs max (p.5) | ≈ 20 A with 50 mΩ | fine |
| Charge over-current | −150 mV, 10 ms (p.1, p.5) | ≈ 3 A charging | far above 0.5 A |
| Supply current | 1.5 µA typ, 5 µA max (p.5) | | negligible against the cell |
| 0 V-battery charge function | present (p.6 §5) | | a cell whose PCM has opened can be woken by this board's charger if the pack's own protector allows it; `BATTERY.md`'s "may not wake" line stays, since the pack's PCM is the unknown |

**Consequence of the R1 finding for the reversed-cell fault:** with R20 at the minimum 470 Ω the reverse current through the DW01A's VCC pin is ≈ (4.2 − 0.6)/470 ≈ **7.7 mA**, 28 mW in the resistor: inside a 0603's 0.1 W with 3× margin, so the "R20 may open" story and the 0805 question both go away, and the DW01A's stress falls fivefold. Why the datasheet wants ≥ 470 Ω: the resistor and C1 filter the VCC pin against the voltage spikes on the cell when the FETs switch under over-current, and limit the current into the pin when the cell is reverse-connected or the charger overshoots; 100 Ω defeats the second purpose. Recommended value: **1 kΩ** (inside 470–1500 Ω, reverse current ≈ 3.6 mA, 13 mW; the 1.5 µA supply drop across it is 1.5 mV, irrelevant to the thresholds). Also, since "DW01A" is a multi-vendor part name: the BOM should state the vendor whose datasheet this is (Pingjing) or verify the chosen vendor's R1 range, because the thresholds and the R1 rule may differ by vendor.

## Bourns MF-MSMF, what the datasheet says
| Model | Vmax | Imax | Ihold 23 °C | Itrip 23 °C | R min / R1 max (Ω) | Max time to trip at 8 A | Ihold at 40 / 50 / 60 / 70 / 85 °C |
|---|---|---|---|---|---|---|---|
| MF-MSMF110/16X (fitted at `1252e0b`) | 16 V | 100 A | 1.10 A | 2.20 A | 0.06 / 0.20 | 0.3 s | see the first derating table (p.11, row MF-MSMF110/16X; the designer quoted 0.77 A at 60 °C from it) |
| MF-MSMF150/16X (proposed) | 16 V | 100 A | 1.50 A | 3.00 A | 0.030 / 0.120 | 0.5 s | **1.25 / 1.08 / 1.00 / 0.78 / 0.64 A** (p.12) |
Both from the electrical characteristics table (p.2–4) and the thermal derating tables (p.11–12). "R1 max" is the resistance one hour after a trip, so the in-circuit drop after a nuisance trip is up to 0.12 Ω × 0.5 A = 60 mV for the 150. Against the sourced all-on load of 0.9–1.05 A from the cell (Part 8 addendum): the 150 holds it at 60 °C (1.00 A) only just, at 70 °C (0.78 A) it does not; the 110 does not hold it from 50 °C up. So (b) widens the margin but does not make the all-on case trip-proof in a hot pocket; what does is that no firmware today runs Wi-Fi transmit, loud audio and a card write together, and the first board's measurement. The trip curve (p.6–7, time-to-trip vs fault current at 23 °C) confirms the family trips in roughly a second at 3× hold and in well under a second at 8 A; it is not instantaneous at 1.2× hold, which is the point of a PPTC.

**Verdict:** one new finding, **R20 100 Ω is below the DW01A datasheet's 470 Ω minimum**; change to 1 kΩ (470 Ω–1.5 kΩ allowed), and name the DW01A vendor in the BOM. The fuse choice between 110 and 150 stands as Part 8 addendum described it, now with the datasheet's own derating numbers: 150 preferred. Everything I had quoted from memory for the DW01A is now sourced; two numbers were refined (over-current 160 mV not 150; short 1.0 V not 1.35 V), neither changes a conclusion.

## Part 9 addendum: rev 0.8 verified (design commit `283594a`, schematic content hash 9ed7c374ca34e7dad227afbdf19a4a0bbdb7435d)
The designer found the same R1 rule in the DW01A datasheet independently and committed rev 0.8 before Part 9 was filed. Semantic netlist diff `1252e0b` → `283594a`: **exactly two value changes, no net change**: R20 100 Ω 0603 → **470 Ω 0402**, R21 1 kΩ → **2 kΩ** (the datasheet's typical values, p.6). ERC 0 errors, 2 expected warnings. At 470 Ω the reversed-cell current into the DW01A is ≈ 7.7 mA, 28 mW, inside a 0402's 0.063 W with 2× margin, so the footprint step down is justified and the "R20 may open" story is closed. I had suggested 1 kΩ; 470 Ω is the datasheet's typical and equally correct. The CS resistor at 2 kΩ with the DW01A's CS leakage (sub-µA) shifts no threshold. **Rev 0.8 verified; Parts 7–9 apply to it.** Still open from Part 9: name the DW01A vendor in the BOM.

## Part 9, second addendum: rev 0.9 verified (design commit `eafbde6`, schematic content hash 304da84e427746d2779c4b5a228b10f730f74106)
John's rulings (2-pin socket, 1.5 A fuse) as built. Semantic netlist diff `283594a` → `eafbde6`: **exactly two component changes and one net change, nothing else**: J3 `S3B-PH-SM4-TB` 1x03 → `S2B-PH-SM4-TB` 1x02 with the value text "1 = + RED WIRE, 2 = −"; F1 `MF-MSMF110/16X-2` → `MF-MSMF150/16X-2`, same 1812 footprint; net TS loses its J3 pin 3 node and is now U5.TS + R12 only (the fixed 10 kΩ "25 °C" resistor stays, which is the right treatment: the BQ24074's TS pin must see a resistance, never float). 132 components both sides; ERC 0 errors, 2 expected warnings. R16 47 kΩ unchanged pending the timer question. Part 9's derating table applies to the fitted fuse (Ihold 1.50 A at 23 °C, 1.00 A at 60 °C, Itrip 3.00 A, R1max 0.12 Ω). **Rev 0.9 verified; Parts 7–9 apply to it.** No open hardware item on the battery sheet beyond the DW01A vendor name in the BOM and the pack's PCM figures (the chosen 2000 mAh JLJLUP cell's listing, if it states them).
