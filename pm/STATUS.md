# Status

_Updated by the senior dev at the end of each session. Written for John._

**Last updated:** 2026-10-04 (morning)

## Where we are
Phase 1 (blackjack) has started. The game logic is built and tested on the Mac. On-board code waits on the layout and art rulings below. The board now runs MicroPython v1.29.0 with 15 MB of space, and the expert has measured it, so my requests now rest on real numbers instead of my estimates.

## New today: the screen speed fix (DR-015)
The new firmware made the screen link 2.6 times slower (a full redraw takes 46 ms instead of 18 ms). The expert found a three-line software fix and measured it back to full speed. I filed DR-015 recommending we use it, with an off switch in case the picture ever looks wrong. Cards play fine either way; it matters more for slot animation later.

## Approved by you so far
Dealer stands on all 17, blackjack pays 3:2, 6 decks reshuffled after 75%, hit/stand/double only, start at 1000 chips with a free refill when broke, bets 5 to 500 in steps of 5, and Pillow for the Mac-side image converter.

## Done
- Built the betting and bankroll logic on top of the engine (bet limits, doubling only when you can afford it, broke and refill, reshuffle flag for the "Shuffling" moment). 58 automated tests pass on the Mac. Saving the bankroll to flash is not written, because that waits on DR-007 and DR-008.
- Read all the project docs and the old program.
- Built and tested the blackjack rules engine. It deals from a shuffled shoe, scores hands (aces count 1 or 11 correctly), plays the dealer's turn, and works out payouts. Hit, stand and double are supported. 40 automated tests pass on the Mac.
- The rules you still have to approve are settings, not hard-wired: dealer stand or hit on soft 17, blackjack pays 3:2 or 6:5, and number of decks.
- Wrote a Mac tool that plays about 3 million hands per rule set and measures the house edge, so the requests below quote real numbers.
- Wrote a read-only check script for the board (`tools/board_probe.py`).
- Filed 14 decision requests in `pm/inbox/` (below).

## Still waiting on a decision (pending with the PM)
Each is one decision with my recommendation. The expert has reviewed DR-001, 002, 003, 005, 006, 007 and 008 (all fit, DR-005 within limits in HR-005), so they are ready for you.
- **DR-015** Use the expert's screen speed fix at start-up (recommended), or live with the slower screen.
- **DR-001** File layout on the board, and keeping the old program as the boot file until you say otherwise.
- **DR-002, DR-003, DR-005** Art pipeline: file format, colour byte order, how images are loaded.
- **DR-006** Whether the art sizes in `assets/ASSETS.md` hold up. My answer: yes, keep them. Please start with 4 pilot images, not all 60.
- **DR-007, DR-008** How the bankroll is saved, and what happens if the save is damaged.

I am not waiting on these. Next I will carry on with parts that need no ruling (see below) and pick up each request as soon as it is ruled.

## What I plan next
- Check `pm/outbox/` first thing next session.
- Start the screen driver copy, the button reader and the blackjack screens once DR-001 is ruled.
- Start the converter once DR-002 and DR-003 are ruled (DR-004 is approved).

## John needs to upload or test
- Nothing needs uploading for the game yet.
- With the expert at the board: the screen check (which half is red, is "TOP" at the top) and the 8-second button press capture. These settle colour order and orientation before you make art.
- Art can wait until DR-002, DR-003 and DR-006 are ruled, then make the 4 pilot files first.

## Not tested
Everything so far is tested on the Mac only. The code has not been run under MicroPython or on the board. In particular the colour byte order and screen orientation are untested guesses based on reading the old driver (see DR-003).
