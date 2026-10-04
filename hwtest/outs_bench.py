# outs_bench.py: DR-042 river hint cost. For the 45 unseen cards: evaluate(card + 5 board cards)
# (6 cards, 6 combinations) and compare with the player's 7-card value; count the cards that beat it.
# Real lib/poker.py on the board (step 1j). Also the 7-card player value once, and the whole hint.
import gc, utime, random, sys
if '/games' not in sys.path: sys.path.append('/games')
import poker
random.seed(4242)
deck = list(range(52))
for i in range(51, 0, -1):
    j = random.randrange(i + 1); deck[i], deck[j] = deck[j], deck[i]
player, board, dealer = deck[0:2], deck[2:7], deck[7:9]
seen = set(player + board)
unseen = [c for c in range(52) if c not in seen]
print("RESULT unseen=%d" % len(unseen))
t0 = utime.ticks_us(); pv = poker.evaluate(player + board); t_pv = utime.ticks_diff(utime.ticks_us(), t0)
t0 = utime.ticks_us()
outs = 0
for c in unseen:
    v = poker.evaluate([c] + board)
    if poker.compare(v, pv) > 0: outs += 1
t_outs = utime.ticks_diff(utime.ticks_us(), t0)
print("RESULT player_7card_evaluate_us=%d" % t_pv)
print("RESULT river_outs_45x6card_us=%d (%.1f ms per unseen card) outs=%d" % (t_outs, t_outs / 45000, outs))
# the dev's alternative reading: dealer's two hole cards unknown -> each unseen card as ONE of them is
# a 6-card hand; if both unknown it would be C(45,2)=990 7-card evaluates: time 20 of those to bound it
t0 = utime.ticks_us()
for k in range(20): poker.evaluate(unseen[k:k+2] + board)
print("RESULT pairs_7card_evaluate_us_each=%d -> 990 pairs would be %.1f s (not viable)" % (utime.ticks_diff(utime.ticks_us(), t0) // 20, utime.ticks_diff(utime.ticks_us(), t0) / 20 * 990 / 1e6))
gc.collect(); print("RESULT mem_free=%d" % gc.mem_free())
