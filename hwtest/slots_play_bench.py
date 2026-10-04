# slots_play_bench.py: the slots screen AS BUILT (step 1g), scripted keys. Shims the module's utime
# so each frame's spent time (FRAME_US - sleep) is logged, tags frames where a reel changed symbol,
# times spin() end to end, the save and the blink, and lets the screen print its own mid-spin
# mem_free. Spins until a win has blinked (max 25). Saves go to /_bench_save.* and are removed.
import sys, gc, utime, os
src = open('/pocket.py').read(); src = src[:src.rstrip().rfind('main()')]
ns = {'__name__': 'slots_play_bench_ns'}; exec(src, ns)
lcd = ns['lcd']
if '/games' not in sys.path: sys.path.append('/games')
gc.collect(); f0 = gc.mem_free()
import slots
gc.collect(); print("RESULT slots_module_cost=%d free=%d" % (f0 - gc.mem_free(), gc.mem_free()))
from save import Store
import random
class Keys:
    def poll(self): return []
    def wait_any(self): return 'A'
ctx = ns['Ctx'](); ctx.lcd = lcd; ctx.assets = ns['Assets']('/assets'); ctx.buttons = Keys()
ctx.store = Store('/_bench_save.json'); ctx.rng = random; ctx.bankroll = ns['Bankroll'](1000)
random.seed(4242)
spent, change_frames, frame_idx = [], set(), [0]
class U:                                    # utime shim: same clock, logs the pacing sleep
    ticks_us = staticmethod(utime.ticks_us); ticks_diff = staticmethod(utime.ticks_diff)
    ticks_ms = staticmethod(utime.ticks_ms); sleep_ms = staticmethod(utime.sleep_ms)
    @staticmethod
    def sleep_us(n):
        spent.append(slots.FRAME_US - n); frame_idx[0] += 1; utime.sleep_us(n)
slots.utime = U
scr = slots.Screen(ctx)
gc.collect(); print("RESULT after_screen_init free=%d (3 window buffers + patterns)" % gc.mem_free())
real_begin = scr.begin_incoming
def tagged_begin(i, sym): change_frames.add(frame_idx[0]); return real_begin(i, sym)
scr.begin_incoming = tagged_begin
real_save = ctx.store.save; save_t = []
def timed_save(b): t0 = utime.ticks_us(); real_save(b); save_t.append(utime.ticks_diff(utime.ticks_us(), t0))
ctx.store.save = timed_save
real_blink = scr.blink; blink_t = []
def timed_blink(): t0 = utime.ticks_us(); real_blink(); blink_t.append(utime.ticks_diff(utime.ticks_us(), t0))
scr.blink = timed_blink
scr.draw_all()
t0 = utime.ticks_us(); scr.handle('RIGHT'); print("RESULT bet_change_us=%d" % utime.ticks_diff(utime.ticks_us(), t0))
spins = 0; wins = 0; spin_t = []
while spins < 25 and not blink_t:
    spent.clear(); change_frames.clear(); frame_idx[0] = 0
    t0 = utime.ticks_us(); scr.handle('A'); dt = utime.ticks_diff(utime.ticks_us(), t0); spin_t.append(dt)
    spins += 1
    overrun = sum(1 for s in spent if s >= slots.FRAME_US)
    # frames with a symbol change vs the rest; the frame index logged at sleep time is the frame just finished
    ch = [spent[i] for i in change_frames if i < len(spent)]
    st = [spent[i] for i in range(len(spent)) if i not in change_frames]
    win, label = scr.table.last
    print("RESULT spin#%d frames=%d steady_mean_us=%d steady_max_us=%d change_frames=%d change_mean_us=%d change_max_us=%d overruns=%d total_ms=%d result=%s %s" %
          (spins, len(spent), sum(st) // max(1, len(st)), max(st) if st else 0, len(ch), sum(ch) // max(1, len(ch)), max(ch) if ch else 0, overrun, dt // 1000, win, label))
    if win: wins += 1
print("RESULT spins=%d wins=%d mid_spin_mem_free=%s" % (spins, wins, scr.mem_mid_spin))
if save_t: print("RESULT save_after_spin_us mean=%d max=%d n=%d" % (sum(save_t) // len(save_t), max(save_t), len(save_t)))
if blink_t: print("RESULT blink_3x_total_us=%d (includes 6 x 120 ms sleeps = 720 ms)" % blink_t[0])
t0 = utime.ticks_us(); scr.paytable(); print("RESULT paytable_draw_and_return_us=%d" % utime.ticks_diff(utime.ticks_us(), t0))
gc.collect(); print("RESULT end free=%d balance=%d" % (gc.mem_free(), scr.table.bankroll.balance))
for p in ('/_bench_save.json', '/_bench_save.bak', '/_bench_save.tmp', '/_bench_save.bad'):
    try: os.remove(p)
    except OSError: pass
print("RESULT cleanup root=%s" % os.listdir('/'))
