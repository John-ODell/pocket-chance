# Slots (shelved, ruling D-009, 2026-10-04)

John dropped slots: a classic multi-line five-reel machine does not fit the board's RAM, and a
three-reel single-line machine was not worth the cost. These files are kept for reference only and
are not uploaded to the board or run by the test suite.

What is here:
- `slots_rules.py`: 3-reel, one-line engine with virtual strips and an exact enumerator (RTP 93.84%
  for the approved paytable, DR-017/018).
- `slots_table.py`: session logic, bet limits and `SpinPlan` (staggered reel timing).
- `slots.py`, `slots_pay.py`: the screen with the scrolled-window spin animation (DR-020 rev 2,
  fallback B) and the paytable screen. The last version here is the zero-allocation rewrite that was
  in progress when slots was shelved; it was never benched.
- `test_slots_*.py`: the tests as they stood (they import from `lib/` and `games/` of that time).
- `slots_rtp.py`: the exact RTP / hit-frequency tool used for DR-018.

The hardware findings from this work (HR-020, HR-021, HR-F03, HR-F04 in `hw/reviews/`) still
apply to every game: no file opens or allocations in an animation loop, sheets instead of one file
per sprite, gc.collect() before any timed loop.
