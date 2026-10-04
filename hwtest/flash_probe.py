# flash_probe.py: READ-ONLY. Is the flash chip really 16 MB? Reads the XIP window at several offsets.
# If the chip were 2 MB, reads above 2 MB mirror the start (addresses wrap) and match the first bytes.
# Real 16 MB: data differs from the start; erased area reads 0xFFFFFFFF.
import machine
base = 0x10000000
head = [machine.mem32[base + 4 * i] for i in range(4)]
print("RESULT head=%s" % ["%08x" % h for h in head])
for mb in (1, 2, 4, 8, 15, 16):
    off = mb * 1024 * 1024 - 16 if mb == 16 else mb * 1024 * 1024
    w = [machine.mem32[base + off + 4 * i] for i in range(4)]
    print("RESULT off=%dMB words=%s mirrors_start=%s" % (mb, ["%08x" % x for x in w], w == head))
