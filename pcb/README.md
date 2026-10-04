# pcb/: designing your own board

This folder is the workspace for turning the Pocket Chance hardware (a Waveshare RP2040-Plus plus a 1.3" LCD HAT) into **your own dev board**, ordered from a PCB fab such as PCBWay or JLCPCB. It is for someone doing this the first time.

**Status:** workspace set up. **Stage 1 (understand, no design choices)** comes first: the PCB maker writes `CONSTRAINTS.md` and `HOW_A_BOARD_IS_MADE.md`. Stage 2, what the first design adds, starts when the owner says so. See [`PLAN.md`](PLAN.md).

| File | What it is |
|---|---|
| [`PLAN.md`](PLAN.md) | The roadmap, the decisions to make first, rough costs, risks, and tools |
| [`INTAKE.md`](INTAKE.md) | What to read before designing: the project's measured hardware notes and the manufacturer documents |
| [`requirements/REQUIREMENTS.md`](requirements/REQUIREMENTS.md) | What the new board must do, with the source of every fact |
| [`../docs/roles/PCB_MAKER.md`](../docs/roles/PCB_MAKER.md) | The role file and starter prompt for the Claude session that guides you |
| `kicad/`, `bom/`, `fab/`, `reviews/` | KiCad project, bill of materials, files for the fab, and design reviews (empty for now) |
| `refs/` | Local copies of datasheets. **Not committed** (git ignores it) |

## How to start
1. Open a new Claude Code session in the repo folder and paste the starter prompt from `docs/roles/PCB_MAKER.md`.
2. Install KiCad (free): `brew install --cask kicad`, or download it from kicad.org.
3. Put the manufacturer PDFs you own into `pcb/refs/`.
4. Answer the questions one at a time. The PCB maker teaches each step.

## Request and review numbering (PM ruling, 2026-10-04)
PCB decision requests use their own prefix so they never clash with the developer's: `pm/inbox/PCB-001-slug.md`, rulings `pm/outbox/PCB-001.md`, and the expert's reviews of them `hw/reviews/HR-P01.md`. The one exception is the first scope request, which keeps its original number: `pm/inbox/DR-033-board-scope.md` (reviewed in `hw/reviews/HR-033.md`).

The PCB maker prepares everything for ordering and gives you a checklist. **You** place the order and enter payment details. It never does.
