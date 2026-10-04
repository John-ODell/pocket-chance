# board_info.py: firmware, clock, filesystem and flash size. Read-only.
import os, sys, gc, machine
u = os.uname()
print("RESULT sysname=%s release=%s version=%s machine=%s" % (u.sysname, u.release, u.version, u.machine))
print("RESULT impl=%s" % (sys.implementation,))
print("RESULT cpu_hz=%d" % machine.freq())
vfs = os.statvfs('/')
bs, blocks, free = vfs[0], vfs[2], vfs[3]
print("RESULT fs_total_bytes=%d fs_free_bytes=%d block=%d" % (bs * blocks, bs * free, bs))
try:
    import rp2
    f = rp2.Flash()
    n, b = f.ioctl(4, 0), f.ioctl(5, 0)
    print("RESULT flash_block_dev_bytes=%d (ioctl count=%d size=%d)" % (n * b, n, b))
except Exception as e:
    print("RESULT flash_ioctl_error=%r" % (e,))
gc.collect()
print("RESULT ram_free=%d ram_alloc=%d" % (gc.mem_free(), gc.mem_alloc()))
print("RESULT unique_id=%s" % machine.unique_id().hex())
print("mounts:", os.listdir('/'))
