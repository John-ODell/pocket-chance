# netdiff.py <old-ref> <new-ref> [repo]: semantic diff of pcb/kicad/exports/netlist.xml between two commits.
# Components by ref/value/footprint, nets by node set (so renamed or renumbered nets do not show as changes).
# Used for every schematic revision check (HR-P05). Default repo: ../pcb-desk.
import sys, subprocess, xml.etree.ElementTree as ET
repo = sys.argv[3] if len(sys.argv) > 3 else "../pcb-desk"
def load(ref):
    root = ET.fromstring(subprocess.check_output(["git", "-C", repo, "show", f"{ref}:pcb/kicad/exports/netlist.xml"]))
    comps = {c.get("ref"): (c.findtext("value"), c.findtext("footprint")) for c in root.iter("comp")}
    nets = {n.get("name"): frozenset((nd.get("ref"), nd.get("pin")) for nd in n.iter("node")) for n in root.iter("net")}
    return comps, nets
a, b = sys.argv[1], sys.argv[2]
ca, na = load(a); cb, nb = load(b)
print(f"{a}: {len(ca)} comps, {len(na)} nets; {b}: {len(cb)} comps, {len(nb)} nets")
for r in sorted(set(ca) | set(cb)):
    if ca.get(r) != cb.get(r): print("COMP", r, ca.get(r), "->", cb.get(r))
sa = {v: k for k, v in na.items()}; sb = {v: k for k, v in nb.items()}
for s in sa.keys() - sb.keys():
    m = s - next((t for t in sb if sa[s] == sb[t]), frozenset())
    print("NET", sa[s], "in", a, "only; nodes not in", b + "'s same-name net:", sorted(m) or "(none: it gained nodes)")
for s in sb.keys() - sa.keys():
    m = s - next((t for t in sa if sb[s] == sa[t]), frozenset())
    print("NET", sb[s], "in", b, "only; nodes added vs", a + "'s same-name net:", sorted(m) or "(none: it lost nodes)")
print("renamed nets:", [(sa[s], sb[s]) for s in sa.keys() & sb.keys() if sa[s] != sb[s]])
