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
# A/B/X/Y: 12 mm tactile switches in a diamond (X top, Y left, A right, B bottom).
at("SW6", 122, 20)           # X
at("SW7", 104, 36)           # Y
at("SW4", 140, 36)           # A
at("SW5", 122, 52)           # B
# Screen module area x 52..98, y 4..46: the module sits above the board on standoffs, cable to J4. Kept empty.
at("J4", 75, 52, 180)        # LCD socket, cable entry towards the screen

# ---------------------------------------------------------------- MCU block (centre)
# U1 turned 90 clockwise: screen/SD pins face up, radio/audio/I2C pins face down, QSPI/USB/core regulator face right,
# crystal/SWD/RUN face left.
at("U1", 72, 70, 270)
at("U2", 88, 62, 90)         # flash, right of U1 near the QSPI pins
at("U3", 96, 62, 90)         # PSRAM next to the flash (shares clock and data)
row(["R4", "R5"], 84, 56.5, dx=2.4)      # flash CS pull-up and BOOT resistor
at("R6", 99, 56.5)                       # PSRAM CS pull-up
at("C18", 88, 67.5)                      # flash bypass
at("C19", 96, 67.5)                      # PSRAM bypass
# core regulator (RP2350 guide 2.1): L1 and its caps right-below U1, next to VREG_LX / 1V1 pins
at("L1", 80, 75, 90)
row(["C13", "C14", "C40"], 82.6, 73, dy=1.6)
at("C15", 82.6, 77.8)
at("R2", 82.6, 79.4)
# decoupling ring (IOVDD and DVDD)
row(["C1", "C2", "C3"], 66, 63.5, dx=2.4)          # top edge of U1
row(["C4", "C5"], 75.5, 63.5, dx=2.4)
row(["C6", "C7"], 78, 66.0, dy=2.4, rot=90)
row(["C8", "C9", "C10"], 65.2, 65.8, dy=2.4, rot=90)
row(["R1", "C12"], 75.5, 77.5, dx=3.0)               # ADC supply filter (radio side, pin 44)
# crystal (left side, pins 21/22)
at("Y1", 61, 72, 90)
row(["C16", "C17"], 57.5, 70.3, dy=3.4)
at("R3", 64, 75.8)
# reset, boot, SWD
at("R7", 64, 78, 0)
at("J1", 52, 80, 90)                    # SWD 2x5 1.27 mm
at("SW1", 59.5, 61.5, 0)                   # BOOT
at("SW2", 40, 60, 0)                 # RESET
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
at("J2", 124, H - 6.57, 0)               # USB-C: the footprint's own PCB-edge line (Dwgs.User) is 6.57 mm below its origin
row(["R8", "R9"], 116, 92, dy=1.6)      # CC pull-downs
at("U4", 124, 86, 0)                    # USB ESD
row(["R10", "R11"], 104, 79, dy=1.6)    # USB series resistors near U1
at("TP1", 132, 88)                      # VBUS
at("C20", 117, 84, 90)
at("U5", 112, 88, 0)                    # charger
row(["R12", "R14", "R15", "R16"], 106, 92, dx=2.2, rot=90)
at("R13", 117, 81)
at("C21", 108, 84, 90)
at("C22", 112, 94, 0)
row(["D1", "R18"], 104, 86, dy=2.2)
at("TP2", 104, 96)                      # VSYS
# buck-boost 3.3 V
at("U6", 110, 72, 0)
at("L2", 116, 72, 0)
at("C23", 106, 74, 90)
at("C24", 106, 70, 90)
row(["C25", "C26"], 110, 66.5, dx=3.6)
at("R19", 118, 66.5)
at("SW3", W - 3.5, 70, 90)              # power slide switch, actuator over the right edge
at("C11", 104, 66.5, 0)                 # 3.3 V bulk (re-placed here, near the regulator output)
# battery: socket on the right edge, fuse and protection next to it
at("J3", W - 5.5, 88, 90)                 # LiPo socket, cable entry from the right edge
at("F1", 136, 95.5, 0)
at("R22", 134, 91, 0)
at("TP7", 128, 80)                      # BAT+
at("U7", 140, 80, 0)                    # DW01A
at("Q1", 140, 75, 0)                    # FS8205A
row(["R20", "R21", "C27"], 134, 76, dy=1.6)
at("TP6", 146, 96)                      # GND near the battery
# gated battery divider, near U1's ADC pin side
at("Q4", 90, 86, 0)
at("Q3", 95, 86, 0)
row(["R39", "R23", "R24", "C28"], 90, 90, dx=2.2, rot=90)

# ---------------------------------------------------------------- audio, RTC, IMU, expansion (bottom left)
at("U8", 38, 80, 0)                     # PAM8302A
row(["R25", "C29", "C30", "C31"], 32, 74.5, dx=2.4, rot=90)
row(["C32", "C41"], 44, 76, dy=2.0)
row(["R44", "C42"], 44, 84, dy=1.6)
at("J5", 5.6, 78, 270)                  # speaker socket, cable from the left edge
at("U9", 20, 66, 0)                     # DS3231MZ RTC
row(["C33"], 20, 61, 0)
at("BT2", 15, 90.5, 0)                    # CR1220 holder
row(["R42", "R43", "JP2"], 27, 70, dy=2.0)
at("U10", 44, 66, 0)                    # LSM6DSOX
row(["C34", "C35"], 40.5, 65.5, dy=1.6)
row(["C36", "C37"], 48, 69, dy=1.6)
row(["R31", "R32"], 34, 66, dy=1.6)     # I2C pull-ups
at("J7", 50, 95.5, 0)                   # STEMMA QT, cable from the bottom edge
at("J8", 30, 97, 90)                    # expansion header along the bottom edge
at("TP5", 57, 89)                       # GND
# microSD on the left edge, card pushed in from outside the board
at("J6", 7.6, 62, 270)
row(["R26", "R27", "R28", "R29", "R30"], 17, 55.5, dy=1.6)


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
        r.SetStart(mm(52, 4))
        r.SetEnd(mm(98, 46))
        board.Add(r)
    t = pcbnew.PCB_TEXT(board)
    t.SetText("SCREEN MODULE (1.54in, on standoffs, cable to J4)")
    t.SetLayer(pcbnew.F_SilkS)
    t.SetPosition(mm(75, 25))
    t.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(1.2), pcbnew.FromMM(1.2)))
    board.Add(t)
    t2 = pcbnew.PCB_TEXT(board)
    t2.SetText("Pocket Chance spin 1  rev 0.10 placement draft")
    t2.SetLayer(pcbnew.F_SilkS)
    t2.SetPosition(mm(75, 1.8))
    t2.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(1.0), pcbnew.FromMM(1.0)))
    board.Add(t2)
    board.Save(str(OUT))
    print(f"wrote {OUT.relative_to(ROOT)}: {len(comps)} footprints, {len(netobj)} nets, outline {W} x {H} mm")
    if missing:
        print("NOT PLACED (parked below the board):", " ".join(missing))


if __name__ == "__main__":
    main()
