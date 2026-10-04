# Status

_Updated by the senior dev at the end of each session. Written for John._

**Last updated:** 2026-10-03 (session 1)

## Where we are
Phase 1 (blackjack) has started. No rulings from the PM existed yet, so I did not start anything that needs one.

## Done
- Read all the project docs and the old program.
- Built and tested the blackjack rules engine. It deals from a shuffled shoe, scores hands (aces count 1 or 11 correctly), plays the dealer's turn, and works out payouts. Hit, stand and double are supported. 40 automated tests pass on the Mac.
- The rules you still have to approve are settings, not hard-wired: dealer stand or hit on soft 17, blackjack pays 3:2 or 6:5, and number of decks.
- Wrote a Mac tool that plays about 3 million hands per rule set and measures the house edge, so the requests below quote real numbers.
- Wrote a read-only check script for the board (`tools/board_probe.py`).
- Filed 14 decision requests in `pm/inbox/` (below).

## Blocked on a decision (all pending with the PM)
Each is one decision with my recommendation. DR-001, 002, 003, 005, 006, 007 and 008 touch RAM, flash, redraw or the display, so they also need a review from the microcontroller expert before they go to you. My timing and speed figures in them are estimates, not measurements.
- **DR-001** File layout on the board, and keeping the old program as the boot file until you say otherwise.
- **DR-002 to DR-005** Art pipeline: file format, colour byte order, Pillow library on the Mac, how images are loaded.
- **DR-006** Whether the art sizes in `assets/ASSETS.md` hold up. My answer: yes, keep them. Please start with 4 pilot images, not all 60.
- **DR-007, DR-008** How the bankroll is saved, and what happens if the save is damaged.
- **DR-009 to DR-012** Blackjack rules. I recommend dealer stands on soft 17, blackjack pays 3:2, 6 decks, hit/stand/double only. House edge about 1%.
- **DR-013, DR-014** Starting chips (1000) and bet limits (5 to 500).

I am not waiting on these. Next I will carry on with parts that need no ruling (see below) and pick up each request as soon as it is ruled.

## What I plan next
- Check `pm/outbox/` first thing next session.
- Start the screen driver copy, the button reader and the bet and play logic wiring once DR-001 is ruled.
- Start the converter once DR-002 to DR-004 are ruled.

## John needs to upload or test
- Nothing needs uploading for the game yet.
- Optional, useful now: run the board check in `UPLOAD.md` and tell me what it prints. It shows which MicroPython firmware you have and how much space is free, and it writes nothing.
- Art can wait until DR-002, DR-003 and DR-006 are ruled, then make the 4 pilot files first.

## Not tested
Everything so far is tested on the Mac only. The code has not been run under MicroPython or on the board. In particular the colour byte order and screen orientation are untested guesses based on reading the old driver (see DR-003).
