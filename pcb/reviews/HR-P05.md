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
