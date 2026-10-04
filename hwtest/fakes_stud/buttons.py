# Stand-in buttons for a scripted CARIBBEAN STUD session of the real pocket.py (step 1j bench):
# menu DOWN to Caribbean, A enter, 20 hands (deal; raise on odd hands, fold on even; next), then
# 4 paytable shows (X, any key returns), then B to the menu. Logs RAM (before/after gc) and the gc
# pause at chosen polls only, to keep the output short.
import gc, utime
SCRIPT = ['DOWN', 'A']
for h in range(6): SCRIPT += (['A', 'A', 'A'] if h % 2 == 0 else ['A', 'B', 'A'])   # note: the reveal drains one press, so a raise hand's 'next' is eaten and the following key acts as next
SCRIPT += ['X', 'X', 'X', 'X', 'B']
PINS = ()
REPORT = {0: 'menu', 1: 'menu->stud', 2: 'stud ready (after init)', 5: 'after hand 1', 20: 'after hand 6', 21: 'after paytable 1', 24: 'after paytable 4', 25: 'back at menu'}
class Buttons:
    def __init__(self): self.idle = 0; self.k = 0
    def poll(self):
        if self.k in REPORT:
            f = gc.mem_free(); t0 = utime.ticks_us(); gc.collect(); gc_us = utime.ticks_diff(utime.ticks_us(), t0); g = gc.mem_free()
            print('RESULT mem at %-24s free=%6d after_gc=%6d garbage=%5d gc_pause_us=%d' % (REPORT[self.k], f, g, g - f, gc_us))
        self.k += 1
        if SCRIPT: return [SCRIPT.pop(0)]
        self.idle += 1
        if self.idle > 1: raise SystemExit('script done')
        return []
    def held(self, name): return False
    def wait_any(self, poll_ms=10): return 'A'
