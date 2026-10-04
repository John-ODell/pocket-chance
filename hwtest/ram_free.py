# ram_free.py: free RAM before/after the 115,200-byte framebuffer, largest free block,
# whether a second full framebuffer fits, and how much sprite cache is left.
import gc
gc.collect()
before = gc.mem_free()
print("RESULT ram_free_boot=%d" % before)

def largest():
    gc.collect()
    lo, hi = 0, gc.mem_free()
    while lo < hi - 256:
        mid = (lo + hi) // 2
        try:
            x = bytearray(mid); del x; lo = mid
        except MemoryError:
            hi = mid
        gc.collect()
    return lo

print("RESULT largest_block_boot=%d" % largest())
from lcdbench import Bench
b = Bench()
gc.collect()
after = gc.mem_free()
print("RESULT ram_free_with_fb_and_driver=%d used_by_fb_and_driver=%d" % (after, before - after))
print("RESULT largest_block_with_fb=%d" % largest())
try:
    second = bytearray(115200)
    print("RESULT second_fb=fits free_after=%d" % (gc.mem_free()))
    del second
except MemoryError:
    print("RESULT second_fb=does_not_fit")
gc.collect()
# what a 'typical' dev module set might cost: 40 KB of imports is simulated by allocation
for kb in (16, 32, 48, 64):
    try:
        x = bytearray(kb * 1024); print("RESULT sprite_cache_%dKB=fits free_after=%d" % (kb, gc.mem_free())); del x
    except MemoryError:
        print("RESULT sprite_cache_%dKB=does_not_fit" % kb)
    gc.collect()
b.blank()
