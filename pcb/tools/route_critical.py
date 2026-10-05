#!/usr/bin/env python3
"""Hand-routed (scripted) critical copper, added to the placed board and LOCKED so Freerouting routes around it.

Run with KiCad's Python after gen_pcb.py:
  /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3 pcb/tools/route_critical.py

Stage 1 (2026-10-04): RP2350 power escape. The first all-nets autoroute (branch route-draft, run 1) failed only at U1's
power pins, boxed in by the decoupling ring. Here every decoupling cap's supply pad gets a short track to its own U1 pin,
every cap's ground pad gets a via straight down to the In1 ground plane, and U1's exposed pad gets a 3 x 3 via array.
Later stages (crystal, QSPI, USB, buck-boost, radio, core regulator loop) are added below as they are routed.
"""
import math
import pathlib

import pcbnew

ROOT = pathlib.Path(__file__).resolve().parents[2]
BOARD = ROOT / "pcb/kicad/pocket-chance-board.kicad_pcb"
OX = OY = 50.0
VIA_D, VIA_DRILL = 0.6, 0.3          # standard via (0.15 mm ring); EP vias are smaller
EP_VIA_D, EP_VIA_DRILL = 0.5, 0.25
W_PWR = 0.25                          # power escape width (QFN pads are 0.2 wide)

b = pcbnew.LoadBoard(str(BOARD))


def mm(v):
    return pcbnew.ToMM(v.x) - OX, pcbnew.ToMM(v.y) - OY


def vec(x, y):
    return pcbnew.VECTOR2I(pcbnew.FromMM(OX + x), pcbnew.FromMM(OY + y))


def track(p0, p1, net, width=W_PWR, layer=pcbnew.F_Cu):
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(vec(*p0)); t.SetEnd(vec(*p1))
    t.SetWidth(pcbnew.FromMM(width)); t.SetLayer(layer); t.SetNet(b.FindNet(net)); t.SetLocked(True)
    b.Add(t)


def via(p, net, d=VIA_D, drill=VIA_DRILL):
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(vec(*p)); v.SetWidth(pcbnew.FromMM(d)); v.SetDrill(pcbnew.FromMM(drill))
    v.SetNet(b.FindNet(net)); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetLocked(True)
    b.Add(v)


def pad(ref, num=None, net=None):
    for p in b.FindFootprintByReference(ref).Pads():
        if (num is None or p.GetNumber() == num) and (net is None or p.GetNetname() == net):
            return p
    raise KeyError((ref, num, net))


u1 = b.FindFootprintByReference("U1")
cx, cy = mm(u1.GetPosition())


def outward(px, py):
    """Unit vector away from U1's body for a pad at (px, py) on the QFN edge."""
    dx, dy = px - cx, py - cy
    return (math.copysign(1, dx), 0.0) if abs(dx) > abs(dy) else (0.0, math.copysign(1, dy))


# ---- stage 1: decoupling (cap -> its U1 supply pin), cap ground vias, exposed-pad vias
DECOUPLE = {"C1": "1", "C8": "6", "C2": "11", "C3": "20", "C9": "23", "C40": "23", "C4": "30", "C5": "38",
            "C10": "39", "C6": "45", "C43": "44", "C13": "49", "C7": "54"}
for cap, pin in DECOUPLE.items():
    up = pad("U1", pin)
    net = up.GetNetname()
    px, py = mm(up.GetPosition())
    ox, oy = outward(px, py)
    sp = pad(cap, net=net)
    gp = [p for p in b.FindFootprintByReference(cap).Pads() if p.GetNumber() != sp.GetNumber()][0]
    sx, sy = mm(sp.GetPosition())
    # leave the pin straight outward along its own row to the cap pad's outward coordinate, then jog sideways to the
    # pad: orthogonal stubs occupy only their own pin's lane (run 2 showed diagonal stubs block the neighbours)
    if ox:
        ex, ey = sx, py
    else:
        ex, ey = px, sy
    track((px, py), (ex, ey), net)
    if (ex, ey) != (sx, sy):
        track((ex, ey), (sx, sy), net)
    # ground pad: via just beyond the pad, on the side away from the supply pad
    gx, gy = mm(gp.GetPosition())
    ux, uy = gx - sx, gy - sy
    n = math.hypot(ux, uy)
    vx, vy = gx + ux / n * 0.75, gy + uy / n * 0.75
    track((gx, gy), (vx, vy), "GND", 0.3)
    via((vx, vy), "GND")

ep = pad("U1", "61")
ex0, ey0 = mm(ep.GetPosition())
for i in (-1, 0, 1):
    for j in (-1, 0, 1):
        via((ex0 + i * 1.1, ey0 + j * 1.1), "GND", EP_VIA_D, EP_VIA_DRILL)

b.Save(str(BOARD))
print("stage 1: decoupling escapes for", len(DECOUPLE), "caps, 9 exposed-pad vias; all locked")
