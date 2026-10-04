# Stand-in buttons for a scripted CARIBBEAN (flop game) session of the real pocket.py (flop-game bench):
# menu DOWN DOWN to Caribbean, A enter, 20 hands cycling call high / call low / fold, then 3 help shows
# (X; wait_any returns at once), then B to the menu. deal() and showdown() each drain one press with
# buttons.poll(), so each hand carries two LEFT fillers that are eaten. Logs RAM (before/after gc) and
# the gc pause at chosen polls; the fake itself allocates nothing per hand (leak check is honest).
import gc, utime
SCRIPT = ['DOWN', 'DOWN', 'A']
for h in range(20):
    SCRIPT += ['A', 'LEFT', ('A', 'Y', 'B')[h % 3], 'LEFT', 'A']     # deal(+eaten), decide(+eaten), next
SCRIPT += ['X', 'X', 'X', 'B']
PINS = ()
REPORT = {0: 'menu', 2: 'menu->caribbean', 3: 'caribbean ready (after init)', 8: 'after hand 1', 53: 'after hand 10', 103: 'after hand 20', 104: 'after help 1', 106: 'after help 3', 107: 'back at menu'}
class Buttons:
    def __init__(self): self.idle = 0; self.k = 0
    def poll(self):
        if self.k in REPORT:
            f = gc.mem_free(); t0 = utime.ticks_us(); gc.collect(); gc_us = utime.ticks_diff(utime.ticks_us(), t0); g = gc.mem_free()
            print('RESULT mem at %-28s free=%6d after_gc=%6d garbage=%5d gc_pause_us=%d' % (REPORT[self.k], f, g, g - f, gc_us))
        self.k += 1
        if SCRIPT: return [SCRIPT.pop(0)]
        self.idle += 1
        if self.idle > 1: raise SystemExit('script done')
        return []
    def held(self, name): return False
    def wait_any(self, poll_ms=10): return 'A'
