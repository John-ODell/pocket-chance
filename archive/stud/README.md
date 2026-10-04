# Caribbean Stud (archived, John's ruling of 2026-10-06)

John ruled three games only: Blackjack, Ultimate and his own "Caribbean" (a flop game, see
`games/caribbean*.py` and DR-062 to DR-071). Caribbean Stud, which was on the board as the
"Caribbean" row from step 1j to step 1n, leaves the menu and is kept here for reference. These files
are not uploaded to the board and are not run by the test suite.

What is here:
- `stud_rules.py`, `stud_table.py`, `stud_seats.py`: the rules (DR-025 to DR-032), the session and
  the five chip-stack seats (DR-041); house edge 5.2% of the ante with the basic strategy.
- `stud.py`, `stud_pay.py`: the screen (two rows of five cards, the clocked dealer reveal, the seat
  rail) and the pays/strategy screen.
- `test_stud.py`, `test_stud_seats.py`, `test_stud_screen.py`: the tests as they stood.
- `stud_edge.py`: the house-edge simulator used for DR-025.

The library modules it needed (`lib/poker.py`, the sheets' `banner_noqualify` slot, `icon_stud`)
stay in place: Ultimate uses the evaluator, sheet member order never changes once art exists, and
the new Caribbean game reuses the `icon_stud` menu slot.

To restore it: move the five game files back to `games/`, the tests to `tests/`, add the row
`('Caribbean', 'stud', 'icon_stud')` to `MENU` in `pocket.py` with a `STUD_SEATS` setting and
`ctx.stud_seats`, and list the files in `UPLOAD.md`.
