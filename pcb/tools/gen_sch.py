#!/usr/bin/env python3
"""Generate the spin-1 schematic (pcb/kicad/pocket-chance-board.kicad_sch) from a connection table.

Why a generator: the PCB maker cannot drive KiCad's window, so the design is written as data
(components, values, footprints, pin-to-net connections) and turned into KiCad's own file
format. KiCad opens it like any hand-drawn schematic, and kicad-cli runs ERC on it.

Style: every pin carries a global label with its net name ("label-based" schematic), power
nets use KiCad power symbols. Symbols come from KiCad's bundled libraries; the two parts
KiCad lacks (the RM2 radio module and the FS8205A MOSFET pair) are drawn here from their
datasheets (pcb/refs/, not committed).

Run:  python3 pcb/tools/gen_sch.py   (from the repo root); then kicad-cli sch erc ...
Standard library only.
"""
import copy
import pathlib
import sys
import uuid

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import sexp
from sexp import QStr as Q

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "pcb/kicad/pocket-chance-board.kicad_sch"
PRO = ROOT / "pcb/kicad/pocket-chance-board.kicad_pro"
LIBDIR = pathlib.Path("/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols")
PROJECT = "pocket-chance-board"

# ----------------------------------------------------------------------------- libraries
_libcache = {}


def lib(name):
    if name not in _libcache:
        tree = sexp.parse((LIBDIR / f"{name}.kicad_sym").read_text())[0]
        _libcache[name] = {str(s[1]): s for s in sexp.find_all(tree, "symbol")}
    return _libcache[name]


def flatten(libname, symname):
    """Return a schematic-ready lib_symbols entry named 'Lib:Name', with `extends` resolved."""
    syms = lib(libname)
    child = syms[symname]
    ext = sexp.find(child, "extends")
    if ext:
        parent = flatten(libname, str(ext[1]))  # already renamed to Lib:Parent; rename again below
        node = copy.deepcopy(parent)
        pname = str(ext[1])
        # child properties override the parent's
        cprops = {str(p[1]): p for p in sexp.find_all(child, "property")}
        for i, x in enumerate(node):
            if isinstance(x, list) and x and x[0] == "property" and str(x[1]) in cprops:
                node[i] = copy.deepcopy(cprops[str(x[1])])
        have = {str(p[1]) for p in sexp.find_all(node, "property")}
        for k, p in cprops.items():
            if k not in have:
                node.append(copy.deepcopy(p))
        # rename the unit sub-symbols Parent_u_s -> Child_u_s
        for x in node:
            if isinstance(x, list) and x and x[0] == "symbol":
                x[1] = Q(str(x[1]).replace(pname, symname, 1))
    else:
        node = copy.deepcopy(child)
    node[1] = Q(f"{libname}:{symname}")
    # the file is written in the KiCad 9 format (version 20250114); KiCad 10 libraries say
    # "(power global)", which a version-9 reader does not recognise, so write the older "(power)"
    for i, x in enumerate(node):
        if isinstance(x, list) and x and x[0] == "power":
            node[i] = ["power"]
    return node


def custom_symbol(libname, symname, pins, width=20.32, ref_prefix="U", footprint=""):
    """A plain rectangular symbol. pins: list of (number, name, etype, side, index).
    side in L/R/T/B; index counts 2.54 mm steps from the top-left (L/R) or left (T/B)."""
    half = width / 2
    nL = max([i for n, nm, t, s, i in pins if s == "L"] + [0]) + 1
    nR = max([i for n, nm, t, s, i in pins if s == "R"] + [0]) + 1
    height = max(nL, nR) * 2.54 + 2.54
    top = height / 2
    body = [["symbol", Q(f"{symname}_0_1"),
             ["rectangle", ["start", -half, top], ["end", half, -top],
              ["stroke", ["width", 0.254], ["type", "default"]], ["fill", ["type", "background"]]]]]
    unit = ["symbol", Q(f"{symname}_1_1")]
    for num, name, etype, side, idx in pins:
        if side == "L":
            at = [-half - 3.81, top - 2.54 * (idx + 1), 0]
        elif side == "R":
            at = [half + 3.81, top - 2.54 * (idx + 1), 180]
        elif side == "T":
            at = [-half + 2.54 * (idx + 1), top + 3.81, 270]
        else:
            at = [-half + 2.54 * (idx + 1), -top - 3.81, 90]
        unit.append(["pin", etype, "line", ["at"] + at, ["length", 3.81],
                     ["name", Q(name), ["effects", ["font", ["size", 1.27, 1.27]]]],
                     ["number", Q(str(num)), ["effects", ["font", ["size", 1.27, 1.27]]]]])
    node = ["symbol", Q(f"{libname}:{symname}"),
            ["exclude_from_sim", "no"], ["in_bom", "yes"], ["on_board", "yes"],
            ["property", Q("Reference"), Q(ref_prefix), ["at", 0, top + 2.54, 0],
             ["effects", ["font", ["size", 1.27, 1.27]]]],
            ["property", Q("Value"), Q(symname), ["at", 0, -top - 2.54, 0],
             ["effects", ["font", ["size", 1.27, 1.27]]]],
            ["property", Q("Footprint"), Q(footprint), ["at", 0, 0, 0],
             ["effects", ["font", ["size", 1.27, 1.27]], "hide"]],
            ["property", Q("Datasheet"), Q(""), ["at", 0, 0, 0],
             ["effects", ["font", ["size", 1.27, 1.27]], "hide"]],
            body[0], unit]
    return node


def pin_points(symnode):
    """{pin_number: (x, y, rot, etype)} in symbol coordinates (y up), over all units."""
    out = {}
    for u in sexp.find_all(symnode, "symbol"):
        for p in sexp.find_all(u, "pin"):
            at = sexp.find(p, "at")
            num = str(sexp.find(p, "number")[1])
            out[num] = (float(at[1]), float(at[2]), int(at[3]), p[1])
    return out


