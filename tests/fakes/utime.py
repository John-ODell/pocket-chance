# Fake `utime` for CPython tests. Sleeps are no-ops so tests run fast.
import time

_t0 = time.perf_counter()


def sleep_ms(ms):
    pass


def sleep_us(us):
    pass


def sleep(s):
    pass


def ticks_us():
    return int((time.perf_counter() - _t0) * 1e6)


def ticks_ms():
    return ticks_us() // 1000


def ticks_diff(a, b):
    return a - b
