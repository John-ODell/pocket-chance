# DR-008: What happens when the save file is missing or corrupt

- **Status:** pending
- **Filed by:** senior dev
- **Date:** 2026-10-03
- **Blocks:** Bankroll module (loading half)
- **Needs HW review:** yes

## The decision
What the game does at start-up when `/save.json` is missing, unreadable, or fails its checksum.

## Why it matters
A silent reset feels like a bug to the player. A crash at boot leaves John with a board that will not run and no screen to explain it.

## Options
### A. Reset to the starting bankroll silently
- Cons: hides problems. John would not know it happened.

### B. Keep a backup, fall back to it, then reset with a message (recommended)
- What it is: before each save the previous good file is kept as `/save.bak`. On start-up: use `/save.json` if valid. Else use `/save.bak` if valid, and show "Save restored from backup". Else start fresh at the starting bankroll and show "Save damaged. Starting fresh." The damaged file is renamed to `/save.bad` so John can look at it. A missing file on first run is normal and shows no message.
- Pros: nearly always recovers; the player is told; nothing crashes.
- Cons: three possible files on the board; `/save.bad` is overwritten if damage happens twice.

### C. Refuse to start until John deletes the file
- Cons: bad for a handheld toy.

## Recommendation
Option B. Loading never raises an error; every failure ends in one of the three outcomes above.

## What John would have to do or accept
Occasionally sees a one-line message on screen after a rough power cut.
