# slots_ram_bench.py: DR-020 rev 2 RAM question. Real /pocket.py set up (menu state), then a game
# module imported the way pocket.play() does (blackjack stands in for the slots screen, same size
# class), then try option A (6 symbol slots + compose = 43,904 B) and option B (2 slots + compose =
# 18,816 B), reporting free RAM and the largest allocatable block at each step.
import gc, sys
src = open('/pocket.py').read(); src = src[:src.rstrip().rfind('main()')]
ns = {'__name__': 'slots_ram_bench_ns'}; exec(src, ns)
def largest():
    gc.collect(); lo, hi = 0, gc.mem_free()
    while lo < hi - 256:
        mid = (lo + hi) // 2
        try: x = bytearray(mid); del x; lo = mid
        except MemoryError: hi = mid
        gc.collect()
    return lo
gc.collect(); print("RESULT menu_ready free=%d largest_block=%d" % (gc.mem_free(), largest()))
if '/games' not in sys.path: sys.path.append('/games')
gc.collect(); f0 = gc.mem_free(); mod = __import__('blackjack'); gc.collect()
print("RESULT game_module_imported cost=%d free=%d largest_block=%d (blackjack as stand-in for the slots screen)" % (f0 - gc.mem_free(), gc.mem_free(), largest()))
def try_option(label, n_slots):
    gc.collect(); f = gc.mem_free(); bufs = []
    try:
        for _ in range(n_slots): bufs.append(bytearray(6272))
        bufs.append(bytearray(6272))                       # compose
        gc.collect(); print("RESULT %s: fits, cost=%d free_after=%d largest_block_after=%d" % (label, f - gc.mem_free(), gc.mem_free(), largest()))
    except MemoryError:
        print("RESULT %s: DOES NOT FIT after %d of %d buffers, free_was=%d" % (label, len(bufs), n_slots + 1, f))
    del bufs; gc.collect()
try_option("option_A_6_slots_plus_compose_43904B", 6)
try_option("option_B_2_slots_plus_compose_18816B", 2)
try_option("option_A2_3_slots_plus_compose_25088B", 3)
gc.collect(); print("RESULT end free=%d" % gc.mem_free())
