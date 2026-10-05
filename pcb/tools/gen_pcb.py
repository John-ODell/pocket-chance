#!/usr/bin/env python3
"""Place every footprint of the Pocket Chance board from the exported netlist (phase 6, placement).

Run with KiCad's own Python (it has the pcbnew module):
  /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3 pcb/tools/gen_pcb.py

Input:  pcb/kicad/exports/netlist.xml (from export.sh; the schematic is the source of truth)
Output: pcb/kicad/pocket-chance-board.kicad_pcb (outline, 4 copper layers, footprints with nets, placement only)

Board coordinates below are millimetres from the board's top-left corner, y downwards, as seen from the front.
Rotation is KiCad's: degrees counter-clockwise. Spin 1 is a prototype: size is not a constraint, probing room is.
Placement only: tracks and zones come later. Re-running replaces the whole board file.
"""
import json
import pathlib
import sys
import xml.etree.ElementTree as ET

import pcbnew

ROOT = pathlib.Path(__file__).resolve().parents[2]
KDIR = ROOT / "pcb/kicad"
NETLIST = KDIR / "exports/netlist.xml"
OUT = KDIR / "pocket-chance-board.kicad_pcb"
FPDIR = pathlib.Path("/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints")

OX, OY = 50.0, 50.0          # where the board's top-left corner sits on KiCad's page
W, H = 150.0, 100.0          # board outline (prototype; credit-card size is spin 2)
SCR_X0, SCR_Y0, SCR_X1, SCR_Y1 = 49.0, 4.0, 101.0, 41.0   # screen reserve, 52 x 37 mm

P = {}                       # ref -> (x, y, rotation)


def at(ref, x, y, rot=0):
    P[ref] = (x, y, rot)


def row(refs, x, y, dx=0.0, dy=0.0, rot=0):
    for k, r in enumerate(refs):
        at(r, x + dx * k, y + dy * k, rot)


# ---------------------------------------------------------------- controls (top band, front)
# D-pad: five 6 mm tactile switches in a cross; left/right turned 90 so they sit narrow side in.
at("SW8", 24, 25)            # up
at("SW9", 24, 51)            # down
at("SW12", 24, 38)           # press (centre)
at("SW10", 10, 38, 90)       # left
at("SW11", 38, 38, 90)       # right
# A/B/X/Y: 12 mm tactile switches turned 90 (pads above/below) in a diamond (X top, Y left, A right, B bottom),
# clear of the screen reserve (placement review 19:02: the old Y overlapped it by 2.4 mm).
at("SW6", 130, 13.5, 90)     # X
at("SW7", 117, 31, 90)       # Y
at("SW4", 143, 31, 90)       # A
at("SW5", 130, 48.5, 90)     # B
# Screen reserve SCR_X0..SCR_X1 x SCR_Y0..SCR_Y1 (52 x 37 mm): holds the chosen 1.54" Waveshare module (50 x 35 mm)
# and the 1.3" (45 x 31 mm) in landscape. The module sits on standoffs, cable to J4. Standoff holes wait for the
# module's mechanical drawing.
at("J4", 75, 52, 180)        # LCD socket, cable entry towards the screen
at("J9", 66.11, 44.0, 90)    # rev 0.11: 1x8 2.54 mm header on the same nets as J4, pins in a row left to right

