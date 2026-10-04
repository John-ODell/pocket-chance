# DR-029: Caribbean Stud: how the dealer's hand is revealed

- **Status:** pending
- **Filed by:** senior dev
- **Date:** 2026-10-05
- **Blocks:** Caribbean Stud screen
- **Needs HW review:** yes

## The decision
How the dealer's four hidden cards are turned over after the player raises, and how long it takes.

## Options
### A. One card at a time, 300 ms apart, then the result (recommended)
- After a raise: the dealer band is redrawn with one more card face up and pushed (one 72-row band push, about 15 ms with code-drawn cards), four times, 300 ms apart; then the hand names and the result banner appear (full redraw, one `show()`), then the save (DR-007 order), so the whole reveal is about 1.3 s. Keys are ignored during the reveal.
- After a fold: the dealer's cards are revealed all at once with the result "Folded, -ante" (the player usually wants to see what they folded against; it costs one redraw).
- Pros: some suspense, cheap (four band pushes), nothing allocated in the loop, no save during the animation (HR-021 rule).
- Cons: 1.2 s of waiting per raised hand.

### B. All at once
- Pros: fastest.
- Cons: flat.

### C. Flip animation per card (sliding the card face in)
- Cons: per-frame work for little gain; HR-F04 showed per-frame animation is where the RAM and timing risks live.

## Recommendation
Option A. The expert should confirm the band-push cost with five cards in the band.

## What John would have to do or accept
About a second's pause after each raise while the dealer's cards turn over.
