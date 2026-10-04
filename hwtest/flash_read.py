# flash_read.py: READ-ONLY. How fast can we stream an asset off the filesystem? Reads main.py
# (32 KB) into preallocated buffers of one row (480 B), ten rows (4800 B) and 32 KB, with readinto.
import utime, os
sz = os.stat('/main.py')[6]
for chunk in (480, 4800, 32768):
    buf = bytearray(chunk); mv = memoryview(buf)
    t0 = utime.ticks_us(); tot = 0
    for _ in range(4):
        with open('/main.py', 'rb') as f:
            while True:
                n = f.readinto(mv)
                if not n: break
                tot += n
    dt = utime.ticks_diff(utime.ticks_us(), t0)
    print("RESULT flash_read chunk=%d bytes=%d us=%d Bps=%d frame_115200_ms=%.1f" % (chunk, tot, dt, tot * 1e6 / dt, 115200 / (tot * 1e6 / dt) * 1000))
