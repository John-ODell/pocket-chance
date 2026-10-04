# Fake `machine` for running board code under CPython in tests. Not uploaded to the board.


class Pin:
    OUT = 1
    IN = 0
    PULL_UP = 1
    registry = {}      # gpio -> Pin, so tests can press buttons

    def __init__(self, gpio, mode=0, pull=None, value=None):
        self.gpio = gpio
        self.mode = mode
        self._v = 1 if value is None else value
        Pin.registry[gpio] = self

    def value(self, v=None):
        if v is None:
            return self._v
        self._v = v

    def __call__(self, v=None):
        return self.value(v)


class SPI:
    def __init__(self, idx, baudrate=1000000, **kw):
        self.idx = idx
        self.baudrate = baudrate
        self.written = 0

    def write(self, data):
        self.written += len(data)

    def deinit(self):
        pass


class PWM:
    def __init__(self, pin):
        self.duty = 0

    def freq(self, f):
        pass

    def duty_u16(self, d):
        self.duty = d


class _Mem:
    def __init__(self):
        self.regs = {0x40008048: 0x840}

    def __getitem__(self, addr):
        return self.regs.get(addr, 0)

    def __setitem__(self, addr, v):
        self.regs[addr] = v & 0xFFFFFFFF


mem32 = _Mem()


freq_calls = []


def freq(*args):
    """machine.freq() reads; machine.freq(cpu, peri) sets (recorded for tests)."""
    if args:
        freq_calls.append(args)
        return None
    return 125000000