# ----------------------------------------------------------------------------- the design
# Each component: ref, (lib, symbol) or custom node, value, footprint, position (x, y) on the
# sheet in mm, and pins -> net. Nets named "GND", "+3V3", "VBUS" become power symbols.
# "NC" marks a no-connect flag. A pin not listed is left open (ERC will tell us).

RM2_PINS = [  # from pcb/refs/rm2-datasheet.pdf, Table 2 (2026-10-04)
    (1, "GND", "power_in", "L", 0), (2, "NC", "no_connect", "L", 1), (3, "SCLK", "input", "L", 2),
    (4, "GND", "passive", "L", 3), (5, "DATA_IN", "input", "L", 4), (6, "DATA_OUT", "output", "L", 5),
    (7, "GND", "passive", "L", 6), (8, "WL_GPIO0", "bidirectional", "L", 7), (9, "CS", "input", "L", 8),
    (10, "nIRQ", "output", "L", 9), (11, "GND", "passive", "L", 10),
    (12, "WL_ON", "input", "R", 0), (13, "BT_ON", "input", "R", 1), (14, "VDDIO", "power_in", "R", 2),
    (15, "GND", "passive", "R", 3), (16, "VIN", "power_in", "R", 4), (17, "WL_GPIO2", "bidirectional", "R", 5),
    (18, "WL_GPIO1", "bidirectional", "R", 6), (19, "NC", "no_connect", "R", 7), (20, "NC", "no_connect", "R", 8),
    (21, "GND", "passive", "R", 9),
]
# FS8205A dual N-MOSFET, common-drain protection pair. Pin assignment read from the Fortune datasheet
# (pcb/refs/parts/fs8205a.pdf, section 4, TSSOP-8 top view, 2026-10-04): 1 D12, 2 S1, 3 S1, 4 G1, 5 G2, 6 S2, 7 S2, 8 D12.
FS8205A_PINS = [
    (1, "D12", "passive", "L", 0), (2, "S1", "passive", "L", 1), (3, "S1", "passive", "L", 2), (4, "G1", "input", "L", 3),
    (5, "G2", "input", "R", 3), (6, "S2", "passive", "R", 2), (7, "S2", "passive", "R", 1), (8, "D12", "passive", "R", 0),
]

CUSTOM = {
    ("pcb_custom", "RM2"): custom_symbol("pcb_custom", "RM2", RM2_PINS, width=25.4, footprint="pcb_custom:RM2"),
    ("pcb_custom", "FS8205A"): custom_symbol("pcb_custom", "FS8205A", FS8205A_PINS, width=15.24, ref_prefix="Q",
                                             footprint="Package_SO:TSSOP-8_4.4x3mm_P0.65mm"),
}

R = ("Device", "R"); C = ("Device", "C"); L = ("Device", "L")
R0402 = "Resistor_SMD:R_0402_1005Metric"; C0402 = "Capacitor_SMD:C_0402_1005Metric"
C0603 = "Capacitor_SMD:C_0603_1608Metric"; C0805 = "Capacitor_SMD:C_0805_2012Metric"
SWP = ("Switch", "SW_Push"); PTS645 = "Button_Switch_SMD:SW_SPST_PTS645Sx43SMTR92"
TP = ("Connector", "TestPoint"); TPFP = "TestPoint:TestPoint_Pad_D1.5mm"

comps = []


def add(ref, sym, value, fp, pos, pins, dnp=False):
    comps.append(dict(ref=ref, sym=sym, value=value, fp=fp, pos=pos, pins=pins, dnp=dnp))


