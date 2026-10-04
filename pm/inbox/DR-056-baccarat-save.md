# DR-056: Baccarat: when the bankroll is saved

- **Status:** pending
- **Filed by:** senior dev
- **Date:** 2026-10-06
- **Blocks:** The baccarat screen
- **Needs HW review:** no

## The decision
When `/save.json` is written during baccarat and what it holds.

## Options
### A. Once per coup after the result is drawn; the stake is saved as the bet, the side is not; seats never saved (recommended)
- Same file, format and order as the other games (DR-007, DR-030, DR-048): draw the result, then save, so the result appears at once and the 50 to 150 ms write hides behind it.
- The saved bet is the stake; the side (Player, Tie, Banker) resets to Player on entry. Saving the side would need a new field and a format version; it is one joystick press to restore.
- Seat chips and the result history (DR-060) are cosmetic and start fresh on entry.

### B. Save the side and the history too
- Cons: a format version bump for two things a player re-creates in a second.

## Recommendation
Option A.

## What John would have to do or accept
The game remembers his chips and his stake; it starts each visit on Player.
