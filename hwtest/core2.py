# core2.py: does _thread help? Pushes frames on core 1 while core 0 draws into a second small
# buffer, vs doing both on core 0. Uses the same 115 KB framebuffer (no second full buffer fits).
from lcdbench import Bench
import utime, _thread, gc
b = Bench(baud=62_500_000)
N = 60
# baseline: draw then push, one core
t0 = utime.ticks_ms()
for i in range(N):
    b.fb.fill(i & 0xFFFF)
    for k in range(20): b.fb.fill_rect((k*11)%200, (k*7)%200, 30, 30, 0x07E0)
    b.show()
base = utime.ticks_diff(utime.ticks_ms(), t0)
print("RESULT core0_only_ms=%d fps=%.1f" % (base, N*1000/base))
# threaded: core1 pushes the frame while core0 draws the next (tearing allowed, it's a timing test)
done = [0]; go = [True]
def pusher():
    while go[0]:
        b.show(); done[0] += 1
    done.append('exit')
gc.collect()
try:
    _thread.start_new_thread(pusher, ())
    t0 = utime.ticks_ms()
    for i in range(N):
        b.fb.fill(i & 0xFFFF)
        for k in range(20): b.fb.fill_rect((k*11)%200, (k*7)%200, 30, 30, 0x07E0)
    draw = utime.ticks_diff(utime.ticks_ms(), t0)
    go[0] = False; utime.sleep_ms(100)
    print("RESULT core1_push_frames=%d while core0 drew %d frames in %d ms; draw_fps=%.1f push_fps=%.1f thread_exit=%s"
          % (done[0], N, draw, N*1000/draw, done[0]*1000/draw, done[-1]))
except Exception as e:
    print("RESULT thread_error=%r" % (e,))
b.blank()
