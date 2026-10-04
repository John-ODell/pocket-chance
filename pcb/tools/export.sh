#!/bin/sh
# Regenerate the schematic exports with kicad-cli and strip absolute paths (the repository is public).
# Usage: sh pcb/tools/export.sh   (from the repo root)
set -e
K=/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli
SCH=pcb/kicad/pocket-chance-board.kicad_sch
OUT=pcb/kicad/exports
mkdir -p "$OUT"
"$K" sch erc --output "$OUT/erc.rpt" --severity-all "$SCH" 2>&1 | grep -v Fontconfig | tail -1
"$K" sch export pdf --output "$OUT/pocket-chance-board-schematic.pdf" "$SCH" 2>&1 | grep -v Fontconfig | tail -1
"$K" sch export netlist --format kicadxml --output "$OUT/netlist.xml" "$SCH" 2>&1 | grep -v Fontconfig | tail -1
# kicad-cli writes the absolute source path into the netlist; replace it with the repository-relative one
sed -i '' "s|<source>.*pocket-chance-board.kicad_sch</source>|<source>$SCH</source>|" "$OUT/netlist.xml"
sed -i '' "s|/Users/[^/ ]*/[^ <\"]*pcb-desk/||g; s|/Users/[^/ ]*/[^ <\"]*pico-pocket-chance/||g" "$OUT/netlist.xml" "$OUT/erc.rpt"
if grep -l "/Users/" "$OUT"/erc.rpt "$OUT"/netlist.xml 2>/dev/null; then echo "ERROR: an absolute path remains in the exports" >&2; exit 1; fi
echo "exports OK: $(grep -o 'ERC messages: [0-9]*  Errors [0-9]*  Warnings [0-9]*' "$OUT/erc.rpt"); schematic hash $(git hash-object "$SCH")"
