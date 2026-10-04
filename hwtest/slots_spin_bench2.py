# slots_spin_bench2.py: DR-020, the fixed draw path. Symbols live in RAM (read once when they scroll
# in, not per frame); the compose buffer is pushed straight to the panel (no copy into the main
# framebuffer, no show_rect row loop). Three reels at 8 px/frame, reads only on the wrap frame.
# Also isolates: blit-from-RAM cost, and stat+open+readinto cost of one symbol file.
import gc, utime, os, framebuf, machine
from clocks import fast_peripherals, is_fast
fast_peripherals()
from lcd import LCD
lcd = LCD(62_500_000); gc.collect()
from pixfmt import rgb, KEY, KEY_BE
S = 56; N = S * S * 2
def write_sym(path, c1, c2):
    with open(path, 'wb') as f:
        f.write(bytes([S & 255, S >> 8, S & 255, S >> 8]))
        key = bytes([KEY_BE >> 8, KEY_BE & 255]) * S
        for y in range(S):
            c = c1 if (y // 8) & 1 else c2
            f.write(key if (y < 6 or y >= S - 6) else bytes([c >> 8, c & 255]) * S)
write_sym('/assets/_bench_sym0.565', 0xF800, 0xFFE0); write_sym('/assets/_bench_sym1.565', 0x07E0, 0x001F)
gc.collect(); m0 = gc.mem_free()
slots = [bytearray(N), bytearray(N)]                    # two symbol slots per reel would be 3 reels x 2; here shared
spr = [framebuf.FrameBuffer(b, S, S, framebuf.RGB565) for b in slots]
compose_buf = bytearray(N); compose = framebuf.FrameBuffer(compose_buf, S, S, framebuf.RGB565)
hdr = bytearray(4)
gc.collect(); print("RESULT ram_for_2_slots_plus_compose=%d bytes, free_after=%d" % (m0 - gc.mem_free(), gc.mem_free()))

def load(path, into):
    with open(path, 'rb') as f:
        f.readinto(hdr); f.readinto(into)
t0 = utime.ticks_us(); load('/assets/_bench_sym0.565', slots[0]); t_load = utime.ticks_diff(utime.ticks_us(), t0)
t0 = utime.ticks_us(); os.stat('/assets/_bench_sym1.565'); t_stat = utime.ticks_diff(utime.ticks_us(), t0)
load('/assets/_bench_sym1.565', slots[1])
t0 = utime.ticks_us(); compose.fill(0); compose.blit(spr[0], 0, -24, KEY); compose.blit(spr[1], 0, S - 24, KEY); t_blit2 = utime.ticks_diff(utime.ticks_us(), t0)
t0 = utime.ticks_us(); compose.blit(spr[0], 0, -24); t_blit_nokey = utime.ticks_diff(utime.ticks_us(), t0)
print("RESULT parts: open+read_one_symbol_us=%d stat_us=%d two_keyed_blits_from_ram_us=%d one_blit_no_key_us=%d" % (t_load, t_stat, t_blit2, t_blit_nokey))

WIN_X = (18, 92, 166); WIN_Y = 100
lcd.fill(rgb(40, 20, 10)); lcd.show()
def frame(reels, off, reload):
    for x in reels:
        if reload:                                      # the two straddling symbols changed
            load('/assets/_bench_sym0.565', slots[0]); load('/assets/_bench_sym1.565', slots[1])
        compose.fill(0)
        compose.blit(spr[0], 0, -off, KEY); compose.blit(spr[1], 0, S - off, KEY)
        lcd._window(x, WIN_Y, S, S); lcd._push(compose_buf)
def run(label, reels, frames=140):
    ts = []; wrap = []; off = 0
    for i in range(frames):
        reload = (off == 0)
        t0 = utime.ticks_us(); frame(reels, off, reload); dt = utime.ticks_diff(utime.ticks_us(), t0)
        (wrap if reload else ts).append(dt); off = (off + 8) % S
    print("RESULT %s: steady_mean_us=%d steady_max_us=%d fps=%.1f | wrap_frame(reads)_mean_us=%d n=%d" %
          (label, sum(ts) // len(ts), max(ts), 1e6 * len(ts) / sum(ts), sum(wrap) // len(wrap), len(wrap)))
run("3_reels_ram_sprites_direct_push_62M", WIN_X)
run("1_reel_ram_sprites_direct_push_62M", WIN_X[2:])
CTRL = 0x40008048; v = machine.mem32[CTRL]
machine.mem32[CTRL] = v & ~(1 << 11); utime.sleep_us(10)
machine.mem32[CTRL] = ((v & ~(7 << 5)) | (2 << 5)) & ~(1 << 11)
machine.mem32[CTRL] = (v & ~(7 << 5)) | (2 << 5) | (1 << 11); utime.sleep_us(10)
print("RESULT clock_now=%s" % ('fast' if is_fast() else 'usb_pll_48MHz_spi_24MHz'))
run("3_reels_ram_sprites_direct_push_24M", WIN_X)
fast_peripherals(); print("RESULT clock_restored=%s" % is_fast())
gc.collect(); print("RESULT end mem_free=%d" % gc.mem_free())
os.remove('/assets/_bench_sym0.565'); os.remove('/assets/_bench_sym1.565')
print("RESULT cleanup assets=%s" % os.listdir('/assets'))
lcd.fill(0); lcd.show()
