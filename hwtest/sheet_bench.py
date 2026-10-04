# sheet_bench.py: DR-024. Writes two temporary sprite sheets (8 x 56x56 symbols; 53 x 40x56 cards),
# then measures: open once; per sprite seek + readinto + keyed blit; reel rows (8 rows) from the
# open sheet; versus the per-file path (open per sprite) on a temp single card. Removes the temps.
import gc, utime, os, framebuf
from clocks import fast_peripherals; fast_peripherals()
from lcd import LCD
lcd = LCD(62_500_000); gc.collect()
from art import Assets
from pixfmt import KEY, KEY_BE
def write_sheet(path, w, h, n):
    with open(path, 'wb') as f:
        f.write(bytes([w & 255, w >> 8, (h * n) & 255, (h * n) >> 8]))
        row = bytes([0x12, 0x34]) * w; keyrow = bytes([KEY_BE >> 8, KEY_BE & 255]) * w
        for k in range(n):
            for y in range(h): f.write(keyrow if y < 4 else row)
t0 = utime.ticks_ms(); write_sheet('/assets/_bench_symbols.565', 56, 56, 8); write_sheet('/assets/_bench_cards.565', 40, 56, 53)
write_sheet('/assets/_bench_card1.565', 40, 56, 1)
print("RESULT wrote sheets in %d ms: symbols=%d B cards=%d B" % (utime.ticks_diff(utime.ticks_ms(), t0), os.stat('/assets/_bench_symbols.565')[6], os.stat('/assets/_bench_cards.565')[6]))
scratch = bytearray(16384); mv = memoryview(scratch)
t0 = utime.ticks_us(); f = open('/assets/_bench_cards.565', 'rb'); t_open = utime.ticks_diff(utime.ticks_us(), t0)
N = 40 * 56 * 2; card = framebuf.FrameBuffer(mv[:N], 40, 56, framebuf.RGB565)
ts_read, ts_blit = [], []
for n in (0, 12, 25, 38, 52, 7, 44, 19):
    t0 = utime.ticks_us(); f.seek(4 + n * N); f.readinto(mv[:N]); t1 = utime.ticks_us(); lcd.blit(card, 20, 20, KEY); t2 = utime.ticks_us()
    ts_read.append(utime.ticks_diff(t1, t0)); ts_blit.append(utime.ticks_diff(t2, t1))
print("RESULT cards_sheet: open_once_us=%d per_card_seek_read_us mean=%d max=%d keyed_blit_us mean=%d -> per_card_total_us=%d" %
      (t_open, sum(ts_read) // 8, max(ts_read), sum(ts_blit) // 8, (sum(ts_read) + sum(ts_blit)) // 8))
f.close()
a = Assets('/assets')
ts = []
for _ in range(5):
    t0 = utime.ticks_us(); a.blit(lcd, '_bench_card1', 80, 20); ts.append(utime.ticks_diff(utime.ticks_us(), t0))
print("RESULT per_file_card_blit_us first=%d cached=%d (today's path)" % (ts[0], sum(ts[1:]) // 4))
f = open('/assets/_bench_symbols.565', 'rb'); S = 56; RB = S * 2
ts = []
for k in range(21):
    sym = k % 8; first = (k * 8) % 56
    t0 = utime.ticks_us(); f.seek(4 + sym * S * RB + first * RB); f.readinto(mv[:8 * RB]); ts.append(utime.ticks_diff(utime.ticks_us(), t0))
print("RESULT symbols_sheet: 8_rows_seek_read_us mean=%d max=%d (what a reel reads per frame; no open per symbol change)" % (sum(ts) // len(ts), max(ts)))
f.close()
t0 = utime.ticks_us(); f = open('/assets/_bench_symbols.565', 'rb'); f.close(); print("RESULT open_close_symbol_file_us=%d (what each symbol change costs today)" % utime.ticks_diff(utime.ticks_us(), t0))
for p in ('/assets/_bench_symbols.565', '/assets/_bench_cards.565', '/assets/_bench_card1.565'): os.remove(p)
print("RESULT cleanup assets=%s" % os.listdir('/assets'))
lcd.fill(0); lcd.show()
