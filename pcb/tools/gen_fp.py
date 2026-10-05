#!/usr/bin/env python3
"""Generate the custom footprints KiCad's library lacks, from the datasheets in pcb/refs (not committed).

Output: pcb/kicad/lib/pcb_custom.pretty/*.kicad_mod
  RM2.kicad_mod            Raspberry Pi Radio Module 2, from rm2-datasheet.pdf Figure 6 and Table 2 (2026-10-04)
  AOTA-B201610S.kicad_mod  Abracon 0806 inductor, from the AOTA-B201610S datasheet land pattern (2026-10-04)
  Fuse_Bourns_MF-MSMF_1812.kicad_mod  Bourns MF-MSMF recommended pad layout (2026-10-04)

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
    Reading of Figure 6 (corrected after AUDIT-3 and HR-P05 part 4): side pads 1.0 wide, 2.0 long in total (1.5 inside,
    0.5 outside), first pad's top on the keep-out line (measured 5.2 mm below the body top on a 400 dpi render of Figure 6; 5.0 by the dimension chain); bottom pads 1.0 wide, 1.8 long (1.3 inside, 0.5 outside), centred
    2.75 + 1.5k from the left edge. Left column pins 1..7 top down, bottom row 8..14 left to right, right column 15..21
    bottom up. Keep-out: 35.5 x 18.5 mm centred on the module, 13.5 mm beyond the antenna edge and
    5.0 mm into the module. VERIFY on the 1:1 print and against the figure before ordering."""
    W, H = 14.5, 16.5
    L, R, T, B = -W / 2, W / 2, -H / 2, H / 2
    pw, pitch, ext = 1.0, 1.5, 0.5
    items = [text("Reference", "U", 0, T - 1.5, "F.SilkS"), text("Value", "RM2", 0, B + 1.5, "F.Fab"),
             text("user", "${REFERENCE}", 0, 0, "F.Fab")]
    # Figure 6 reading agreed with the expert and the auditor (2026-10-04): side pads 2.0 long x 1.0 wide, the first one
    # starting 0.5 mm below the keep-out line (which lies 5.0 mm into the module), 1.5 mm pitch; bottom pads 1.0 wide x 1.8
    # long centred 2.75 mm from the left edge, 1.5 mm pitch; every pad reaches 0.5 mm outside the module edge.
    keepout_y = T + 5.0
    side_len = 2.0
    ys = [keepout_y + pw / 2 + pitch * k for k in range(7)]                # pin 1 at the top: -2.75, ..., +6.25 (first pad's top on the keep-out line)
    for k, y in enumerate(ys):
        items.append(pad(k + 1, L + side_len / 2 - ext, y, side_len, pw))     # x centre -6.75, spans -7.75 .. -5.75 (2.0 total, 0.5 outside)
    bot_len = 1.8
    for k in range(7):
        x = L + 2.75 + pitch * k                                             # -4.50, ..., +4.50
        items.append(pad(8 + k, x, B + ext - bot_len / 2, pw, bot_len))     # y centre 7.85, spans 6.95 .. 8.75
    for k, y in enumerate(reversed(ys)):
        items.append(pad(15 + k, R - side_len / 2 + ext, y, side_len, pw))    # x centre +6.75
    # outlines: fab = module body; silk = body minus the pad sides; courtyard = body + 0.5 mm
    items.append(rect("F.Fab", L, T, R, B))
    items.append(rect("F.SilkS", L, T, R, T + 4.0, 0.12))     # antenna end marked on silk
    items.append(rect("F.CrtYd", L - 0.75, T - 0.5, R + 0.75, B + 0.75, 0.05))   # 0.25 mm beyond the pads' outer edges
    # RF keep-out (RM2 ds 2.4): 35.5 x 18.5 mm, 13.5 mm beyond the antenna edge and 5.0 mm into the module.
    # Drawn on the comments layer AND as a rule area on all copper layers (*.Cu: F, In1, In2, B; placement review 19:02), so the DRC enforces it.
    items.append(rect("Cmts.User", -35.5 / 2, T - 13.5, 35.5 / 2, T + 5.0, 0.15))
    kx0, ky0, kx1, ky1 = -35.5 / 2, T - 13.5, 35.5 / 2, T + 5.0
    items.append(f'\t(zone (net 0) (net_name "") (layers "*.Cu") (uuid "{U()}") (name "RF_KEEP_OUT") (hatch edge 0.5)'
                 f' (connect_pads (clearance 0)) (min_thickness 0.25) (filled_areas_thickness no)'
                 f' (keepout (tracks not_allowed) (vias not_allowed) (pads not_allowed) (copperpour not_allowed) (footprints not_allowed))'
                 f' (placement (enabled no) (sheetname "")) (fill (thermal_gap 0.5) (thermal_bridge_width 0.5))'
                 f' (polygon (pts (xy {kx0:.3f} {ky0:.3f}) (xy {kx1:.3f} {ky0:.3f}) (xy {kx1:.3f} {ky1:.3f}) (xy {kx0:.3f} {ky1:.3f}))))')
    items.append(text("user", "RF KEEP OUT: no copper on any layer (rm2 ds 2.4)", 0, T - 7, "Cmts.User", size=0.8))
    items.append(text("user", "pin 1", L - 2.0, ys[0], "F.SilkS", size=0.6))
    footprint("RM2", "Raspberry Pi Radio Module 2, 21 castellated pads 1.5 mm pitch; drawn from the RM2 datasheet Figure 6 (VERIFY on 1:1 print)", items)


