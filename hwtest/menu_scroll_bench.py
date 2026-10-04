# menu_scroll_bench.py: DR-022 five-item scrolling menu. Runs the REAL /pocket.py menu code (final
# main() stripped): times menu entry, a move inside the visible window (two row bands) and a move
# that scrolls (all three rows as one band), walking down the list and back; RAM; no human.
import gc, utime, os
src = open('/pocket.py').read(); src = src[:src.rstrip().rfind('main()')]
ns = {'__name__': 'menu_scroll_bench_ns'}; exec(src, ns)
gc.collect(); print("RESULT after_pocket_setup mem_free=%d" % gc.mem_free())
lcd = ns['lcd']; ctx = ns['Ctx'](); ctx.lcd = lcd
ctx.assets = ns['Assets']('/assets'); ctx.bankroll = ns['Bankroll'](1000); ctx.buttons = ns['Buttons']()
MENU, VISIBLE, top_for = ns['MENU'], ns['VISIBLE'], ns['top_for']
print("RESULT menu_items=%s visible=%d" % ([m[0] for m in MENU], VISIBLE))
t0 = utime.ticks_us(); ns['draw_menu'](ctx, 0, 0); print("RESULT menu_entry_us=%d" % utime.ticks_diff(utime.ticks_us(), t0))
sel, top = 0, 0; within, scroll = [], []
path = ['DOWN'] * (len(MENU) - 1) + ['UP'] * (len(MENU) - 1) + ['DOWN', 'DOWN', 'UP', 'UP']
for key in path:
    new = sel + (1 if key == 'DOWN' else -1)
    if not 0 <= new < len(MENU): continue
    scrolls = top_for(new, top) != top
    t0 = utime.ticks_us(); top = ns['menu_select'](ctx, sel, new, top); dt = utime.ticks_diff(utime.ticks_us(), t0)
    (scroll if scrolls else within).append(dt); sel = new
    print("RESULT move %s -> sel=%d top=%d %s us=%d" % (key, sel, top, 'SCROLL' if scrolls else 'within', dt))
def rep(n, xs): print("RESULT %s n=%d mean_us=%d max_us=%d" % (n, len(xs), sum(xs) // len(xs), max(xs))) if xs else None
rep("move_within_window", within); rep("move_with_scroll", scroll)
gc.collect(); print("RESULT end mem_free=%d" % gc.mem_free())
ns['draw_menu'](ctx, 0, 0); print("RESULT leaving menu on screen, top row selected")