# ---- Block 1: core -----------------------------------------------------------------
X0, Y0 = 60, 80
add("U1", ("MCU_RaspberryPi", "RP2350A"), "RP2350A", "Package_DFN_QFN:QFN-60-1EP_7x7mm_P0.4mm_EP3.4x3.4mm", (X0, Y0), {
    "1": "+3V3", "53": "+3V3", "54": "+3V3", "44": "ADC_AVDD", "6": "1V1", "46": "VREG_AVDD", "47": "GND",
    "48": "VREG_LX", "49": "+3V3", "50": "1V1", "61": "GND",
    "21": "XIN", "22": "XOUT", "24": "SWCLK", "25": "SWDIO", "26": "RUN",
    "51": "USB_DM_R", "52": "USB_DP_R",
    "55": "QSPI_SD3", "56": "QSPI_SCLK", "57": "QSPI_SD0", "58": "QSPI_SD2", "59": "QSPI_SD1", "60": "QSPI_SS",
    "2": "PSRAM_CS", "3": "EXP_GP1", "4": "JOY_UP", "5": "JOY_PRESS", "7": "SD_MISO", "8": "SD_CS", "9": "SD_SCK",
    "10": "SD_MOSI", "12": "LCD_DC", "13": "LCD_CS", "14": "LCD_SCK", "15": "LCD_MOSI", "16": "LCD_RST", "17": "LCD_BL",
    "18": "IMU_INT", "19": "BTN_A", "27": "JOY_LEFT", "28": "BTN_B", "29": "JOY_DOWN", "31": "BTN_X", "32": "JOY_RIGHT",
    "33": "BTN_Y", "34": "AUDIO_PWM", "35": "WL_REG_ON", "36": "WL_DATA", "37": "WL_CS", "40": "SDA", "41": "SCL",
    "42": "VBAT_SENSE", "43": "WL_CLK",
})
# decoupling: one 100 nF per power pin (IOVDD x6, DVDD x3, one shared for 53/54), per the design guide 2.2.1
x = 130
for i in range(10):
    add(f"C{i+1}", C, "100nF", C0402, (x + 12 * (i % 5), 60 + 20 * (i // 5)), {"1": "+3V3" if i < 7 else "1V1", "2": "GND"})
add("C11", C, "10uF", C0603, (190, 60), {"1": "+3V3", "2": "GND"})          # 3.3 V bulk near U1
add("C12", C, "2.2uF", C0603, (190, 80), {"1": "ADC_AVDD", "2": "GND"})     # ADC supply filter (Pico 2 W: 201 R into 2.2 uF)
add("R1", R, "200R", R0402, (205, 80), {"1": "+3V3", "2": "ADC_AVDD"})
# on-chip 1.1 V switching regulator: design guide 2.1 (exact parts)
add("L1", L, "3.3uH AOTA-B201610S3R3-101-T", "pcb_custom:AOTA-B201610S", (130, 110), {"1": "VREG_LX", "2": "1V1"})   # footprint from the Abracon land pattern (gen_fp.py)
add("C13", C, "4.7uF", C0402, (145, 110), {"1": "+3V3", "2": "GND"})        # C6 regulator input
add("C14", C, "4.7uF", C0402, (160, 110), {"1": "1V1", "2": "GND"})         # C7 regulator output
add("R2", R, "33R", R0402, (175, 110), {"1": "+3V3", "2": "VREG_AVDD"})     # R3 AVDD filter
add("C15", C, "4.7uF", C0402, (190, 110), {"1": "VREG_AVDD", "2": "GND"})   # C9
add("C40", C, "4.7uF", C0402, (205, 110), {"1": "1V1", "2": "GND"})        # RP2350 ds: second 4.7 uF on the VOUT net at DVDD pin 23, not near LX/COUT (AUDIT-2 #11)
# crystal: design guide 4.1 (ABM8-272-T3, 15 pF, 1 k series)
add("Y1", ("Device", "Crystal_GND24"), "12MHz ABM8-272-T3", "Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm", (130, 140),
    {"1": "XIN", "3": "XOUT_X", "2": "GND", "4": "GND"})
add("R3", R, "1k", R0402, (150, 140), {"1": "XOUT", "2": "XOUT_X"})
add("C16", C, "15pF", C0402, (165, 140), {"1": "XIN", "2": "GND"})
add("C17", C, "15pF", C0402, (180, 140), {"1": "XOUT_X", "2": "GND"})
# flash and PSRAM: design guide 3.1, 3.2
add("U2", ("Memory_Flash", "W25Q128JVS"), "W25Q128JVSIQ", "Package_SO:SOIC-8_5.3x5.3mm_P1.27mm", (130, 180), {
    "1": "QSPI_SS", "2": "QSPI_SD1", "3": "QSPI_SD2", "4": "GND", "5": "QSPI_SD0", "6": "QSPI_SCLK", "7": "QSPI_SD3", "8": "+3V3"})
add("C18", C, "100nF", C0402, (160, 180), {"1": "+3V3", "2": "GND"})
add("R4", R, "10k", R0402, (175, 180), {"1": "+3V3", "2": "QSPI_SS"})       # optional pull-up (guide R5)
add("R5", R, "1k", R0402, (190, 180), {"1": "QSPI_SS", "2": "BOOT_SW"})     # guide R6, to the BOOT button
add("SW1", SWP, "BOOT", PTS645, (205, 180), {"1": "BOOT_SW", "2": "GND"})
add("U3", ("Memory_RAM", "APS6404L-3SQRx-SN"), "APS6404L-3SQR-SN", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", (130, 215), {
    "1": "PSRAM_CS", "2": "QSPI_SD1", "3": "QSPI_SD2", "4": "GND", "5": "QSPI_SD0", "6": "QSPI_SCLK", "7": "QSPI_SD3", "8": "+3V3"})
add("C19", C, "100nF", C0402, (160, 215), {"1": "+3V3", "2": "GND"})
add("R6", R, "10k", R0402, (175, 215), {"1": "+3V3", "2": "PSRAM_CS"})      # guide R13: pull-up needed on CS1
# RUN, reset button, SWD
add("R7", R, "10k", R0402, (130, 250), {"1": "+3V3", "2": "RUN"})
add("SW2", SWP, "RESET", PTS645, (150, 250), {"1": "RUN", "2": "GND"})
add("J1", ("Connector", "Conn_ARM_JTAG_SWD_10"), "SWD", "Connector_PinHeader_1.27mm:PinHeader_2x05_P1.27mm_Vertical_SMD",
    (190, 250), {"1": "+3V3", "2": "SWDIO", "3": "GND", "4": "SWCLK", "5": "GND", "6": "NC", "7": "NC", "8": "NC", "9": "GND", "10": "RUN"})
# test points (HR-P03)
for i, net in enumerate(["VBUS", "VSYS", "+3V3", "1V1", "GND", "GND", "BAT+", "RUN"]):
    add(f"TP{i+1}", TP, net, TPFP, (130 + 12 * i, 285), {"1": net})

# ---- Block 2: USB --------------------------------------------------------------------
add("J2", ("Connector", "USB_C_Receptacle_USB2.0_16P"), "USB4085-GF-A", "Connector_USB:USB_C_Receptacle_GCT_USB4085", (300, 80), {
    "A4": "VBUS", "A9": "VBUS", "B4": "VBUS", "B9": "VBUS", "A5": "CC1", "B5": "CC2",
    "A6": "USB_DP", "B6": "USB_DP", "A7": "USB_DM", "B7": "USB_DM", "A8": "NC", "B8": "NC",
    "A1": "GND", "A12": "GND", "B1": "GND", "B12": "GND", "SH": "GND"})
add("R8", R, "5.1k", R0402, (340, 60), {"1": "CC1", "2": "GND"})
add("R9", R, "5.1k", R0402, (355, 60), {"1": "CC2", "2": "GND"})
add("R10", R, "27R", R0402, (340, 85), {"1": "USB_DP", "2": "USB_DP_R"})      # guide 5.1, close to the chip
add("R11", R, "27R", R0402, (355, 85), {"1": "USB_DM", "2": "USB_DM_R"})
add("U4", ("Power_Protection", "USBLC6-2SC6"), "USBLC6-2SC6", "Package_TO_SOT_SMD:SOT-23-6", (345, 115),
    {"1": "USB_DP", "6": "USB_DP", "3": "USB_DM", "4": "USB_DM", "5": "VBUS", "2": "GND"})

# ---- Block 3: power (PCB-001, HR-P03) ---------------------------------------------------
add("U5", ("Battery_Management", "BQ24074RGT"), "BQ24074RGTR", "Package_DFN_QFN:VQFN-16-1EP_3x3mm_P0.5mm_EP1.68x1.68mm_ThermalVias", (300, 180), {
    "13": "VBUS", "10": "VSYS", "11": "VSYS", "2": "BAT+", "3": "BAT+", "1": "TS", "4": "GND",
    "6": "CHG_EN1", "5": "GND", "7": "NC", "9": "CHG_STAT", "12": "ILIM", "14": "TMR", "15": "NC", "16": "ISET", "8": "GND", "17": "GND"})
add("C20", C, "1uF", C0603, (340, 160), {"1": "VBUS", "2": "GND"})
add("C21", C, "10uF", C0603, (355, 160), {"1": "VSYS", "2": "GND"})
add("C22", C, "10uF", C0603, (370, 160), {"1": "BAT+", "2": "GND"})
add("R12", R, "10k", R0402, (340, 185), {"1": "TS", "2": "GND"})            # BQ24074 ds Table 7-1: "connect a 10-kΩ fixed resistor from TS to VSS" when TS is unused
add("R13", R, "10k", R0402, (355, 185), {"1": "VBUS", "2": "CHG_EN1"})      # BQ24074 ds Table 7-2: EN2=0, EN1=1 = USB500 (500 mA input limit); EN pins have ~285k internal pull-downs
add("R14", R, "1.8k", R0402, (370, 185), {"1": "ISET", "2": "GND"})         # I_CHG = K_ISET/R_ISET, K_ISET 890 AΩ typ (797-975): 443-542 mA. Assumed cell: protected pouch >= 1000 mAh rated >= 0.5 C. 3.6k for 500 mAh (AUDIT-2 #7)
add("R15", R, "3.0k DNP", R0402, (340, 210), {"1": "ILIM", "2": "GND"}, dnp=True)   # NOT FITTED: the active limit is USB500 (EN2=0, EN1=1); ILIM only counts with EN2 high (AUDIT-2 #13)
add("R16", R, "47k", R0402, (355, 210), {"1": "TMR", "2": "GND"})           # ds: 18k to 72k programs the timers; t_MAXCHG = 10 x R x K_TMR(48 s/kΩ) = about 6.3 h
add("R18", R, "1k", R0402, (340, 235), {"1": "VSYS", "2": "CHG_LED"})
add("D1", ("Device", "LED"), "CHG", "LED_SMD:LED_0603_1608Metric", (355, 235), {"2": "CHG_LED", "1": "CHG_STAT"})
# 3.3 V buck-boost
add("U6", ("Regulator_Switching", "TPS63001"), "TPS63001DRCR", "Package_SON:Texas_DRC0010J_ThermalVias", (300, 290), {
    "5": "VSYS", "8": "VSYS", "6": "PWR_EN", "7": "GND", "4": "BB_L1", "2": "BB_L2", "1": "+3V3", "10": "+3V3",
    "3": "GND", "11": "GND", "9": "GND"})
add("L2", L, "2.2uH ASPIAIG-F4020-2R2M", "Inductor_SMD:L_Abracon_ASPIAIG-F4020", (340, 270), {"1": "BB_L1", "2": "BB_L2"})   # TPS63001 ds: 2.2 uH; Abracon 4x4x2 mm shielded, Isat and DCR to confirm from its datasheet (AUDIT-2 #10)
add("C23", C, "10uF 16V X5R", C0805, (355, 270), {"1": "VSYS", "2": "GND"})
add("C24", C, "100nF", C0402, (370, 270), {"1": "VSYS", "2": "GND"})        # VINA
add("C25", C, "10uF 10V X5R", C0805, (385, 270), {"1": "+3V3", "2": "GND"})
add("C26", C, "10uF 10V X5R", C0805, (400, 270), {"1": "+3V3", "2": "GND"})
add("SW3", ("Switch", "SW_SPDT"), "POWER PCM12", "Button_Switch_SMD:SW_SPDT_PCM12", (340, 300),
    {"2": "PWR_EN", "1": "VSYS", "3": "GND"})
add("R19", R, "100k", R0402, (360, 300), {"1": "PWR_EN", "2": "GND"})       # off with no switch fitted (HR-033)
# protection on the negative lead (HR-P03), both cells through one circuit
add("U7", ("Battery_Management", "DW01A"), "DW01A", "Package_TO_SOT_SMD:SOT-23-6", (300, 350),
    {"5": "PROT_VCC", "6": "BAT-", "2": "PROT_CS", "1": "PROT_OD", "3": "PROT_OC", "4": "NC"})
add("R20", R, "100R", R0402, (340, 335), {"1": "BAT+", "2": "PROT_VCC"})
add("C27", C, "100nF", C0402, (355, 335), {"1": "PROT_VCC", "2": "BAT-"})
add("R21", R, "1k", R0402, (370, 335), {"1": "PROT_CS", "2": "GND"})
add("Q1", ("pcb_custom", "FS8205A"), "FS8205A", "Package_SO:TSSOP-8_4.4x3mm_P0.65mm", (340, 365),
    {"1": "FET_D", "8": "FET_D", "2": "BAT-", "3": "BAT-", "4": "PROT_OD", "5": "PROT_OC", "6": "GND", "7": "GND"})
# S1 = cell negative (BAT-), gate 1 from DW01A OD (discharge control); S2 = board ground, gate 2 from OC (charge control);
# the common drain D12 is internal, net FET_D is only the two package pins tied together.
# one protected LiPo pouch cell on a JST-PH socket (owner's choice 2026-10-04, no 18650 holder).
# Reverse-polarity guard: P-MOSFET in the positive lead (body diode conducts at power-up, FET then turns on;
# a reversed cell holds it off). Drain to the cell, source to BAT+, gate to the cell's negative.  VERIFY pinout.
# AUDIT-2 findings 7/8: a 3-pin JST-PH socket; a plain 2-wire cell uses pins 1-2, a cell with a thermistor lead adds pin 3 to
# TS. R12 (10 k fixed on TS) is FITTED by default, which bypasses the cell temperature check: the design then relies on the
# cell's own protection board and the charger's junction-temperature regulation. With an NTC cell, remove R12. PCB-001 states
# the assumed cell (protected 1000 mAh+ pouch, 0.5 C charge, 0 to 45 C charging) and the owner warning.
add("J3", ("Connector", "Conn_01x03_Socket"), "LiPo JST-PH 2.0mm (1 = + RED, 2 = -, 3 = NTC)", "Connector_JST:JST_PH_S3B-PH-SM4-TB_1x03-1MP_P2.00mm_Horizontal",
    (300, 400), {"1": "CELL_P", "2": "BAT-", "3": "TS"})
add("Q2", ("Transistor_FET", "AO3401A"), "AO3401A", "Package_TO_SOT_SMD:SOT-23", (340, 400),
    {"1": "BAT-", "2": "CELL_G", "3": "CELL_P"})   # 1 G = cell negative, 2 S = board side (BAT+ via R22), 3 D = cell positive
# AUDIT-2 finding 1 (fixed): the P-FET's body diode conducts drain -> source, i.e. from the cell's + into the board.
# Correct cell: the diode conducts at power-up, then Vgs = -Vcell turns the channel on (about 25 mV drop at 0.5 A);
#   charging current from the BQ24074 BAT pin flows board -> cell through the ON channel. Reversed cell: the diode is
#   reverse-biased, Vgs is positive so the channel stays off, and the cell's other lead (on BAT-) has no return path
#   because the DW01A is unpowered and the FS8205A pair is off: no current in either direction, USB present or not.
add("R22", R, "0R", "Resistor_SMD:R_0603_1608Metric", (395, 400), {"1": "CELL_G", "2": "BAT+"})   # ammeter link (HR-P03)
# battery voltage divider to GP28 (HR-P01: >= 100k total)
# AUDIT-2 finding 2 (fixed): the divider is connected only while the 3.3 V rail is up. Q3 (N-FET, gate on +3V3) pulls the
# P-FET's gate low; with the board off, R39 holds Q4's gate at BAT+, Q4 is off, and R24 holds the ADC pin at 0 V, so GPIO28
# never sees voltage with IOVDD at 0 V (RP2350 ds: IO limit IOVDD + 0.5 V). Same idea as the Pico W's WL_CS-gated VSYS divider.
add("Q4", ("Transistor_FET", "AO3401A"), "AO3401A", "Package_TO_SOT_SMD:SOT-23", (300, 455), {"1": "DIV_PG", "2": "BAT+", "3": "DIV_TOP"})
add("R39", R, "100k", R0402, (315, 455), {"1": "BAT+", "2": "DIV_PG"})
add("Q3", ("Transistor_FET", "2N7002"), "2N7002", "Package_TO_SOT_SMD:SOT-23", (330, 455), {"1": "+3V3", "2": "GND", "3": "DIV_PG"})
add("R23", R, "100k", R0402, (300, 430), {"1": "DIV_TOP", "2": "VBAT_SENSE"})
add("R24", R, "100k", R0402, (315, 430), {"1": "VBAT_SENSE", "2": "GND"})
add("C28", C, "100nF", C0402, (330, 430), {"1": "VBAT_SENSE", "2": "GND"})

# ---- Block 4: screen and input ------------------------------------------------------------
# Waveshare 1.54inch LCD Module: "PH2.0 8PIN interface" (wiki, read 2026-10-04): a JST-PH 2.0 mm cable, pin order
# VCC, GND, DIN, CLK, CS, DC, RST, BL. 3.3 V supply and logic.
add("J4", ("Connector", "Conn_01x08_Socket"), "LCD 1.54in ST7789 module, JST-PH 8-pin", "Connector_JST:JST_PH_S8B-PH-SM4-TB_1x08-1MP_P2.00mm_Horizontal",
    (480, 80), {"1": "+3V3", "2": "GND", "3": "LCD_MOSI", "4": "LCD_SCK", "5": "LCD_CS", "6": "LCD_DC", "7": "LCD_RST", "8": "LCD_BL"})
# game buttons: John asked for about 10 mm; tactile switches come in 6 and 12 mm standard sizes, so 12 mm it is
# (C&K PTS125, 12 x 12 mm surface-mount; KiCad footprint), fallback XKB TS-1187A (same size, cheaper), see PARTS.md
PTS125 = "Button_Switch_SMD:SW_Push_1P1T_NO_CK_PTS125Sx43SMTR"
for i, (ref, net) in enumerate([("SW4", "BTN_A"), ("SW5", "BTN_B"), ("SW6", "BTN_X"), ("SW7", "BTN_Y")]):
    add(ref, SWP, net[4:] + " PTS125SM43SMTR2LFS", PTS125, (480 + 20 * i, 130), {"1": net, "2": "GND"})
# direction pad: five standard 6 mm tactile switches (PTS645) instead of a 5-way joystick part, because Alps serves
# no drawing to scripts and John accepts buttons for the joystick; zero custom footprints (PARTS.md fallback row)
for i, (ref, net) in enumerate([("SW8", "JOY_UP"), ("SW9", "JOY_DOWN"), ("SW10", "JOY_LEFT"), ("SW11", "JOY_RIGHT"), ("SW12", "JOY_PRESS")]):
    add(ref, SWP, "DPAD " + net[4:] + " PTS645SM43SMTR92", PTS645, (480 + 20 * i, 155), {"1": net, "2": "GND"})

# ---- Block 5: audio --------------------------------------------------------------------
# PAM8302A ds ordering table: PAM8302AASCR = MSOP-8, PAM8302AADCR = SO-8. SO-8 chosen (larger, easier to inspect).
add("U8", ("Amplifier_Audio", "PAM8302AAD"), "PAM8302AADCR", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", (480, 220), {
    "1": "AMP_SD", "2": "NC", "3": "AUDIO_INP", "4": "AUDIO_INN", "5": "SPK+", "8": "SPK-", "6": "+3V3", "7": "GND"})
add("R44", R, "47k", R0402, (595, 200), {"1": "+3V3", "2": "AMP_SD"})       # SD released about 30 ms after 3.3 V (ds: 1 to 100 ms) (AUDIT-2 #12)
add("C42", C, "1uF", C0603, (610, 200), {"1": "AMP_SD", "2": "GND"})
add("C41", C, "1uF", C0603, (625, 200), {"1": "+3V3", "2": "GND"})        # local 1 uF at the amplifier VDD, next to C32 10 uF (ds p.8)
add("R25", R, "1k", R0402, (520, 200), {"1": "AUDIO_PWM", "2": "AUDIO_FILT"})
add("C29", C, "10nF", C0402, (535, 200), {"1": "AUDIO_FILT", "2": "GND"})
add("C30", C, "1uF", C0603, (550, 200), {"1": "AUDIO_FILT", "2": "AUDIO_INP"})
add("C31", C, "1uF", C0603, (565, 200), {"1": "GND", "2": "AUDIO_INN"})
add("C32", C, "10uF", C0603, (580, 200), {"1": "+3V3", "2": "GND"})
add("J5", ("Connector", "Conn_01x02_Socket"), "Speaker JST-PH", "Connector_JST:JST_PH_S2B-PH-SM4-TB_1x02-1MP_P2.00mm_Horizontal",
    (520, 230), {"1": "SPK+", "2": "SPK-"})

# ---- Block 6: microSD -------------------------------------------------------------------
add("J6", ("Connector", "Micro_SD_Card"), "microSD Molex 104031-0811", "Connector_Card:microSD_HC_Molex_104031-0811", (480, 300), {
    "1": "SD_DAT2", "2": "SD_CS", "3": "SD_MOSI", "4": "+3V3", "5": "SD_SCK", "6": "GND", "7": "SD_MISO", "8": "SD_DAT1", "SH": "GND"})
for i, net in enumerate(["SD_DAT2", "SD_CS", "SD_MOSI", "SD_MISO", "SD_DAT1"]):
    add(f"R{26+i}", R, "10k", R0402, (530 + 14 * i, 285), {"1": "+3V3", "2": net})
add("C33", C, "10uF", C0603, (530, 315), {"1": "+3V3", "2": "GND"})
add("C34", C, "100nF", C0402, (545, 315), {"1": "+3V3", "2": "GND"})

# ---- Block 7: sensors and connectors ---------------------------------------------------
add("U9", ("Timer_RTC", "DS3231MZ"), "DS3231MZ+", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", (480, 380), {
    "2": "+3V3", "5": "GND", "6": "RTC_VBAT", "7": "SDA", "8": "SCL", "3": "RTC_INT", "4": "NC", "1": "NC"})
