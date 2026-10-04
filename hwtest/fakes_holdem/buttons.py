# Stand-in buttons for a scripted ULTIMATE HOLD'EM session of the real pocket.py (step 1m bench):
# menu DOWN DOWN to Hold'em, A enter, 20 hands alternating raise-at-river and fold-at-river, then
# 4 help shows (X, any key returns), then B to the menu. The showdown drains one press, so a raise
# hand sends an extra A. Logs RAM (before/after gc) and the gc pause at chosen polls.
import gc, utime
SCRIPT = ['DOWN', 'DOWN', 'A']
for h in range(20):
    SCRIPT += (['A', 'B', 'B', 'A', 'A', 'A'] if h % 2 == 0 else ['A', 'B', 'B', 'B', 'A'])   # deal, check, check, raise(+eaten next)+next | fold, next
SCRIPT += ['X', 'X', 'X', 'X', 'B']
PINS = ()
REPORT = {0: 'menu', 2: 'menu->holdem', 3: 'holdem ready (after init)', 9: 'after hand 1', 58: 'after hand 10', 113: 'after hand 20', 114: 'after help 1', 117: 'after help 4', 118: 'back at menu'}
class Buttons:
    def __init__(self): self.idle = 0; self.k = 0
    def poll(self):
        if self.k in REPORT:
            f = gc.mem_free(); t0 = utime.ticks_us(); gc.collect(); gc_us = utime.ticks_diff(utime.ticks_us(), t0); g = gc.mem_free()
            print('RESULT mem at %-26s free=%6d after_gc=%6d garbage=%5d gc_pause_us=%d' % (REPORT[self.k], f, g, g - f, gc_us))
        self.k += 1
        if SCRIPT: return [SCRIPT.pop(0)]
        self.idle += 1
        if self.idle > 1: raise SystemExit('script done')
        return []
    def held(self, name): return False
    def wait_any(self, poll_ms=10): return 'A'