# ---------------------------------------------------------------- MCU block (centre)
# U1 turned 90 clockwise: screen/SD pins face up, radio/audio/I2C pins face down, QSPI/USB/core regulator face right,
# crystal/SWD/RUN face left. U1 pins (board mm): top edge y 66.55 (pin 1 at x 74.8 ... pin 15), left edge x 68.55
# (pins 16..30), bottom edge y 73.45 (pins 31..45), right edge x 75.45 (pin 46 at y 72.8 ... pin 60 at y 67.2).
at("U1", 72, 70, 270)
at("U2", 88, 62, 90)         # flash, right of U1 near the QSPI pins
at("U3", 96, 62, 90)         # PSRAM next to the flash (shares clock and data)
row(["R4", "R5"], 84, 56.5, dx=2.4)      # flash CS pull-up and BOOT resistor
at("R6", 99, 56.5)                       # PSRAM CS pull-up
at("C18", 88, 67.5)                      # flash bypass
at("C19", 96, 67.5)                      # PSRAM bypass
# core regulator (RP2350 guide 2.1, pp.7-8): LX pin 48 (75.45, 72.0) -> L1 pad 1 -> 1V1; VREG_VIN pin 49 (71.6)
at("L1", 78.2, 73.6, 0)                  # pad 1 (dot, VREG_LX) at x 77.45, nearest pin 48
at("C13", 77.4, 71.8, 0)                 # VREG_VIN 4.7 uF, beside pin 49
at("C14", 80.8, 73.6, 90)                # 1V1 4.7 uF at L1 pad 2
at("C15", 77.6, 75.8, 0)                 # VREG_AVDD 4.7 uF (pin 46) with R2
at("R2", 79.8, 75.8, 0)
# decoupling: one cap per supply pin, at that pin (placement review 19:02)
at("C1", 74.8, 64.3, 90)                 # IOVDD pin 1
at("C8", 72.8, 64.3, 90)                 # DVDD pin 6
at("C2", 70.8, 64.3, 90)                 # IOVDD pin 11
at("C3", 66.3, 67.4, 0)                  # IOVDD pin 20
at("C9", 66.3, 69.4, 0)                  # DVDD pin 23
at("C40", 66.3, 70.9, 0)                 # DVDD pin 23 bulk 4.7 uF (guide: one per DVDD side)
at("C4", 66.3, 72.9, 0)                  # IOVDD pin 30
at("C5", 70.8, 75.8, 90)                 # IOVDD pin 38
at("C10", 72.0, 75.8, 90)                # DVDD pin 39
at("C6", 74.0, 75.8, 90)                 # IOVDD pin 45
at("C12", 75.6, 76.2, 90)                # ADC_AVDD 2.2 uF, pin 44 (room left at 73.2, 77.6 for the 100 nF if approved)
at("R1", 75.6, 79.0, 90)
at("C7", 77.4, 65.6, 0)                  # USB/QSPI IOVDD pins 53/54
# crystal (left side, pins 21/22)
at("Y1", 61, 72, 90)
row(["C16", "C17"], 57.5, 70.3, dy=3.4)
at("R3", 64, 75.8)
# reset, boot, SWD
at("R7", 64, 78, 0)
at("J1", 52, 80, 90)                    # SWD 2x5 1.27 mm
at("SW1", 59.5, 61.5, 0)                # BOOT
at("SW2", 40, 60, 0)                    # RESET
at("TP8", 58, 76)                       # RUN
at("TP4", 86, 80)                       # 1V1
at("TP3", 100, 70)                      # +3V3
# user LED
at("D2", 66, 81, 0)
at("R35", 69, 81, 0)

# ---------------------------------------------------------------- radio (bottom centre, antenna at the bottom edge)
at("U11", 72, H - 8.25, 180)            # RM2 module edge on the board edge; keep-out spills off the board
row(["C38", "C39"], 60, 86, dy=2.0)
row(["R33", "R34"], 76.5, 81, dx=2.4)
row(["R36", "R37"], 84, 86, dy=1.6)     # VBUS sense divider