add("C35", C, "100nF", C0402, (520, 365), {"1": "+3V3", "2": "GND"})
add("BT2", ("Device", "Battery_Cell"), "CR1220", "Battery:BatteryHolder_Keystone_3001_1x12mm", (535, 380), {"1": "RTC_VBAT", "2": "GND"})
add("R42", R, "10k", R0402, (575, 365), {"1": "+3V3", "2": "RTC_INT"})      # DS3231M INT/SQW is open-drain (AUDIT-2 #9)
add("R43", R, "1k", R0402, (590, 365), {"1": "RTC_INT", "2": "RTC_INT_R"})  # limits contention to 3 mA if the IMU is still push-pull when JP2 is closed
add("JP2", ("Jumper", "SolderJumper_2_Open"), "RTC INT to GP14 (open; close only after firmware sets IMU INT1 open-drain, active-low)", "Jumper:SolderJumper-2_P1.3mm_Open_Pad1.0x1.5mm", (560, 380),
    {"1": "RTC_INT_R", "2": "IMU_INT"})
add("U10", ("Sensor_Motion", "LSM6DSM"), "LSM6DSOXTR", "Package_LGA:LGA-14_3x2.5mm_P0.5mm_LayoutBorder3x4y", (480, 440), {
    "1": "GND", "2": "GND", "3": "GND", "4": "IMU_INT", "5": "+3V3", "6": "GND", "7": "GND", "8": "+3V3", "9": "NC",
    "10": "NC", "11": "NC", "12": "+3V3", "13": "SCL", "14": "SDA"})
