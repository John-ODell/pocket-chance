# Read-only board check. Run it on the board; it writes nothing.
# Prints the MicroPython version, free flash for files, and free RAM.
import gc
import os
import sys

gc.collect()
print('--- Pocket Chance board probe ---')
print('micropython:', sys.implementation)
print('uname      :', os.uname())
st = os.statvfs('/')
block = st[0]
print('flash total: %d KB' % (st[2] * block // 1024))
print('flash free : %d KB' % (st[3] * block // 1024))
print('RAM free   : %d bytes' % gc.mem_free())
print('RAM used   : %d bytes' % gc.mem_alloc())
print('files on /:', os.listdir('/'))
print('--- done ---')
