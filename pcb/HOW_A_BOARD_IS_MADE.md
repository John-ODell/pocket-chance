# How a board is made: from idea to boards in your hands

Written 2026-10-04 by the PCB maker, for someone doing this for the first time. Costs and times are **estimates**. Confirm prices on the fab's quote page before you order.

## The short version

You draw a circuit, then you draw the board, then a factory makes it. The drawing happens in a free program called **KiCad**. The factory is called a **fab**. Between "draw" and "order" there are checks, and each check is cheap compared with a wrong board. Everything up to the order costs nothing but time.

## The steps

### 1. Decide what the board does (days)
Write down what must be on it and what it must do. We did the first pass today: [`requirements/REQUIREMENTS.md`](requirements/REQUIREMENTS.md) and [`CONSTRAINTS.md`](CONSTRAINTS.md). Then you answer the questions in [`PLAN.md`](PLAN.md): what goes on the board, screen approach, battery, shape, assembly, budget, sharing. One at a time, with a recommendation each.
- Costs you: an hour of reading and a few decisions.

### 2. Install KiCad (half an hour)
KiCad is free and runs on your Mac. It holds two drawings per project: the **schematic** (what connects to what) and the **PCB layout** (where things physically sit and where the copper goes).

```bash
brew install --cask kicad
```

You should see: a "KiCad" app in Applications that opens to a project window. Tell me the version number from "KiCad > About KiCad".

### 3. Choose the parts (a few days)
Every chip, resistor, capacitor, button and socket is a **part**. Each needs three things: a part number you can buy, a **symbol** (its picture in the schematic) and a **footprint** (the shape of its solder pads on the board). KiCad has libraries of symbols and footprints for most common parts.

We choose parts from the fab's own stock when we can, so the fab can solder them. For each part we read its **datasheet** (the maker's document) to confirm the footprint and voltages.
- Costs you: approving the datasheet downloads, and a look at each choice.

### 4. Draw the schematic (a few evenings)
In KiCad's schematic editor you place symbols and draw wires between pins. The RP2040 chip needs a fixed set of support parts: the crystal, decoupling capacitors, the flash chip, the USB connector, the boot button. The official Raspberry Pi guide "Hardware design with RP2040" shows the minimal circuit, and we follow it.

Then you run the **ERC** (electrical rules check). It finds pins left unconnected, two outputs tied together, power pins with no supply. You fix every error. I can run the same check from the terminal on your saved file.
- Costs you: the clicking, guided step by step. I check each saved file.

### 5. Review 1 (a day)
The microcontroller expert checks every pin against the game's code. I check the circuit against the RP2040 guide and the datasheets. The result is a written review with open risks. Nothing is ordered until it is clean.

### 6. Assign footprints (an evening)
Every symbol in the schematic gets a footprint. This is where first boards most often go wrong: a footprint that is a little off means a part that does not fit. We check each one against its datasheet drawing, and we look at the 3D view.

### 7. Lay out the board (several evenings)
In the PCB editor you draw the board outline, place the parts, and draw the copper traces that join them. A simple board has two copper layers: top and bottom. Small plated holes called **vias** connect the two. Most of the bottom layer becomes a solid **ground plane**, which keeps the fast signals clean.

Rules we follow: the crystal and its capacitors tight against the chip; the flash chip close with short traces; the two USB data wires drawn as a matched pair; the screen's SPI traces short with ground next to them (the 62.5 MHz link is the one we most want clean).

Then you run the **DRC** (design rules check): traces too close, holes too small, copper too near the edge. The limits come from the fab's capabilities page. Fix every error.
- Costs you: the most clicking of the whole project. We do it in small sessions.

### 8. Review 2 and the paper test (a day)
A second written review of the layout, the 3D view, and test points. Then print the board at 1:1 on paper and hold the real parts on it: the screen module, the buttons, the USB cable. If anything does not line up, fix it now. This costs a sheet of paper and saves a whole order.

### 9. Export the fab files (an hour)
KiCad exports **Gerber** files (one per layer: copper, solder mask, silkscreen, outline), a **drill** file (every hole), and for assembly a **BOM** (bill of materials: the parts list) and a **pick-and-place** file (where each part sits). I produce these with `kicad-cli` from your saved project and zip them into `pcb/fab/`.

### 10. Upload to the fab and read the quote (an hour)
You upload the zip to the fab's quote page. It shows a preview of every layer and a price. We check the preview layer by layer: outline right, holes right, nothing missing. If you chose assembly, you also upload the BOM and pick-and-place, and the fab shows which parts it matched and which are out of stock.
- Options you will see: layers (2), thickness (1.6 mm), colour, surface finish, quantity (5 is often the minimum), assembly (yes or no, which side). I give you the exact list to tick.

### 11. Order (ten minutes, yours alone)
You place the order and pay. I never do this and never see your payment details. You get a confirmation and later a tracking number.
- Costs you: the money in `CONSTRAINTS.md` section 8, and 1 to 3 weeks of waiting.

### 12. Bring-up (an evening, carefully)
The boards arrive. Before plugging anything in, you look at them under a light for shorts and missing parts. Then, in order, with a multimeter:
1. Measure resistance between 3.3 V and ground: it must not be a short.
2. Plug in USB. Measure 3.3 V on the 3.3 V test point.
3. Hold BOOT and plug in: the `RPI-RP2` drive should appear. If it does, the chip, crystal, flash and USB all work.
4. Drag the MicroPython file on. Run `mpremote connect list`.
5. Plug in the screen. Run the game.
If a battery is ever on the board, its first power-up is through a current-limited supply, with the expert's checklist.

### 13. Second spin (likely)
Most first boards need one fix. Keep a list of everything wrong, fix them all at once, and order again. The second order is usually right.

## Where the time goes

| Step | Your time | Waiting |
|---|---|---|
| 1 to 3: decide, install, parts | a few hours over a few days | none |
| 4 to 8: schematic, reviews, footprints, layout | several evenings over 1 to 3 weeks | a day per review |
| 9 to 11: export, quote, order | a couple of hours | none |
| Fab and shipping | nothing | 1 to 3 weeks |
| 12: bring-up | an evening | none |

## Words you will hear

- **Schematic**: the circuit drawing. **Layout**: the board drawing. **Footprint**: a part's pad shape. **Symbol**: a part's schematic picture.
- **ERC / DRC**: KiCad's checks of the schematic and the layout.
- **Gerber, drill, BOM, pick-and-place**: the files a fab needs.
- **Layer**: one sheet of copper. **Via**: a plated hole joining layers. **Ground plane**: a big area of copper tied to ground.
- **Silkscreen**: the printed labels. **Solder mask**: the coloured coating that keeps solder off the copper.
- **BOOT / BOOTSEL**: the button that makes the board show up as a drive for loading firmware.
- **QSPI flash**: the memory chip that holds the firmware and your files.
- **Decoupling capacitor**: a tiny capacitor next to a chip's power pin that smooths its supply. The RP2040 wants about ten of them.