# LSM6DSOX ds (pcb/refs/parts/lsm6dsox.pdf, pin table, 2026-10-04): pin map identical to KiCad's LSM6DSM symbol;
# SDx/SCx "connect to VDDIO or GND" (GND here), OCS_Aux "leave unconnected", SDO_Aux "connect to VDDIO or leave
# unconnected", CS high = I2C mode, SA0 low = address 1101010b (0x6A). Package LGA-14L 2.5 x 3.0 x 0.83 mm.
add("C36", C, "100nF", C0402, (520, 430), {"1": "+3V3", "2": "GND"})
add("C37", C, "100nF", C0402, (535, 430), {"1": "+3V3", "2": "GND"})
add("R31", R, "4.7k", R0402, (555, 430), {"1": "+3V3", "2": "SDA"})
add("R32", R, "4.7k", R0402, (570, 430), {"1": "+3V3", "2": "SCL"})
add("J7", ("Connector", "Conn_01x04_Socket"), "STEMMA QT", "Connector_JST:JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal",
    (520, 465), {"1": "GND", "2": "+3V3", "3": "SDA", "4": "SCL"})
add("J8", ("Connector", "Conn_01x06_Pin"), "Expansion (6 = VBAT_SENSE ADC node, not free GPIO)", "Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical",
    (560, 465), {"1": "+3V3", "2": "GND", "3": "SDA", "4": "SCL", "5": "EXP_GP1", "6": "VBAT_SENSE"})