# ---------------------------------------------------------------- power (bottom right)
at("J2", 124, H - 6.57, 0)              # USB-C: the footprint's own PCB-edge line (Dwgs.User) is 6.57 mm below its origin
row(["R8", "R9"], 116, 92, dy=1.6)      # CC pull-downs
at("U4", 127, 89.2, 0)                  # USB ESD, right behind the connector pins (review: was 11.4 mm away)
row(["R10", "R11"], 104, 79, dy=1.6)    # USB series resistors near U1
at("TP1", 120.5, 83.5)                  # VBUS (moved clear of the J3 polarity text)
# charger U5 (112, 88): BAT pins 2/3 left, VSYS 10/11 right, VBUS 13 / TMR 14 / ISET 16 top, EN1 6 bottom, ILIM 12 right
at("U5", 112, 88, 0)
at("C22", 108.4, 88.0, 90)              # BAT 10 uF at pins 2/3
at("C21", 115.6, 88.0, 90)              # VSYS 10 uF at pins 10/11
at("C20", 113.9, 84.2, 90)              # VBUS 1 uF at pin 13
at("R12", 108.4, 85.6, 0)               # TS (pin 1)
at("R14", 110.8, 84.2, 90)              # ISET (pin 16)
at("R16", 112.1, 84.2, 90)              # TMR (pin 14)
at("R15", 115.8, 85.2, 0)               # ILIM (pin 12)
at("R13", 111.5, 92.0, 90)              # EN1 pull-up (pin 6)
row(["D1", "R18"], 118.5, 89.5, dy=1.8) # charge LED (pin 9)
at("TP2", 104, 96)                      # VSYS
# buck-boost 3.3 V, U6 pins: 1 VOUT, 2 L2, 3 PGND, 4 L1, 5 VIN on the left (x 108.6); 6 EN, 7 PS, 8 VINA, 9 GND,
# 10 FB on the right. L2 sits against the left pins (TPS6300x p.16).
at("U6", 110, 72, 0)
at("L2", 105.4, 72, 90)                 # pad 1 (BB_L1) down at pin 4, pad 2 (BB_L2) up at pin 2
at("C23", 109.5, 75.8, 0)               # VIN 10 uF below pin 5
row(["C25", "C26"], 109.2, 68.2, dx=3.7)# VOUT 2 x 10 uF above pin 1
at("C24", 113.6, 72.0, 90)              # VINA 100 nF (pin 8)
at("R19", 113.6, 75.0, 0)               # EN pull-down (pin 6)
at("SW3", W - 3.5, 70, 90)              # power slide switch, actuator over the right edge
at("C11", 104, 66.5, 0)                 # 3.3 V bulk
# battery: socket on the right edge, fuse and protection next to it
at("J3", W - 5.5, 88, 90)               # LiPo socket, cable entry from the right edge; pin 1 (+) is the lower pin
at("F1", 136, 95.5, 0)
at("R22", 134, 91, 0)
at("TP7", 128, 80)                      # BAT+
at("U7", 140, 80, 0)                    # DW01A
at("Q1", 140, 75, 0)                    # FS8205A
row(["R20", "R21", "C27"], 134, 76, dy=1.6)
at("TP6", 142, 97.5)                    # GND near the battery (clear of the corner mounting hole)
# gated battery divider, near U1's ADC pin side
at("Q4", 90, 86, 0)
at("Q3", 95, 86, 0)
row(["R39", "R23", "R24", "C28"], 90, 90, dx=2.2, rot=90)

