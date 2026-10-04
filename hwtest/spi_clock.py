# spi_clock.py: what SPI1 baud does the RP2040 actually grant, and what throughput results.
# Requests 100 MHz (old code), then 62.5/40/31.25/20 MHz. Sends 115200 bytes with CS high to the
# panel's idle state is not needed: we write inside a RAMWR window so the panel just swallows pixels.
from lcdbench import Bench, spi_baud, stats
import utime, gc
b = None
for req in (100_000_000, 62_500_000, 40_000_000, 31_250_000, 20_000_000):
    b = None; gc.collect()   # free the previous 115 KB framebuffer first
    b = Bench(baud=req, fb=True)
    b.fb.fill(0x1234)
    b.show()  # warm
    ts = []
    for _ in range(20):
        t = utime.ticks_us(); b.show(); ts.append(utime.ticks_diff(utime.ticks_us(), t))
    mean = sum(ts) / len(ts)
    print("RESULT spi_req=%d granted=%s frame_us=%d wire_Bps=%d wire_Mbit=%.1f" %
          (req, b.granted, mean, 115200 * 1e6 / mean, 115200 * 8 / mean))
    b.spi.deinit()