# ---- Block 8: wireless (RM2 datasheet Table 2; Pico 2 W pins) ------------------------------
add("U11", ("pcb_custom", "RM2"), "RM2", "pcb_custom:RM2", (660, 120), {
    "1": "GND", "4": "GND", "7": "GND", "11": "GND", "15": "GND", "21": "GND", "2": "NC", "19": "NC", "20": "NC",
    "3": "WL_CLK", "5": "WL_DATA", "6": "WL_DOUT", "8": "WL_GPIO0", "9": "WL_CS", "10": "WL_IRQ",
    "12": "WL_REG_ON", "13": "WL_REG_ON", "14": "+3V3", "16": "+3V3", "17": "WL_VBUS_SENSE", "18": "NC"})
add("R33", R, "470R", R0402, (710, 100), {"1": "WL_DOUT", "2": "WL_DATA"})
add("R34", R, "10k", R0402, (725, 100), {"1": "WL_IRQ", "2": "WL_DATA"})
add("R35", R, "1k", R0402, (740, 100), {"1": "WL_GPIO0", "2": "LED_A"})
add("D2", ("Device", "LED"), "USER", "LED_SMD:LED_0603_1608Metric", (755, 100), {"2": "LED_A", "1": "GND"})
add("R36", R, "5.6k", R0402, (710, 130), {"1": "VBUS", "2": "WL_VBUS_SENSE"})
add("R37", R, "10k", R0402, (725, 130), {"1": "WL_VBUS_SENSE", "2": "GND"})
add("C38", C, "10uF", C0603, (740, 130), {"1": "+3V3", "2": "GND"})
add("C39", C, "100nF", C0402, (755, 130), {"1": "+3V3", "2": "GND"})

