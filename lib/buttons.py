# Buttons and joystick on the Waveshare 1.3" LCD HAT. Active low with pull-ups (0 = pressed).
# Pin map verified on the board (hw/BUDGET.md, Input, 2026-10-04). No bounce was measured, so a
# press is the falling edge and the key is ignored until released (edge detect, not level).

from machine import Pin

PINS = (
    ('A', 15), ('B', 17), ('X', 19), ('Y', 21),
    ('UP', 2), ('DOWN', 18), ('LEFT', 16), ('RIGHT', 20), ('PRESS', 3),
)


class Buttons:
    def __init__(self):
        self.names = [n for n, _ in PINS]
        self.pins = [Pin(g, Pin.IN, Pin.PULL_UP) for _, g in PINS]
        self.last = [1] * len(PINS)

    def poll(self):
        """Return the list of key names that went down since the last poll (usually empty)."""
        hit = []
        pins = self.pins
        last = self.last
        for i in range(len(pins)):
            v = pins[i].value()
            if v == 0 and last[i] == 1:
                hit.append(self.names[i])
            last[i] = v
        return hit

    def held(self, name):
        return self.pins[self.names.index(name)].value() == 0

    def wait_any(self, poll_ms=10):
        """Block until a key goes down; return its name. For simple prompt screens."""
        import utime
        while True:
            hit = self.poll()
            if hit:
                return hit[0]
            utime.sleep_ms(poll_ms)
