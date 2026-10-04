# HR-P01: Review of DR-033 appendix H and requirements §11a, microSD slot and the Stage 2 pin plan

- **Verdict: fits, with the trades and cautions below.** The pin plan is consistent with the RP2040/RP2350 GPIO function table as I know it; the card belongs on its own SPI0 bus; the throughput claim is an upper bound I cannot measure here.
- Reviewer: microcontroller expert, 2026-10-04. Desk review. **No SD module or card is on my desk**, so nothing about SD throughput is measured; the pin functions below are from the RP2040 datasheet's GPIO function table (section 2.19.2), which the RP2350A keeps for GP0–29 per its datasheet; confirm in the RP2350 table before freezing.

## 1. Pin plan
| Line | Chosen | Function-table check |
|---|---|---|
| microSD MISO | **GP4** = SPI0 RX | Correct. SPI0 RX exists on GP0, GP4, GP16, GP20; GP0 is PSRAM CS, GP16 and GP20 are joystick left/right, so GP4 is indeed the only one left |
| microSD SCK | **GP6** = SPI0 SCK | Correct (SPI0 SCK: GP2, 6, 18, 22) |
| microSD MOSI | **GP7** = SPI0 TX | Correct (SPI0 TX: GP3, 7, 19, 23) |
| microSD CS | **GP5** = SPI0 CSn | Correct, and `sdcard.py` drives CS as a plain GPIO anyway, so any pin would do |
| Card detect | GP14 | Plain input, fine. Give it the internal pull-up and read it before mounting; a card insertion is the one event `os.VfsFat` cannot survive un-told |
| Fuel gauge I2C1 | **GP26 SDA / GP27 SCL** | Correct (I2C1 SDA: GP2, 6, 10, 14, 18, 22, 26; SCL: GP3, 7, 11, 15, 19, 23, 27). Note GP26/27 are also ADC0/ADC1; using them for I2C leaves ADC2 (GP28) and ADC3 (GP29, the radio's) as the only analog inputs, which is what the plan does |
| Battery divider | GP28 = ADC2 | Fine |
| Speaker PWM | GP22 | Fine; every GPIO has a PWM slice. GP22 shares slice 3A with GP6 (SD SCK is not PWM, no conflict) |
| Spare | GP1 | Fine as the one spare; it is also UART0 TX, so a one-wire debug print is still possible (TX only) if ever wanted |

Consequences I agree with: no I2S (three pins), no two-wire debug UART; PWM audio. **What I would trade:** nothing on the verified pins. One optional swap: if the fuel gauge turns out unwanted on spin 1 (the ADC divider does the job), GP26/27 become free again and I2S or a full UART returns; design the footprint so the gauge is optional, as the DR already says.

## 2. Sharing SPI1 with the screen: no, agreed
- SPI1 RX is on GP8, GP12, GP24, GP28: LCD DC, LCD RST, the RM2 data line, the battery ADC. No free RX, so the card cannot even be wired to SPI1 without moving a verified pin.
- Even with a pin, `sdcard.py` initialises at 100–400 kHz and then sets its own baud, and the screen holds the bus at 62.5 MHz for 18 ms per frame; a shared bus means re-initialising the SPI object around every card access and blocking frames during reads. A separate SPI0 bus costs three pins and removes all of that. Right call.

## 3. Electrical
- 10 kΩ pull-ups on CS, MOSI, MISO and the unused DAT1/DAT2: standard and correct (the SD spec wants the card's DAT lines held high in SPI mode).
- 10 µF + 0.1 µF at the slot: correct; put the 10 µF close, the card's write bursts are what it is for.
- **Current:** card write bursts of 100–200 mA for tens of ms are real; add them to the ~100 mA I estimate for the board (still unmeasured, `hwtest/load_hold.py`) and size the buck-boost for ≥ 500 mA continuous with headroom; the MP28164 (2 A) or a TPS63001 (1.2 A) both have it. The 10 µF at the slot plus the regulator's output capacitance carries the burst.
- ESD array on the exposed lines and a push-push SMD slot: agreed.
- 3.3 V card supply direct from the 3.3 V rail is fine; a switched supply (a GPIO-controlled load switch) would let the game power the card down between uses and protect the file system from a weak battery, worth a footprint.

## 4. Software and throughput
- Correct: MicroPython's rp2 port has no `machine.SDCard`; it is `sdcard.py` (micropython-lib) over `machine.SPI` plus `os.VfsFat`. The driver reads 512-byte blocks with Python-level framing around `spi.readinto`, so throughput is bounded by the SPI clock and the per-block Python overhead.
- **My bound, not a measurement:** at a 20–25 MHz SPI0 clock the wire alone is ~2.5–3 MB/s, and the per-block Python overhead in `sdcard.py` typically brings an RP2040 to a few hundred KB/s for large sequential reads. So "a few hundred KB/s" is the right order of magnitude; against the internal flash's measured 4.4–5.6 MB/s the card is **about ten times slower**. A 115 KB background would take ~300 ms from the card against 21 ms from flash; a 237 KB card sheet ~0.5–1 s.
- **What that means for the game:** the card is **storage, not a streaming source**. Scenes cannot stream backgrounds or sprites from it per frame or per key. It can hold the full asset library, saves and logs, with assets copied to internal flash (or a sheet loaded once per scene into RAM only if RAM allows, which on the RP2040 it does not and on the RP2350 with PSRAM it might). Mounting at boot costs about a second; mount lazily.
- I will measure this the first time an SD module and a card are on the desk; the RP2040-Plus has the pins (SPI0 on GP4–7 is free today) and `sdcard.py` would run unchanged. Not urgent, as the PCB maker says.

## What I could not verify
SD throughput (no module); the RP2350 GPIO function table itself (worked from the RP2040 table, which the RP2350A documents as identical for GP0–29); the current draw of today's board.