# power flags: KiCad's rule is that power symbols (GND, +3V3) do not count as sources; a net whose only
# sources are power symbols, connectors or passives needs a PWR_FLAG or ERC reports 'power pin not driven'.
# (Confirmed 2026-10-04 by running ERC on KiCad's own Arduino template, which shows the same error.)
PWR_FLAGS = ["GND", "VBUS", "1V1", "VREG_AVDD", "ADC_AVDD", "BAT-", "RTC_VBAT", "PROT_VCC", "CELL_P"]

# ----------------------------------------------------------------------------- emit
POWER = {"GND": ("power", "GND"), "+3V3": ("power", "+3V3"), "VBUS": ("power", "VBUS")}


def U():
    return Q(str(uuid.uuid4()))


def prop(name, value, x, y, hide=False, size=1.27):
    eff = ["effects", ["font", ["size", size, size]]]
    if hide:
        eff.append("hide")
    return ["property", Q(name), Q(value), ["at", x, y, 0], eff]


def build():
    root_uuid = Q(_root_uuid())
    lib_symbols = ["lib_symbols"]
    seen = {}
    items = []
    refs = set()
    for c in comps:
        key = c["sym"]
        if key not in seen:
            seen[key] = CUSTOM[key] if key in CUSTOM else flatten(*key)
            lib_symbols.append(seen[key])
        node = seen[key]
        pts = pin_points(node)
        x0, y0 = (round(v / 1.27) * 1.27 for v in c["pos"])
        assert c["ref"] not in refs, c["ref"]
        refs.add(c["ref"])
        sym = ["symbol", ["lib_id", Q(f"{key[0]}:{key[1]}")], ["at", x0, y0, 0], ["unit", 1],
               ["exclude_from_sim", "no"], ["in_bom", "yes"], ["on_board", "yes"], ["dnp", "yes" if c.get("dnp") else "no"], ["uuid", U()],
               prop("Reference", c["ref"], x0 + 2.54, y0 - 2.54),
               prop("Value", c["value"], x0 + 2.54, y0 + 2.54),
               prop("Footprint", c["fp"], x0, y0, hide=True),
               prop("Datasheet", "", x0, y0, hide=True)]
        for num in pts:
            sym.append(["pin", Q(num), ["uuid", U()]])
        sym.append(["instances", ["project", Q(PROJECT), ["path", Q("/" + str(root_uuid)), ["reference", Q(c["ref"])], ["unit", 1]]]])
        items.append(sym)
        # labels at pins
        done_points = set()
        for num, net in c["pins"].items():
            if num not in pts:
                raise SystemExit(f"{c['ref']}: no pin {num} in {key}")
            px, py, rot, etype = pts[num]
            X, Y = round(x0 + px, 4), round(y0 - py, 4)
            if (X, Y) in done_points:
                continue
            done_points.add((X, Y))
            if net == "NC":
                items.append(["no_connect", ["at", X, Y], ["uuid", U()]])
            elif net in POWER:
                items.append(power_symbol(net, X, Y, rot, root_uuid))
            else:
                ang = {0: 180, 180: 0, 90: 270, 270: 90}[rot]
                items.append(["global_label", Q(net), ["shape", "passive"], ["at", X, Y, ang], ["fields_autoplaced", "yes"],
                              ["effects", ["font", ["size", 1.27, 1.27]], ["justify", "right" if ang == 180 else "left"]],
                              ["uuid", U()],
                              ["property", Q("Intersheetrefs"), Q("${INTERSHEET_REFS}"), ["at", X, Y, 0],
                               ["effects", ["font", ["size", 1.27, 1.27]], "hide"]]])
        # every listed pin must exist; unlisted pins are reported
        missing = [n for n in pts if n not in c["pins"]]
        if missing:
            print(f"note: {c['ref']} ({key[1]}) pins left open: {missing}")
    for net in POWER.values():
        if net not in seen:
            seen[net] = flatten(*net)
            lib_symbols.append(seen[net])
    # PWR_FLAG symbols on passively-driven nets
    seen[("power", "PWR_FLAG")] = flatten("power", "PWR_FLAG")
    lib_symbols.append(seen[("power", "PWR_FLAG")])
    for i, net in enumerate(PWR_FLAGS):
        X, Y = round((60 + 25 * i) / 1.27) * 1.27, 20.32
        items.append(["symbol", ["lib_id", Q("power:PWR_FLAG")], ["at", X, Y, 0], ["unit", 1], ["exclude_from_sim", "no"],
                      ["in_bom", "yes"], ["on_board", "yes"], ["dnp", "no"], ["uuid", U()],
                      prop("Reference", f"#FLG{i+1}", X, Y - 5, hide=True), prop("Value", "PWR_FLAG", X, Y - 7.62),
                      prop("Footprint", "", X, Y, hide=True), prop("Datasheet", "", X, Y, hide=True),
                      ["pin", Q("1"), ["uuid", U()]],
                      ["instances", ["project", Q(PROJECT), ["path", Q("/" + str(root_uuid)), ["reference", Q(f"#FLG{i+1}")], ["unit", 1]]]]])
        if net in POWER:
            items.append(power_symbol(net, X, Y, 90, root_uuid))
        else:
            items.append(["global_label", Q(net), ["shape", "passive"], ["at", X, Y, 270], ["fields_autoplaced", "yes"],
                          ["effects", ["font", ["size", 1.27, 1.27]], ["justify", "left"]], ["uuid", U()]])
    sch = ["kicad_sch", ["version", 20250114], ["generator", Q("eeschema")], ["generator_version", Q("9.0")],
           ["uuid", root_uuid], ["paper", Q("A1")],
           ["title_block", ["title", Q("Pocket Chance board, spin 1")], ["date", Q("2026-10-04")], ["rev", Q("0.3")],
            ["company", Q("Pocket Chance")],
            ["comment", 1, Q("Generated by pcb/tools/gen_sch.py from the connection table. Label-based: every pin carries its net name.")],
            ["comment", 2, Q("Blocks left to right: core | USB, power | screen, input, audio, card, sensors | wireless.")]],
           lib_symbols]
    sch.extend(items)
    note = ("BATTERY (PCB-001, owner decision 2026-10-04): one protected LiPo pouch cell, 1000 mAh or more, rated 0.5 C charge, "
            "charge temperature 0 to 45 C, JST-PH plug, + on pin 1 (red wire). Charge current 494 mA (R14 1.8k; 3.6k for 500 mAh). "
            "The charger does NOT sense the cell's temperature with a two-wire cell (R12 10k fitted = check bypassed); it relies on the cell's "
            "own protection board and the 0.5 C rate. A cell with a thermistor lead goes on pin 3: then remove R12. "
            "First power-ups: current-limited supply, no cell; then cell alone; then both. Charge on a non-flammable surface, never unattended.")
    sch.append(["text", Q(note), ["exclude_from_sim", "no"], ["at", 290, 470, 0],
                ["effects", ["font", ["size", 1.5, 1.5]], ["justify", "left", "top"]], ["uuid", U()]])
    sch.append(["sheet_instances", ["path", Q("/"), ["page", Q("1")]]])
    sch.append(["embedded_fonts", "no"])
    OUT.write_text(sexp.write(sch) + "\n")
    write_lib_tables(seen, comps)
    print(f"wrote {OUT.name}: {len(comps)} components, {len(lib_symbols)-1} symbols, {len(items)} items")


