# Stand-in for lib/buttons.py used ONLY by hwtest/pocket_scripted.py: feeds scripted keys to the
# real pocket.py instead of reading pins. Put /remote/fakes first on sys.path before `import pocket`.
SCRIPT = ['DOWN', 'A', 'A', 'A', 'B']          # to Slots, enter, spin, spin, back to menu
PINS = ()
class Buttons:
    def __init__(self): self.idle = 0
    def poll(self):
        if SCRIPT: return [SCRIPT.pop(0)]
        self.idle += 1
        if self.idle > 3: raise SystemExit('script done')
        return []
    def held(self, name): return False
    def wait_any(self, poll_ms=10): return 'A'
