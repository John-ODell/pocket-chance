# DR-018: Slots: paytable, RTP and jackpot

- **Status:** pending
- **Filed by:** senior dev
- **Date:** 2026-10-04
- **Blocks:** Slots screen
- **Needs HW review:** no

## The decision
What each winning line pays, and therefore the return to player (RTP), hit frequency and jackpot.

## Why it matters
This is the house edge of the game. Everything below is **exact**, computed by enumerating all 32,768 stop combinations (`tools/slots_rtp.py`), not sampled.

## The strip (from DR-017)
32 stops per reel: cherry 3, lemon 7, orange 6, bell 5, bar 4, seven 3, diamond 3, star 1.

## Options (pays are per chip bet)
| Line | A (recommended) | B generous | C big jackpot |
|---|---|---|---|
| Three stars (jackpot) | **1000** | 1000 | 2000 |
| Three diamonds | 200 | 200 | 200 |
| Three sevens | 100 | 100 | 100 |
| Three bars | 40 | 40 | 40 |
| Three bells | 20 | 20 | 20 |
| Three oranges | 14 | 14 | 14 |
| Three lemons | 10 | 10 | 10 |
| Three cherries | 8 | 8 | 8 |
| Two cherries anywhere | 3 | 4 | 2 |
| One cherry anywhere | 1 (bet back) | 1 | 1 |
| **RTP** | **93.8%** | 96.2% | 94.5% |
| House edge | 6.2% | 3.8% | 5.5% |
| Hit frequency | 1 in 3.6 spins (28%) | 1 in 3.6 | 1 in 3.6 |
| Volatility (SD per spin) | 8.9 bets | 8.9 | 13.0 |
| Jackpot odds | 1 in 32,768 | same | same |

For comparison, real machines run 85 to 96%. Blackjack here is about 0.55% house edge; slots are meant to be a faster, swingier game.

## Recommendation
Option A: 93.8% RTP sits inside the PM's 93 to 96% target, pays something on 28% of spins (one cherry returns the bet, which keeps play going), and the 1000x jackpot is reachable (about one in 32,768 spins; at a spin every 4 seconds that is one jackpot per 36 hours of play). The jackpot is **fixed** (1000 x bet), not progressive: a progressive would need its own saved value and its own rules, and can come later as a separate request.

I would pick B if John wants the game kinder, or C if he wants a bigger headline prize and accepts bigger swings.

## What John would have to do or accept
House edge about 6% per spin. With a 5-chip bet, the bankroll drifts down about 0.3 chips per spin on average, with swings of about 45 chips. A paytable screen in the game will show these numbers to the player.

## Appendix
`python3 tools/slots_rtp.py` prints the contribution of every line. Option A: the one-cherry line is 23.1 points of the 93.8% RTP (it hits 1 in 4.3 spins), three diamonds 16.5 (1 in 1,214), three lemons 10.5 (1 in 96), three oranges 9.2, three sevens 8.2, three bars 7.8, three bells 7.6, two cherries 7.2 (1 in 42), three stars 3.05 (1 in 32,768), three cherries 0.7.