_pwr_count = [0]


def power_symbol(net, X, Y, pin_rot, root_uuid):
    libname, symname = POWER[net]
    _pwr_count[0] += 1
    # power symbol pin is at its origin; orient so the symbol points away from the component pin
    ang = {0: 270, 180: 90, 90: 180, 270: 0}[pin_rot] if net != "GND" else {0: 90, 180: 270, 90: 0, 270: 180}[pin_rot]
    # simpler and always valid: GND hangs down, others point up, regardless of pin direction
    ang = 0
    ref = f"#PWR{_pwr_count[0]}"
    return ["symbol", ["lib_id", Q(f"{libname}:{symname}")], ["at", X, Y, ang], ["unit", 1], ["exclude_from_sim", "no"],
            ["in_bom", "yes"], ["on_board", "yes"], ["dnp", "no"], ["uuid", U()],
            prop("Reference", ref, X, Y, hide=True), prop("Value", net, X + 2.54, Y + (3.81 if net == "GND" else -3.81), size=1.0),
            prop("Footprint", "", X, Y, hide=True), prop("Datasheet", "", X, Y, hide=True),
            ["pin", Q("1"), ["uuid", U()]],
            ["instances", ["project", Q(PROJECT), ["path", Q("/" + str(root_uuid)), ["reference", Q(ref)], ["unit", 1]]]]]


def write_lib_tables(seen, comps):
    """Project-local sym-lib-table and fp-lib-table listing the bundled libraries we use, plus pcb_custom."""
    symlibs = sorted({k[0] for k in seen if k[0] != "pcb_custom"})
    fplibs = sorted({c["fp"].split(":")[0] for c in comps if ":" in c["fp"] and not c["fp"].startswith("pcb_custom")})
    rows = ["(sym_lib_table", "\t(version 7)"]
    for name in symlibs:
        rows.append(f'\t(lib (name "{name}")(type "KiCad")(uri "${{KICAD10_SYMBOL_DIR}}/{name}.kicad_sym")(options "")(descr ""))')
    rows.append('\t(lib (name "pcb_custom")(type "KiCad")(uri "${KIPRJMOD}/lib/pcb_custom.kicad_sym")(options "")(descr "drawn from datasheets"))')
    rows.append(")")
    (OUT.parent / "sym-lib-table").write_text("\n".join(rows) + "\n")
    rows = ["(fp_lib_table", "\t(version 7)"]
    for name in fplibs:
        rows.append(f'\t(lib (name "{name}")(type "KiCad")(uri "${{KICAD10_FOOTPRINT_DIR}}/{name}.pretty")(options "")(descr ""))')
    rows.append('\t(lib (name "pcb_custom")(type "KiCad")(uri "${KIPRJMOD}/lib/pcb_custom.pretty")(options "")(descr "drawn from datasheets"))')
    rows.append(")")
    (OUT.parent / "fp-lib-table").write_text("\n".join(rows) + "\n")
    # the custom symbols also go into a real library file so KiCad's editor can show them
    libnode = ["kicad_symbol_lib", ["version", 20241209], ["generator", Q("gen_sch")], ["generator_version", Q("9.0")]]
    for k, node in CUSTOM.items():
        n = copy.deepcopy(node); n[1] = Q(k[1]); libnode.append(n)
    (OUT.parent / "lib").mkdir(exist_ok=True)
    (OUT.parent / "lib" / "pcb_custom.kicad_sym").write_text(sexp.write(libnode) + "\n")
    (OUT.parent / "lib" / "pcb_custom.pretty").mkdir(exist_ok=True)


def _root_uuid():
    import json
    pro = json.loads(PRO.read_text())
    return pro["sheets"][0][0]


if __name__ == "__main__":
    build()
