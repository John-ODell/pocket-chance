# DR-026: Caribbean Stud: screen layout for two five-card hands

- **Status:** pending
- **Filed by:** senior dev
- **Date:** 2026-10-05
- **Blocks:** Caribbean Stud screen
- **Needs HW review:** yes

## The decision
Where the ten cards, the dealer's up-card, the hand names, the ante/raise line and the prompts go on the 240 x 240 screen, and how it is redrawn.

## Why it matters
Ten 40 x 56 cards is the most this screen has shown; each code-drawn card costs 3.9 ms, each sheet card 2.9 ms (HR-F03/HR-024), so a deal is about 40 to 60 ms of drawing.

## Options
### A. Same four bands as blackjack, five cards per row (recommended)
- Top band 0–23: `$chips` left; ante and raise on the right ("ante 10" while betting, "10 + 20" after a raise).
- Dealer band 24–95: five cards at y 28–83, x = 12, 56, 100, 144, 188 (40 wide, 4 px gaps, 216 px total); the four hole cards face down until the player decides. Dealer line at y 86–94: "Dealer shows K" before, "Dealer: two pair" or "Dealer does not qualify" after.
- Player band 96–167: five cards at y 100–155, same x. Line at y 158–166: "You: pair of 9s".
- Bottom band 168–239: result banner at y 168–199 (`banner_win` / `banner_lose` / `banner_push`, plus a new `banner_noqualify`; code-drawn text until the art exists); net line at 204 ("+30: ante 10, raise 20 x 1"); prompts at 218 ("A raise 20   B fold", then "A next   B menu").
- Redraw: a scene change (deal, result) is a full redraw and one `show()`, like blackjack (measured 45 ms with 8 cards; expect about 50 to 60 ms with 10 code-drawn cards, about 45 with sheet art). A raise or fold redraws the dealer band and the bottom band (two band pushes). No per-frame work except the reveal (DR-029).
- Pros: the player already knows this screen from blackjack; everything fits with no overlap (the text-bounds test enforces it).
- Cons: 4 px gaps are tight; cards never overlap so the rank corner is always visible.

### B. Fan the cards with overlap and show hand names larger
- Cons: hides corners for no gain; the row fits without overlap.

## Recommendation
Option A. The expert should time a 10-card full redraw code-drawn and with a sheet.

## What John would have to do or accept
Nothing new to draw for the layout. See DR-032 for the one optional banner.
