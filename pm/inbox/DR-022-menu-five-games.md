# DR-022: Menu: five games do not fit three rows

- **Status:** pending
- **Filed by:** senior dev
- **Date:** 2026-10-04
- **Blocks:** Nothing yet; needed before the second new game is added
- **Needs HW review:** no

## The decision
How the main menu shows Blackjack, Slots, Caribbean Stud, Ultimate Texas Hold'em and Off when only three 48 px rows fit between the title and the footer.

## Options
### A. Scrolling list, three rows visible (recommended)
- The list is Blackjack, Slots, Caribbean Stud, Ultimate Hold'em, Off. Three rows show at a time in the same boxes as today; the selection moves and the list scrolls when it reaches the edge. Small gold arrows at the right edge of the row area (x 228, y 70 and y 206) show there is more above or below.
- Redraw: a scroll redraws the three row bands (three 48-row background slices and pushes, about 70 ms); a move within the visible rows is the two-band redraw used today (46 ms measured).
- Pros: keeps the look John said he likes, the icon slot, the photo background and the plates; grows to any number of games.
- Cons: the player cannot see all five at once.

Mock (rows 70, 118, 166; `>` = selected):
```
        Pocket Chance
            $1000
  [icon]  Blackjack
> [icon]  Slots            <- box
  [icon]  Caribbean Stud  v  (arrow: more below)
   joystick: move   A: pick
```

### B. Submenu: "Cards" and "Slots"
- Cons: two presses to reach a game; "Cards" hides what is inside.

### C. Two-column grid of 48 x 48 icons with small labels
- Cons: depends on icon art that does not exist yet; size-1 labels are small; a new layout to test on the photo.

## Recommendation
Option A. "Ultimate Hold'em" (15 characters) fits at size 2 only if the label area is 152 px wide; 15 x 16 = 240 px does not. The two long names are shown as **"Carib. Stud"** and **"Ult. Hold'em"**, which fit (the text-bounds test enforces it). The game screens use the full names.

## What John would have to do or accept
Two abbreviated names on the menu, and a small arrow when the list continues.
