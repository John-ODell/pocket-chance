# Stand-in buttons for a scripted BACCARAT session of the real pocket.py (step 1q, main b102960):
# menu DOWN x3 (two moves and a scroll) to Baccarat, A enter, 100 coups (A; deal() drains one press
# with buttons.poll(), so each coup carries one LEFT filler that is eaten), 3 pay screens (X;
# wait_any returns at once), B to the menu, then idle ends the script. Logs RAM (before/after gc)
# and the gc pause at chosen polls; the fake allocates nothing per coup (the leak check is honest).
import gc, utime
SCRIPT = ['DOWN', 'DOWN', 'DOWN', 'A']
for c in range(100):
    SCRIPT += ['A', 'LEFT']
SCRIPT += ['X', 'X', 'X', 'B']
PINS = ()
REPORT = {0: 'menu', 3: 'menu, Baccarat selected', 4: 'baccarat ready (after init)', 6: 'after coup 1',
          24: 'after coup 10', 104: 'after coup 50', 204: 'after coup 100', 205: 'after pays 1',
          207: 'after pays 3', 208: 'back at menu'}
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
