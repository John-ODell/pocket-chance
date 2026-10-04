# Stand-in buttons for a scripted BLACKJACK run of the real pocket.py (step 1i bench): enter, deal,
# stand, next, deal, stand, back to menu; logs free RAM (before/after gc) and the gc pause per poll.
import gc, utime
SCRIPT = ['A', 'A', 'B', 'A', 'A', 'B', 'B']
PINS = ()
LABELS = ['menu', 'menu->blackjack', 'blackjack ready (after init)', 'after deal 1', 'after stand 1 (result)', 'after next (betting)', 'after deal 2', 'after stand 2 (result)', 'back at menu']
class Buttons:
    def __init__(self): self.idle = 0; self.k = 0
    def poll(self):
        f = gc.mem_free(); t0 = utime.ticks_us(); gc.collect(); gc_us = utime.ticks_diff(utime.ticks_us(), t0); g = gc.mem_free()
        label = LABELS[self.k] if self.k < len(LABELS) else 'poll %d' % self.k
        print('RESULT mem at %-28s free=%6d after_gc=%6d garbage=%5d gc_pause_us=%d' % (label, f, g, g - f, gc_us))
        self.k += 1
        if SCRIPT: return [SCRIPT.pop(0)]
        self.idle += 1
        if self.idle > 1: raise SystemExit('script done')
        return []
    def held(self, name): return False
    def wait_any(self, poll_ms=10): return 'A'
