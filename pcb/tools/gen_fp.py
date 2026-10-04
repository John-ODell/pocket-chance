#!/usr/bin/env python3
"""Generate the custom footprints KiCad's library lacks, from the datasheets in pcb/refs (not committed).

Output: pcb/kicad/lib/pcb_custom.pretty/*.kicad_mod
  RM2.kicad_mod            Raspberry Pi Radio Module 2, from rm2-datasheet.pdf Figure 6 and Table 2 (2026-10-04)
  AOTA-B201610S.kicad_mod  Abracon 0806 inductor, from the AOTA-B201610S datasheet land pattern (2026-10-04)

Every number below is read from the datasheet drawing and must be checked on the 1:1 paper print (phase 7).
Standard library only.
"""
import pathlib
import uuid

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUTDIR = ROOT / "pcb/kicad/lib/pcb_custom.pretty"


def U():
    return str(uuid.uuid4())


def pad(num, x, y, w, h, shape="roundrect"):
    extra = ' (roundrect_rratio 0.15)' if shape == "roundrect" else ""
    return (f'\t(pad "{num}" smd {shape} (at {x:.3f} {y:.3f}) (size {w:.3f} {h:.3f})'
            f' (layers "F.Cu" "F.Paste" "F.Mask"){extra} (uuid "{U()}"))')


def rect(layer, x0, y0, x1, y1, width=0.1):
    return (f'\t(fp_rect (start {x0:.3f} {y0:.3f}) (end {x1:.3f} {y1:.3f}) (stroke (width {width}) (type default))'
            f' (fill no) (layer "{layer}") (uuid "{U()}"))')


def text(kind, s, x, y, layer, hide=False, size=1.0):
    h = " hide" if hide else ""
    return (f'\t(property "{kind}" "{s}" (at {x:.3f} {y:.3f} 0) (layer "{layer}"){h} (uuid "{U()}")'
            f' (effects (font (size {size} {size}) (thickness 0.15))))') if kind in ("Reference", "Value") else \
           (f'\t(fp_text user "{s}" (at {x:.3f} {y:.3f} 0) (layer "{layer}") (uuid "{U()}")'
            f' (effects (font (size {size} {size}) (thickness 0.15))))')


def footprint(name, descr, items, attr="smd"):
    body = [f'(footprint "{name}" (version 20241229) (generator "gen_fp") (generator_version "9.0") (layer "F.Cu")',
            f'\t(descr "{descr}")', f'\t(attr {attr})'] + items + [")"]
    (OUTDIR / f"{name}.kicad_mod").write_text("\n".join(body) + "\n")
    print("wrote", name)


def rm2():
    """RM2: 14.5 x 16.5 mm module, 21 castellated pads at 1.5 mm pitch (rm2-datasheet.pdf Figure 6, Table 2).
    Origin: module centre. Module top edge at y = -8.25 (antenna end), bottom edge at y = +8.25.
    Reading of Figure 6: pads are 1.0 mm wide along the edge and 2.0 mm long into the module, extended 0.5 mm
    outside the edge (castellation). Left column pins 1..7 from the top down, 0.5 mm clear of the bottom edge;
    bottom row pins 8..14 left to right starting 2.75 mm from the left edge (pad edge); right column pins 15..21
    from the bottom up. Keep-out: 35.5 x 18.5 mm centred on the module, 13.5 mm beyond the antenna edge and
    5.0 mm into the module. VERIFY on the 1:1 print and against the figure before ordering."""
    W, H = 14.5, 16.5
    L, R, T, B = -W / 2, W / 2, -H / 2, H / 2
    pw, pl, ext, pitch = 1.0, 2.0, 0.5, 1.5
    items = [text("Reference", "U", 0, T - 1.5, "F.SilkS"), text("Value", "RM2", 0, B + 1.5, "F.Fab"),
             text("user", "${REFERENCE}", 0, 0, "F.Fab")]
    # left column: 7 pads, last one 0.5 mm above the bottom edge
    ys = [B - 0.5 - pw / 2 - pitch * (6 - k) for k in range(7)]   # k=0 is pin 1 (top)
    for k, y in enumerate(ys):
        items.append(pad(k + 1, L + (pl - ext) / 2, y, pl + ext, pw))
    # bottom row: pins 8..14, first pad edge 2.75 mm from the left edge
    for k in range(7):
        x = L + 2.75 + pw / 2 + pitch * k
        items.append(pad(8 + k, x, B - (pl - ext) / 2, pw, pl + ext))
    # right column: pins 15..21 from the bottom up
    for k, y in enumerate(reversed(ys)):
        items.append(pad(15 + k, R - (pl - ext) / 2, y, pl + ext, pw))
    # outlines: fab = module body; silk = body minus the pad sides; courtyard = body + 0.5 mm
    items.append(rect("F.Fab", L, T, R, B))
    items.append(rect("F.SilkS", L, T, R, T + 4.0, 0.12))     # antenna end marked on silk
    items.append(rect("F.CrtYd", L - 0.5, T - 0.5, R + 0.5, B + 0.5, 0.05))
    # RF keep-out, drawn on the comments layer for the layout to turn into a rule area
    items.append(rect("Cmts.User", -35.5 / 2, T - 13.5, 35.5 / 2, T + 5.0, 0.15))
    items.append(text("user", "RF KEEP OUT: no copper on any layer (rm2 ds 2.4)", 0, T - 7, "Cmts.User", size=0.8))
    items.append(text("user", "pin 1", L - 2.0, ys[0], "F.SilkS", size=0.6))
    footprint("RM2", "Raspberry Pi Radio Module 2, 21 castellated pads 1.5 mm pitch; drawn from the RM2 datasheet Figure 6 (VERIFY on 1:1 print)", items)


def aota():
    """Abracon AOTA-B201610S: body 2.0 x 1.6 x 1.0 mm; land pattern two pads 0.80 x 1.60 mm, 0.70 mm gap
    (datasheet 'Recommended Land Pattern'). Polarity dot on pin 1 side (design guide 2.1): marked on silk."""
    items = [text("Reference", "L", 0, -1.6, "F.SilkS"), text("Value", "AOTA-B201610S", 0, 1.6, "F.Fab"),
             pad(1, -0.75, 0, 0.8, 1.6), pad(2, 0.75, 0, 0.8, 1.6),
             rect("F.Fab", -1.0, -0.8, 1.0, 0.8), rect("F.CrtYd", -1.4, -1.05, 1.4, 1.05, 0.05),
             f'\t(fp_circle (center -1.45 -0.9) (end -1.35 -0.9) (stroke (width 0.12) (type default)) (fill yes) (layer "F.SilkS") (uuid "{U()}"))',
             f'\t(fp_line (start -1.0 -1.0) (end 1.0 -1.0) (stroke (width 0.12) (type default)) (layer "F.SilkS") (uuid "{U()}"))',
             f'\t(fp_line (start -1.0 1.0) (end 1.0 1.0) (stroke (width 0.12) (type default)) (layer "F.SilkS") (uuid "{U()}"))']
    footprint("AOTA-B201610S", "Abracon AOTA-B201610S 0806 molded inductor, land pattern from the datasheet; polarity dot = pin 1 side", items)


if __name__ == "__main__":
    OUTDIR.mkdir(parents=True, exist_ok=True)
    rm2()
    aota()
