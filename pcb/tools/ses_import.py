"""Usage (KiCad Python): ses_import.py <board.kicad_pcb> <routes.ses> <pcb/tools dir>.
Import a Freerouting .ses into a KiCad board (KiCad's ImportSpecctraSES returned False on this file)."""
import sys, re
sys.path.insert(0, sys.argv[3])
import pcbnew, sexp
pcb, ses = sys.argv[1:3]
b = pcbnew.LoadBoard(pcb)
tree = sexp.parse(open(ses).read())
def find(node, name):
    for c in node[1:] if isinstance(node, list) else []:
        if isinstance(c, list) and c and str(c[0]) == name:
            yield c
def first(node, name):
    return next(find(node, name), None)
sess = tree[0] if isinstance(tree[0], list) else tree
res = 1.0
rt = first(sess, "routes")
r = first(rt, "resolution")
if r: res = float(r[2])              # units per um
k = 1e-3 / res                       # session units -> mm
layers = {b.GetLayerName(l): l for l in range(pcbnew.PCB_LAYER_ID_COUNT)}
nt = first(rt, "network_out")
nwires = nvias = 0
for net in find(nt, "net"):
    name = str(net[1])
    ni = b.FindNet(name)
    for w in find(net, "wire"):
        ty = first(w, "type")
        if ty is not None and str(ty[1]) in ("fix", "protect"):
            continue                      # our own locked copper, already on the board
        p = first(w, "path")
        lay = layers[str(p[1])]; width = float(p[2]) * k
        xs = [float(v) for v in p[3:] if not isinstance(v, list)]
        pts = [(xs[i] * k, -xs[i + 1] * k) for i in range(0, len(xs) - 1, 2)]
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            t = pcbnew.PCB_TRACK(b)
            t.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(x0), pcbnew.FromMM(y0)))
            t.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(x1), pcbnew.FromMM(y1)))
            t.SetWidth(pcbnew.FromMM(width)); t.SetLayer(lay); t.SetNet(ni)
            b.Add(t); nwires += 1
    for v in find(net, "via"):
        ty = first(v, "type")
        if ty is not None and str(ty[1]) in ("fix", "protect"):
            continue
        m = re.search(r"_(\d+):(\d+)_um", str(v[1]))
        dia, drill = int(m.group(1)) / 1000, int(m.group(2)) / 1000
        via = pcbnew.PCB_VIA(b)
        via.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(float(v[2]) * k), pcbnew.FromMM(-float(v[3]) * k)))
        via.SetWidth(pcbnew.FromMM(dia)); via.SetDrill(pcbnew.FromMM(drill)); via.SetNet(ni)
        via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        b.Add(via); nvias += 1
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.BuildConnectivity()
print("segments", nwires, "vias", nvias, "unrouted connections", b.GetConnectivity().GetUnconnectedCount(True))
b.Save(pcb)
