# Questions for the owner (first PCB)

Answer these one at a time, in order. The first two matter most: they decide how hard everything after is. There are no wrong answers, only trade-offs. Costs are rough estimates from `pcb/PLAN.md`. Confirm every price on the fab's quote page before ordering. Nothing here is decided until you answer and the PM records it.

Not sure of a word? See "Words you will hear" at the bottom.

---

## Question 1: What goes on the board? (scope and screen together)

Think of the board as a sandwich. Today you have two layers: the Waveshare RP2040-Plus (the brain, USB, flash memory) and the Waveshare screen HAT (screen, joystick, buttons). What do you want your own board to be?

**Option A: Brain board only, plus a header for your existing screen HAT.**
You design the RP2040, flash memory, USB-C, power and a connector. The Waveshare HAT plugs onto it, exactly like now.
- Cost: lowest. Small board.
- Difficulty: easiest. The screen, joystick and buttons are already proven, so the game should work with no code change.
- Risk: lowest. The main risk is that the connector does not line up with the HAT. Fix: print the footprint on paper at 1:1 and hold the HAT against it.

**Option B: One board with the brain, the joystick, the four buttons and a header or connector for the screen module.**
Joystick and buttons are on your board; only the screen is a separate module.
- Cost: low to medium.
- Difficulty: medium. You choose and place the buttons and joystick, and the board outline has to suit the module.
- Risk: medium. Wrong button footprints or heights are a common first-board mistake.

**Option C: Everything on one board, with a bare screen panel on a small connector.**
A real handheld: one board, nothing stacked.
- Cost: medium to high.
- Difficulty: hard. The bare panel has its own connector, backlight circuit and startup values. The panel's exact part number is not yet known to us.
- Risk: highest. If the panel does not start, the board is hard to debug.

**My recommendation: Option A for the first board.**
Reason: it keeps the proven screen and input unchanged, so any problem is in the part you are learning (the brain board). You can always do Option C on a second board once the first works. Plan for a second spin anyway: most first boards need one fix.

Also note: your final answer depends on a fact I could not read yet (the HAT and board outlines, in the PDFs). I can confirm this recommendation once I can read them.

**Update, 2026-10-04 (after reading the PDFs):** the two PDFs are Waveshare's product pages, not schematics. They give the brain board's size (21 x 51 mm, Pico pinout) but nothing about the HAT's outline, so Option B's main unknowns (button and joystick parts, screen position) are still open. Because you said you want "the screen, joystick and buttons" on your board, the parked decision request `pm/inbox/DR-033-board-scope.md` recommends **Option B with the screen as a plug-in module** and names Option A as the safe fallback. Either is defensible; the PM will take it to you when Stage 2 opens.

---

## Question 2: Battery or no battery?

A battery lets the board run without a cable. It also adds a charger chip and protection circuit.

**Option A: No battery. USB power only.**
- Cost: lowest.
- Difficulty: easiest.
- Risk: lowest. A mistake costs a board, not a fire.

**Option B: Add a connector for a ready-made battery with its own protection, and a simple charger.**
- Cost: low to medium (a charger chip, a connector, the battery).
- Difficulty: medium.
- Risk: medium. A wrong charger or missing protection on a lithium cell can start a fire. The role file requires a proven charger design, a second opinion from the expert, and a first test with a current-limited power supply.

**Option C: Full battery system on the board (charging, protection, battery gauge, power switch).**
- Cost: highest.
- Difficulty: hard.
- Risk: highest.

**My recommendation: Option A for the first board.**
Reason: you are learning the whole process at once. A battery is the one part that can be dangerous. Put a clearly marked place for it on the second board. (The Waveshare board has a battery connector today. I have not been able to read how it is built.)

---

## Question 3: Do you want the factory to solder the small parts, or will you solder?

The RP2040 chip is tiny, square, with no legs you can see. It is very hard to solder by hand.