# ---------------------------------------------------------------- audio, RTC, IMU, expansion (bottom left)
at("U8", 38, 80, 0)                     # PAM8302A
row(["R25", "C29", "C30", "C31"], 32, 74.5, dx=2.4, rot=90)
row(["C32", "C41"], 43.4, 80.6, dy=2.0) # amplifier VDD pin 6 (40.5, 80.6)
row(["R44", "C42"], 33, 84, dy=1.6)     # SD pin 1
at("J5", 5.6, 78, 270)                  # speaker socket, cable from the left edge
at("U9", 24, 70, 0)                     # DS3231MZ RTC, VCC pin 2 on the left
at("C35", 19.6, 69.4, 90)               # RTC bypass at pin 2 (review: was 22.6 mm away)
at("BT2", 15, 90.5, 0)                  # CR1220 holder
row(["R42", "R43", "JP2"], 29.6, 72.6, dy=2.2)
at("U10", 44, 66, 0)                    # LSM6DSOX
row(["C36", "C37"], 47.2, 67.6, dy=1.4) # IMU VDD/VDDIO pins 8 and 12 (right side)
row(["R31", "R32"], 34, 66, dy=1.6)     # I2C pull-ups
at("J7", 50, 95.5, 0)                   # STEMMA QT, cable from the bottom edge
at("J8", 30, 97, 90)                    # expansion header along the bottom edge
at("TP5", 57, 89)                       # GND
# microSD on the left edge, card pushed in from outside the board; VDD pin 4 at (13.05, 62.2)
at("J6", 7.6, 62, 270)
at("C34", 15.4, 62.2, 90)               # SD 100 nF at pin 4 (review: was 27 mm away)
at("C33", 17.6, 62.2, 90)               # SD 10 uF next to it
row(["R26", "R27", "R28", "R29", "R30"], 17, 54.0, dy=1.3)


# ---------------------------------------------------------------- build
def load_netlist():
    root = ET.parse(NETLIST).getroot()
    comps = {}
    for c in root.iter("comp"):
        comps[c.get("ref")] = (c.findtext("value"), c.findtext("footprint"))
    nets = {}
    for n in root.iter("net"):
        for node in n.iter("node"):
            nets.setdefault(node.get("ref"), {})[node.get("pin")] = n.get("name")
    return comps, nets


def fp_path(lib):
    return str(KDIR / "lib/pcb_custom.pretty") if lib == "pcb_custom" else str(FPDIR / f"{lib}.pretty")


def mm(x, y):
    return pcbnew.VECTOR2I(pcbnew.FromMM(OX + x), pcbnew.FromMM(OY + y))


def silk_text(board, text, x, y, size):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(text)
    t.SetLayer(pcbnew.F_SilkS)
    t.SetPosition(mm(x, y))
    t.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(size), pcbnew.FromMM(size)))
    t.SetTextThickness(pcbnew.FromMM(size * 0.15))
    board.Add(t)
    return t


def rect(board, layer, x0, y0, x1, y1, width):
    r = pcbnew.PCB_SHAPE(board)
    r.SetShape(pcbnew.SHAPE_T_RECT)
    r.SetLayer(layer)
    r.SetWidth(pcbnew.FromMM(width))
    r.SetStart(mm(x0, y0))
    r.SetEnd(mm(x1, y1))
    board.Add(r)


def hole(board, ref, x, y, d):
    """A board-only non-plated hole (cable tie), not in the schematic, BOM or pick-and-place."""
    fp = pcbnew.FOOTPRINT(board)
    fp.SetReference(ref)
    fp.Reference().SetVisible(False)
    fp.SetValue("tie-down hole")
    fp.Value().SetVisible(False)
    fp.SetBoardOnly(True)
    fp.SetExcludedFromBOM(True)
    fp.SetExcludedFromPosFiles(True)
    pad = pcbnew.PAD(fp)
    pad.SetAttribute(pcbnew.PAD_ATTRIB_NPTH)
    pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
    pad.SetSize(pcbnew.VECTOR2I(pcbnew.FromMM(d), pcbnew.FromMM(d)))
    pad.SetDrillSize(pcbnew.VECTOR2I(pcbnew.FromMM(d), pcbnew.FromMM(d)))
    pad.SetLayerSet(pad.UnplatedHoleMask())
    fp.Add(pad)
    board.Add(fp)
    fp.SetPosition(mm(x, y))


