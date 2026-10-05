# Battery: what to buy and how to be safe (spin 1)

Written for John, 2026-10-04. The decisions behind it are in `pm/inbox/PCB-001-battery-and-power-path.md` and the audit response in `pcb/reviews/AUDIT-2-RESPONSE.md`.

## The fuse
The board has a self-resetting fuse in the battery lead (1.5 A hold, 3 A trip, your decision). It can limit the heat from a short on the board side of the fuse. It does not protect against a short in the battery's own leads before they reach the board, and it does not save the two chips a reversed battery destroys: the polarity check below is still the protection. In normal use it drops 15 to 60 mV at 0.5 A (Bourns datasheet p.2), which lengthens a charge slightly. A tripped fuse is not fully open: it stays hot and keeps passing a small current while the battery is connected. **Unplug USB and the battery**, let it cool, and find the fault before reconnecting; how long it takes to reset is not guaranteed. Near 60 °C its hold rating falls to 1.0 A (Bourns p.10), so it is sized for room-temperature prototype use, not a hot enclosure (AUDIT-3 #24, #26).

## Approved test battery (John, 2026-10-04)
**JLJLUP 3.7 V 2000 mAh LiPo, 2-pack (Amazon listing B0FH7G1WPG):** 34 x 10 x 52 mm, 34 g, integrated protection circuit, JST-PH 2.0 mm two-wire plug, rated 1 C discharge (about 2 A). Fits the standard-cell specification below except thickness (10 mm instead of 5 to 6), which is fine for the spin 1 dev board; the enclosure question comes with spin 2.
- The board is programmed for about 494 mA charge (nominal; the 500 mA USB budget and the board's own draw can make it less), which is about 0.25 C for this cell. A low rate is not a temperature guarantee: the board cannot sense the cell's temperature, so charge it at room temperature, on a non-flammable surface, and supervise the first charges (AUDIT-3 #5, #6). A full charge from empty takes about 4.5 to 5 hours (longer when the board is also drawing from the same 500 mA USB budget), inside the safety timer: rev 0.10 sets the timer resistor R16 to 68 k, which allows 6.8 to 11.3 hours (6.7 to 11.4 h with the resistor's 1 % tolerance; BQ24074 datasheet p.13, p.27). That leaves margin, but whether a full charge of this pack actually finishes is **measured at bring-up**, not assumed (AUDIT-3 #19). The timer does not change the charge speed. The timer slows in proportion while the charger is limiting current because the board is also drawing from USB (p.28). A cell drained very flat (below about 3.0 V) first gets a slow pre-charge limited to about 41 to 68 minutes. **If the charge LED flashes about twice a second, the timer has run out: that is a fault.** Unplug USB and the battery and ask the expert to look at it; do not keep re-plugging USB to force more charge.
- Discharge: the listing claims 1 C (2 A) but also says about 1.5 A maximum operating current, so treat **1.5 A** as the ceiling (AUDIT-3 #27). The board's estimated worst all-on draw is about 1 A from a nearly empty cell; that is an estimate, measured at bring-up.
- **The listing itself warns that the plug's polarity is not universal.** Before the first plug-in of each cell: hold the plug against the socket and check that the red wire sits at the + mark.

## The standard test cell specification (any seller)
Any cell that matches all of this is approved for the first boards:
- single-cell 3.7 V lithium-polymer pouch, **1000 to 1200 mAh**;
- **with its own protection board** (the listing says "protected", "with PCM" or "with protection circuit");
- **JST-PH 2.0 mm two-wire plug**;
- size **503450** (5 x 34 x 50 mm) or **603048** (6 x 30 x 48 mm).

Because sellers wire the plug both ways, the rule stands for **every new cell, every time**: hold the plug against the socket and check that the red wire sits at the **+** mark before plugging in. That check is the protection; there is no electronic guard.

## What to buy
- A single **LiPo pouch cell, 3.7 V, 1000 to 1200 mAh, WITH a protection board** (the listing says "protected", "with PCM" or "with protection circuit"). Sizes that fit a flat credit-card board: 503450 (5 x 34 x 50 mm) or 603048 (6 x 30 x 48 mm).
- With a **JST-PH 2.0 mm plug** (two wires, red and black). This is the plug most hobby cells come with.
- Rated for at least 0.5 C charging (1000 mAh cell: 500 mA). Nearly all pouch cells are; the cell's own listing is the authority.
- A battery whose own protection has tripped (it shows 0 V) may not wake on this board; charge it briefly on an ordinary single-cell charger first, then use it here.
- Cells with a third thermistor wire cannot be used on this board (the socket has two pins); a later spin may add that.

## Before plugging in, every time
0. **Unplug USB first.** With USB plugged in the socket's + pin is live at about 4.2 V from the charger even with no battery in it. So: USB out, swap the battery, USB back in.
1. Look at the board's marks beside the socket: **+ RED** at pin 1, **- BLK** at pin 2. Hold the plug the way it will go in and check that the red wire lines up with **+**. Then, with the plug unconnected, **put a meter on the plug's two metal contacts**: the contact that will land on **+** must read positive (about 3.7 V). Colours and keying are not enough on their own: a plug can be crimped backwards (AUDIT-3 #28). Cells from different sellers are wired both ways. **There is no electronic guard on this board** (decided after the audit: none can be made safe with a two-wire plug). A reversed cell puts a wrong-way voltage on the protection chip and the charger the instant the plug seats, and with USB connected the cell then drives current through the damaged chips, limited only by the cell's own protection board (the charger's limit does not apply in that loop). This check, and a protected cell from the approved listing, are the protection. Buy from the one approved listing below, which has its wire colours recorded.
2. Make sure the cell is not swollen, dented or warm.

## First power-ups
The step-by-step plan, with what to read and when to stop, is `pcb/BRINGUP.md`. In short: USB only first, then a current-limited bench supply in place of the battery, and only then a real battery, always supervised.
