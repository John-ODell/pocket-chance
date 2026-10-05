"""Make a routing copy of the board with In1 = GND and In2 = +3V3 planes and export it to Specctra DSN for Freerouting.
Usage (KiCad Python): route_prep.py <board.kicad_pcb> <out.kicad_pcb> <out.dsn>"""
import pcbnew, sys
src, dst, dsn = sys.argv[1:4]
b = pcbnew.LoadBoard(src)
OX = OY = 50.0
def mm(x, y): return pcbnew.VECTOR2I(pcbnew.FromMM(OX + x), pcbnew.FromMM(OY + y))
def plane(layer, netname):
    z = pcbnew.ZONE(b)
    z.SetLayer(layer)
    z.SetNet(b.FindNet(netname))
    z.SetLocalClearance(pcbnew.FromMM(0.2))
    z.SetMinThickness(pcbnew.FromMM(0.2))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    ol = z.Outline(); ol.NewOutline()
    for x, y in ((0.5, 0.5), (149.5, 0.5), (149.5, 99.5), (0.5, 99.5)):
        ol.Append(pcbnew.FromMM(OX + x), pcbnew.FromMM(OY + y))
    b.Add(z)
plane(pcbnew.In1_Cu, "GND")
plane(pcbnew.In2_Cu, "+3V3")
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(dst)
print("export dsn", pcbnew.ExportSpecctraDSN(b, dsn))
