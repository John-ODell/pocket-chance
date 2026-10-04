# DR-052: Baccarat: screen layout and how the cards are dealt

- **Status:** pending
- **Filed by:** senior dev
- **Date:** 2026-10-06
- **Blocks:** The baccarat screen
- **Needs HW review:** yes (full redraw and the clocked deal; band pushes)

## The decision
Where the Banker hand, the Player hand, the three bet areas, the totals and the prompt sit on the 240 x 240 panel, and how the cards appear.

## Why it matters
Baccarat shows at most six cards, so it is the roomiest of our screens, but the three bet areas and the seat rail (DR-055) must share the bottom band with the prompt and the result.

## Options
### A. Caribbean Stud's four bands, three card slots per hand, three bet boxes along the bottom (recommended)
- **Top band, rows 0 to 23:** chips and stake, as in every game.
- **Banker band, rows 24 to 95:** up to three cards (40 x 56) at x 56, 100 and 144, y 28 to 83 (the third card fills the third slot); the line "BANKER  7" under them at y 86 in size-1 white, "natural" appended on an 8 or 9.
- **Player band, rows 96 to 167:** the same at y 100 to 155 with "PLAYER  6" at y 158. The Player's hand is the lower one, as at a real table.
- **Bottom band, rows 168 to 239:** three bet boxes at x 8 to 78, 85 to 155 and 162 to 232, y 172 to 196, labelled PLAYER, TIE and BANKER with their pays in small text ("1:1", "8:1", "19:20"); the chosen box has a gold frame and shows the stake. The prompt line at y 202 ("joystick: bet   A deal   X pays   B menu"); after the coup the same line shows the result in gold, for example "BANKER WINS 8-6   -20" or "TIE   +160", and the chips move. Rows 228 to 239 are the seat rail (DR-055); rows 214 to 222 the result history if DR-060 is approved.
- **Deal:** the four cards appear one at a time, Player, Banker, Player, Banker, 300 ms apart, each a 72-row band push with the total line updated (the pace ruled for Stud and Hold'em, DR-029 and DR-047). A natural ends the coup. Otherwise, after a further 300 ms, the Player's third card if drawn, then the Banker's, each 300 ms apart, with the total line changing as the card lands. From A to the result: 1.5 s with four cards, up to 2.1 s with six.
- **Cost estimate:** a full redraw with six cards is about 18.5 ms on the wire plus six cards at 3.9 ms drawn (2.9 from a sheet) plus four short text lines, about 50 ms, less than Stud's 89 ms. A band push during the deal is about 26 ms. No new primitives; the bet boxes are `fill_rect` and size-1 text.
- Pros: every element reuses Stud's measured parts; the pace matches the other two card games.
- Cons: the bottom band is busy once the rail and the history strip are in; the text test keeps every string on the panel.

### B. Cards side by side in one band, Player left and Banker right
- Three cards each need 2 x 128 px plus a gap, 264 px: too wide for 40 x 56 cards. Rejected on the arithmetic.

### C. All four cards at once, then clocked third cards only
- Pros: a coup takes 0.9 to 1.5 s.
- Cons: the alternating deal is the game's one moment of drama; the other card games clock every reveal.

## Recommendation
Option A. The expert can check the bottom band's drawing time and the 300 ms spacing on the mount before the first upload.

## What John would have to do or accept
Nothing to draw; cards and chips come from the existing sheets. Each coup takes 1.5 to 2.1 s from A to the result, like a Stud raise.

## Appendix
Band rows and card x positions are Stud's (`games/stud.py`: `CARD_X`, `DEALER_TOP`, `PLAYER_TOP`, `BOTTOM_TOP`, `RAIL_Y`). HR-026 and HR-029 measured a five-card band push at 26 to 28 ms and a code-drawn card at 3.9 ms.