def main():
    comps, pinnets = load_netlist()
    missing = sorted(set(comps) - set(P), key=str)
    extra = sorted(set(P) - set(comps))
    if extra:
        sys.exit(f"placed but not in netlist: {extra}")
    board = pcbnew.BOARD()
    board.SetCopperLayerCount(4)
    ds = board.GetDesignSettings()
    ds.SetBoardThickness(pcbnew.FromMM(1.6))
    # PCBWay standard limits (REQUIREMENTS 11c): 0.1 mm trace/space, 0.15 mm annular ring; we keep margin.
    ds.m_TrackMinWidth = pcbnew.FromMM(0.127)
    ds.m_MinClearance = pcbnew.FromMM(0.127)
    ds.m_ViasMinSize = pcbnew.FromMM(0.5)
    ds.m_MinThroughDrill = pcbnew.FromMM(0.2)       # thermal vias under U5/U6; PCBWay drills from 0.15 mm
    nc = ds.m_NetSettings.GetDefaultNetclass()
    nc.SetClearance(pcbnew.FromMM(0.15))              # fine-pitch pads (USB-C, LGA) are 0.15 mm apart
    nc.SetTrackWidth(pcbnew.FromMM(0.2))
    netobj = {}
    for name in sorted({n for d in pinnets.values() for n in d.values()}):
        ni = pcbnew.NETINFO_ITEM(board, name)
        board.Add(ni)
        netobj[name] = ni
    staging = 0
    for ref, (value, fpid) in sorted(comps.items()):
        lib, name = fpid.split(":")
        fp = pcbnew.FootprintLoad(fp_path(lib), name)
        if fp is None:
            sys.exit(f"footprint not found: {fpid}")
        fp.SetFPID(pcbnew.LIB_ID(lib, name))
        fp.SetReference(ref)
        fp.SetValue(value)
        if ref in P:
            x, y, rot = P[ref]
        else:                                   # unplaced parts parked below the board, visible in the render
            x, y, rot = 5 + 8 * (staging % 18), H + 15 + 8 * (staging // 18), 0
            staging += 1
        board.Add(fp)
        fp.SetPosition(mm(x, y))
        fp.SetOrientationDegrees(rot)
        for pad in fp.Pads():
            net = pinnets.get(ref, {}).get(pad.GetNumber())
            if net:
                pad.SetNet(netobj[net])
    # outline
    corners = [(0, 0), (W, 0), (W, H), (0, H)]
    for (x0, y0), (x1, y1) in zip(corners, corners[1:] + corners[:1]):
        seg = pcbnew.PCB_SHAPE(board)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetLayer(pcbnew.Edge_Cuts)
        seg.SetWidth(pcbnew.FromMM(0.1))
        seg.SetStart(mm(x0, y0))
        seg.SetEnd(mm(x1, y1))
        board.Add(seg)
    # screen area marked on the fab and silk layers
    for layer, wdt in ((pcbnew.F_Fab, 0.1), (pcbnew.F_SilkS, 0.15)):
        r = pcbnew.PCB_SHAPE(board)
        r.SetShape(pcbnew.SHAPE_T_RECT)
        r.SetLayer(layer)
        r.SetWidth(pcbnew.FromMM(wdt))
        r.SetStart(mm(SCR_X0, SCR_Y0))
        r.SetEnd(mm(SCR_X1, SCR_Y1))
        board.Add(r)
    t = pcbnew.PCB_TEXT(board)
    t.SetText("SCREEN MODULE 1.54in 50x35 (or 1.3in), on standoffs, cable to J4")
    t.SetLayer(pcbnew.F_SilkS)
    t.SetPosition(mm((SCR_X0 + SCR_X1) / 2, (SCR_Y0 + SCR_Y1) / 2))
    t.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(1.2), pcbnew.FromMM(1.2)))
    board.Add(t)
    t2 = pcbnew.PCB_TEXT(board)
    t2.SetText("Pocket Chance spin 1  rev 0.10 placement draft")
    t2.SetLayer(pcbnew.F_SilkS)
    t2.SetPosition(mm(75, 1.8))
    t2.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(1.0), pcbnew.FromMM(1.0)))
    board.Add(t2)
    # J3 polarity marks (AUDIT-3 #28): pin 1 = CELL_P = + RED WIRE is the lower pin, pin 2 = - the upper one
    silk_text(board, "+ RED", 136.6, 89.0, 1.2)
    silk_text(board, "-  BLK", 136.6, 87.0, 1.2)
    silk_text(board, "CHECK POLARITY WITH A METER", 135.0, 85.2, 0.8)
    # the cell lives on the back behind the A/B/X/Y buttons (front: SMD switches only, nothing hot, no through-hole
    # tails), on insulating foam tape inside this outline; its lead runs down the back and round the right edge into J3
    # and is tied down through the two holes beside J3. Kept off the back of the charger and buck-boost (auditor 19:21).
    rect(board, pcbnew.B_SilkS, 92.0, 3.0, 144.0, 39.0, 0.15)   # clear of the corner mounting hole
    for k, line in enumerate(("LiPo CELL 52 x 34 x 10", "on insulating foam tape", "lead to J3 round the right edge")):
        t3 = silk_text(board, line, 118.0, 17.0 + 3.0 * k, 1.2)
        t3.SetLayer(pcbnew.B_SilkS)
        t3.SetMirrored(True)
    # tie-down holes 3.0 mm: a common 2.5 x 1 mm cable tie passes flat (auditor 19:28: 2.2 mm was too small)
    for k, (x, y) in enumerate(((147.0, 76.5), (147.0, 81.2))):
        hole(board, f"H{k + 1}", x, y, 3.0)
    # four corner mounting holes for M2 nylon standoffs (2.4 mm clearance), 3.5 mm in from each corner
    for k, (x, y) in enumerate(((3.5, 3.5), (W - 3.5, 3.5), (3.5, H - 3.5), (W - 3.5, H - 3.5))):
        hole(board, f"MH{k + 1}", x, y, 2.4)
    # speaker: PAM8302A bridge output, neither terminal is ground (auditor 19:28)
    silk_text(board, "SPK+ SPK-: bridge output,", 12.5, 71.5, 0.8)
    silk_text(board, "neither wire is GND", 12.5, 72.8, 0.8)
    # J9 pin names (wire by name: modules differ in pin order), one label per pin, reading upwards into the screen area
    j9 = board.FindFootprintByReference("J9")
    if j9:
        names = {"1": "3V3", "2": "GND", "3": "MOSI/SDA", "4": "SCK/SCL", "5": "CS", "6": "DC", "7": "RST", "8": "BL"}
        for p in j9.Pads():
            t = silk_text(board, names[p.GetNumber()], 0, 0, 0.9)
            t.SetTextAngleDegrees(90)
            t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT)
            t.SetPosition(p.GetPosition() + pcbnew.VECTOR2I(0, pcbnew.FromMM(-1.8)))
        silk_text(board, "J9: WIRE BY NAME, MODULES DIFFER IN ORDER. ONE SCREEN AT A TIME", 75.0, 30.5, 0.9)
    # rail names next to the probe pads
    for fp in board.GetFootprints():
        if fp.GetReference().startswith("TP"):
            v = fp.Value()
            v.SetLayer(pcbnew.F_SilkS)
            v.SetVisible(True)
            v.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(0.8), pcbnew.FromMM(0.8)))
            v.SetPosition(fp.GetPosition() + pcbnew.VECTOR2I(0, pcbnew.FromMM(2.0)))
    pro = OUT.with_suffix(".kicad_pro")
    before = json.loads(pro.read_text())
    board.Save(str(OUT))                    # this also rewrites the project file with only board settings
    after = json.loads(pro.read_text())
    for key in ("board", "net_settings"):   # keep the schematic/ERC settings, take the new board and net-class rules
        before[key] = after[key]
    pro.write_text(json.dumps(before, indent=2) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(comps)} footprints, {len(netobj)} nets, outline {W} x {H} mm")
    if missing:
        print("NOT PLACED (parked below the board):", " ".join(missing))


if __name__ == "__main__":
    main()