**Option A: Factory assembles everything possible ("assembled boards").**
- Cost: highest (about 30 to 150 USD or more for a small run, estimate).
- Difficulty: easiest for you. You choose parts the factory has in stock.
- Risk: parts can be out of stock, or a footprint can be wrong and you only see it when the boards arrive.

**Option B: Factory assembles the hard small parts. You solder the rest (connectors, buttons).**
- Cost: medium.
- Difficulty: medium.
- Risk: medium. Needs a soldering iron and some practice.

**Option C: You solder everything.**
- Cost: lowest board cost (about 5 to 30 USD for bare boards, estimate), plus tools.
- Difficulty: hard. Needs hot air or a good iron and steady hands for the RP2040 chip.
- Risk: highest. You could waste boards.

**My recommendation: Option A or B.** Pick B if you already own a soldering iron; otherwise A.
Reason: a first board that works matters more than saving money. Hand-soldering the RP2040 is the most common way first boards fail.

---

## Question 4: Shape and size of the board

**Option A: Same size as the screen HAT. The board is the whole handheld, with the screen on top.**
- Cost: low.
- Difficulty: medium.
- Risk: medium. Everything has to fit.

**Option B: A board that plugs under the existing HAT, like the Waveshare board does today.**
- Cost: low.
- Difficulty: easiest, if the connector matches. The HAT outline decides.
- Risk: low.

**Option C: A new custom shape (for a case).**
- Cost: medium.
- Difficulty: hard. Needs mechanical drawings.
- Risk: high.

**My recommendation: Option B** if you chose Question 1 Option A. It is a direct consequence. If you chose Option B or C in Question 1, I will ask this again, because the answer changes.

---

## Question 5: Budget and waiting time

What is the most you will spend on the first order, and how long can you wait?

**Option A: Under about 50 USD, slow shipping (about 2 to 3 weeks).**
- Only bare boards, or a very small assembled run. You may not afford a fix run.

**Option B: About 50 to 150 USD, normal shipping (about 1 to 2 weeks).**
- Assembled boards, possibly a second small run for fixes.

**Option C: More than about 150 USD, fast shipping.**
- Several runs or a bigger test batch.

**My recommendation: Option B.**
Reason: plan for one fix run. These figures are estimates from `pcb/PLAN.md`; the real quote can differ.

---

## Question 6: Will you share your board design publicly?

Your repo is already public. Do you want the board files public too?

**Option A: Yes, as open hardware under a recognised open licence.**
- No cost. Easy. Lets others learn from it and spot mistakes.
- Risk: none for you, but anything you publish must not include Waveshare's own drawings or layout. I will design an original board.

**Option B: Publish the game only. Keep the board files private.**
- No cost. Easy.

**Option C: Decide later.**
- No cost. Easy.

**My recommendation: Option C for now**, and decide before ordering. Reason: no rush, and we only need the choice before the files go anywhere. Note: a licence choice is yours to make and not something I can pick for you.

---

## Words you will hear

- **ERC (electrical rules check):** KiCad checks your drawn circuit for mistakes like a pin left unconnected.
- **DRC (design rules check):** KiCad checks your board layout against the factory's limits, like traces too close together.
- **Gerber:** The set of files the factory reads to make your board, one per layer.
- **BOM (bill of materials):** The shopping list of every part on the board.
- **Pick-and-place:** The file that tells the factory's machine where to put each part.
- **Footprint:** The shape of a part's pads on the board, which must match the real part.
- **Schematic:** The circuit drawing that shows how parts connect, without caring where they sit.
- **Layer:** One thin sheet of copper in the board; a simple board has two (top and bottom).
- **Via:** A tiny plated hole that carries a connection from one layer to another.
- **Silkscreen:** The white printed labels and outlines on the board.
- **BOOTSEL:** A button that, held while plugging in USB, makes the board appear as a drive so you can copy firmware onto it.
- **QSPI:** A fast four-wire connection between the RP2040 chip and its flash memory chip.
