# menu_bench.py: D-007 menu background check. Loads the REAL /pocket.py source with its trailing
# main() call removed, so draw_menu()/menu_select() run exactly as shipped, then times menu entry,
# each joystick move (two 48-row bands), counts how many times the image file is opened, and
# reports RAM. Run: mpremote connect <port> mount hwtest exec "import menu_bench"
import sys, gc, utime
src = open('/pocket.py').read()
i = src.rstrip().rfind('main()')
src = src[:i]                                  # everything except the final main() call
ns = {'__name__': 'pocket_bench_ns'}
exec(src, ns)                                  # runs the clock fix, creates the LCD, imports libs
gc.collect(); print("RESULT after_pocket_setup mem_free=%d" % gc.mem_free())
lcd = ns['lcd']; Assets = ns['Assets']; Bankroll = ns['Bankroll']; Buttons = ns['Buttons']
ctx = ns['Ctx'](); ctx.lcd = lcd; ctx.assets = Assets('/assets'); ctx.bankroll = Bankroll(1000); ctx.buttons = Buttons()

opens = [0]; bg_time = [0]
real_open = ctx.assets._open
def counting_open(name):
    opens[0] += 1
    return real_open(name)
ctx.assets._open = counting_open
real_bg = ctx.assets.background
def timed_bg(l, name):
    t0 = utime.ticks_us(); r = real_bg(l, name); bg_time[0] = utime.ticks_diff(utime.ticks_us(), t0); return r
ctx.assets.background = timed_bg

print("RESULT image size=%s file_bytes=%d" % (ctx.assets.size('menu_background'), __import__('os').stat('/assets/menu_background.565')[6]))
opens[0] = 0
t0 = utime.ticks_us(); ns['draw_menu'](ctx, 0); entry = utime.ticks_diff(utime.ticks_us(), t0)
print("RESULT menu_entry_us=%d background_read_us=%d _open_calls_during_entry=%d (1 real read: background; the rest are size() and logo/icon probes answered from the missing-cache)" % (entry, bg_time[0], opens[0]))
opens[0] = 0
t0 = utime.ticks_us(); ns['draw_menu'](ctx, 0); entry2 = utime.ticks_diff(utime.ticks_us(), t0)
print("RESULT menu_entry_2nd_us=%d _open_calls=%d (1 real read + 3 cache hits for the missing logo and icons)" % (entry2, opens[0]))
moves = ((0, 1), (1, 2), (2, 1), (1, 0), (0, 1), (1, 0))
ts = []
for old, new in moves:
    opens[0] = 0
    t0 = utime.ticks_us(); ns['menu_select'](ctx, old, new); ts.append(utime.ticks_diff(utime.ticks_us(), t0))
print("RESULT joystick_move_us mean=%d max=%d n=%d _open_calls_per_move=%d (2 real slice reads + 2 cached icon misses; two band pushes)" % (sum(ts) // len(ts), max(ts), len(ts), opens[0]))
gc.collect(); print("RESULT end mem_free=%d" % gc.mem_free())
print("RESULT leaving the menu on screen, row 0 selected")
ns['draw_menu'](ctx, 0)