def aota():
    """Abracon AOTA-B201610S: body 2.0 x 1.6 x 1.0 mm; land pattern two pads 0.80 x 1.60 mm, 0.70 mm gap
    (datasheet 'Recommended Land Pattern'). Orientation dot on the OUTPUT end = pad 2 = 1V1 (RP2350 datasheet Figure 28:
    current enters the unmarked end and leaves at the dot; Figure 26: dotted end goes to C_OUT). Pad 1 = VREG_LX.
    Marked on silk and fab so assembly puts the part's dot on pad 2 (auditor evidence 19:06, checked 2026-10-04)."""
    items = [text("Reference", "L", 0, -1.6, "F.SilkS"), text("Value", "AOTA-B201610S", 0, 1.6, "F.Fab"),
             pad(1, -0.75, 0, 0.8, 1.6), pad(2, 0.75, 0, 0.8, 1.6),
             rect("F.Fab", -1.0, -0.8, 1.0, 0.8), rect("F.CrtYd", -1.4, -1.05, 1.4, 1.05, 0.05),
             f'\t(fp_circle (center 0.6 -0.4) (end 0.8 -0.4) (stroke (width 0.05) (type default)) (fill yes) (layer "F.Fab") (uuid "{U()}"))',
             text("user", "DOT=1V1", 0, 0, "F.Fab", size=0.3),
             # no copper pour and no vias under the inductor on the top and inner layers (RP2350 datasheet p.411: cut copper
             # under the inductor; auditor and expert: inner layers too). B.Cu keeps its ground plane, as on the Pico 2.
             # Tracks are allowed so the pads can be reached; route nothing else through this area.
             f'\t(zone (net 0) (net_name "") (layers "F.Cu" "In1.Cu" "In2.Cu") (uuid "{U()}") (name "LX_NO_POUR") (hatch edge 0.3)'
             f' (connect_pads (clearance 0)) (min_thickness 0.25) (filled_areas_thickness no)'
             f' (keepout (tracks allowed) (vias not_allowed) (pads allowed) (copperpour not_allowed) (footprints allowed))'
             f' (placement (enabled no) (sheetname "")) (fill (thermal_gap 0.5) (thermal_bridge_width 0.5))'
             f' (polygon (pts (xy -1.3 -1.0) (xy 1.3 -1.0) (xy 1.3 1.0) (xy -1.3 1.0))))',
             f'\t(fp_circle (center 1.45 -0.9) (end 1.55 -0.9) (stroke (width 0.12) (type default)) (fill yes) (layer "F.SilkS") (uuid "{U()}"))',
             f'\t(fp_line (start -1.0 -1.0) (end 1.0 -1.0) (stroke (width 0.12) (type default)) (layer "F.SilkS") (uuid "{U()}"))',
             f'\t(fp_line (start -1.0 1.0) (end 1.0 1.0) (stroke (width 0.12) (type default)) (layer "F.SilkS") (uuid "{U()}"))']
    footprint("AOTA-B201610S", "Abracon AOTA-B201610S 0806 molded inductor, land pattern from the datasheet; orientation dot = pad 2 (1V1 output end)", items)


def fuse_1812_bourns():
    """Bourns MF-MSMF 1812 (Style 1), recommended pad layout from the MF-MSMF datasheet pp.6-7: two pads 1.5 mm wide
    (along the part) x 3.2 mm tall, 2.7 mm gap between them (inch values 0.059, 0.126, 0.106). Body 4.5 x 3.2 mm.
    Replaces KiCad's generic Fuse_1812 lands (1.125 x 3.4, gap 3.15), AUDIT-3 Appendix A."""
    px = 2.7 / 2 + 1.5 / 2                                   # pad centres at +-2.10
    items = [text("Reference", "F", 0, -2.8, "F.SilkS"), text("Value", "MF-MSMF", 0, 2.8, "F.Fab"),
             pad(1, -px, 0, 1.5, 3.2), pad(2, px, 0, 1.5, 3.2),
             rect("F.Fab", -2.25, -1.6, 2.25, 1.6), rect("F.CrtYd", -px - 1.0, -1.85, px + 1.0, 1.85, 0.05),
             f'\t(fp_line (start -1.0 -1.75) (end 1.0 -1.75) (stroke (width 0.12) (type default)) (layer "F.SilkS") (uuid "{U()}"))',
             f'\t(fp_line (start -1.0 1.75) (end 1.0 1.75) (stroke (width 0.12) (type default)) (layer "F.SilkS") (uuid "{U()}"))']
    footprint("Fuse_Bourns_MF-MSMF_1812", "Bourns MF-MSMF 1812 PTC fuse, recommended pad layout from the Bourns datasheet (VERIFY on 1:1 print)", items)


if __name__ == "__main__":
    OUTDIR.mkdir(parents=True, exist_ok=True)
    rm2()
    aota()
    fuse_1812_bourns()
