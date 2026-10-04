# Stand-in for lib/buttons.py used ONLY by hwtest/pocket_scripted.py: feeds scripted keys to the
# real pocket.py instead of reading pins, and logs free RAM at each poll (before and after a
# gc.collect, so garbage churn is told apart from retention). Zero overhead inside the game.
import gc, utime
SCRIPT = ['DOWN', 'A', 'A', 'A', 'A', 'B']      # to Slots, enter, spin, spin, spin, back to menu
PINS = ()
LABELS = ['menu', 'menu->slots', 'slots ready (after init)', 'after spin 1', 'after spin 2', 'after spin 3', 'back at menu']
class Buttons:
    def __init__(self): self.idle = 0; self.k = 0
    def poll(self):
        f = gc.mem_free(); t0 = utime.ticks_us(); gc.collect(); gc_us = utime.ticks_diff(utime.ticks_us(), t0); g = gc.mem_free()
        label = LABELS[self.k] if self.k < len(LABELS) else 'poll %d' % self.k
        print('RESULT mem at %-26s free=%6d after_gc=%6d garbage=%6d gc_pause_us=%d' % (label, f, g, g - f, gc_us))
        self.k += 1
        if SCRIPT: return [SCRIPT.pop(0)]
        self.idle += 1
        if self.idle > 1: raise SystemExit('script done')
        return []
    def held(self, name): return False
    def wait_any(self, poll_ms=10): return 'A'
