# blit_bench.py: HR-F03 re-check. One 40x56 card blit from flash: first call (stat + header) vs
# cached calls, via the real lib/art.py; background_rows slice; Assets.load/LCD.show_buf if present.
# Then RAM headroom for DR-020 rev 2 option A (6 slots + compose = 43.9 KB) with the menu set up.
import gc, utime, os, framebuf
src = open('/pocket.py').read(); src = src[:src.rstrip().rfind('main()')]
ns = {'__name__': 'blit_bench_ns'}; exec(src, ns)
lcd = ns['lcd']; Assets = ns['Assets']
W, H = 40, 56; N = W * H * 2
with open('/assets/_bench_card.565', 'wb') as f:
    f.write(bytes([W, 0, H, 0])); f.write(bytes([0xFF, 0xFF]) * (W * H))
a = Assets('/assets')
t = []
for i in range(6):
    t0 = utime.ticks_us(); ok = a.blit(lcd, '_bench_card', 10, 10); t.append(utime.ticks_diff(utime.ticks_us(), t0))
print("RESULT card_blit_us first=%d cached=%s ok=%s (old art.py: ~8000 every call)" % (t[0], t[1:], ok))
t0 = utime.ticks_us(); a.background_rows(lcd, 'menu_background', 70, 48); print("RESULT background_rows_48_us=%d" % utime.ticks_diff(utime.ticks_us(), t0))
t0 = utime.ticks_us(); a.background_rows(lcd, 'menu_background', 70, 48); print("RESULT background_rows_48_cached_us=%d" % utime.ticks_diff(utime.ticks_us(), t0))
if hasattr(a, 'load'):
    buf = bytearray(N)
    try:
        t0 = utime.ticks_us(); r = a.load('_bench_card', buf); print("RESULT Assets.load_us=%d returned=%r" % (utime.ticks_diff(utime.ticks_us(), t0), r))
    except Exception as e:
        print("RESULT Assets.load error=%r" % (e,))
if hasattr(lcd, 'show_buf'):
    buf2 = bytearray(56 * 56 * 2)
    t0 = utime.ticks_us(); lcd.show_buf(18, 100, 56, 56, buf2); print("RESULT LCD.show_buf_56x56_us=%d" % utime.ticks_diff(utime.ticks_us(), t0))
os.remove('/assets/_bench_card.565')
gc.collect(); free0 = gc.mem_free()
print("RESULT ram_menu_ready=%d (pocket set up, no game module)" % free0)
slots = [bytearray(6272) for _ in range(6)]; comp = bytearray(6272)
gc.collect(); print("RESULT ram_after_6_slots_plus_compose=%d (cost %d)" % (gc.mem_free(), free0 - gc.mem_free()))
try:
    big = bytearray(16384); print("RESULT plus_16KB_scratch_fits free=%d" % gc.mem_free()); del big
except MemoryError:
    print("RESULT plus_16KB_scratch=does_not_fit")
del slots, comp; gc.collect()
import sys
if '/games' not in sys.path: sys.path.append('/games')
gc.collect(); b0 = gc.mem_free(); import blackjack; gc.collect()
print("RESULT blackjack_module_cost=%d free_with_blackjack=%d (slots screen module will be similar)" % (b0 - gc.mem_free(), gc.mem_free()))
print("RESULT cleanup assets=%s" % os.listdir('/assets'))
lcd.fill(0); lcd.show()
