# menu_style_a_bench.py: the built DR-072 style-A menu from hwtest/stage/pocket.py (branch flop-game),
# as hwtest/stage/pocket_nomain.py (the file minus its trailing main(), imported, not exec'd: the
# source string would fragment the heap before the framebuffer) so draw_menu()/menu_select() run as shipped. Forces the no-photo
# path (ctx.menu_art = False) for the style-A numbers, then the photo path (John's board has the file):
# entry, joystick moves (two bands), a scroll (three-row band), RAM. Board untouched.
import sys, gc, utime
sys.path.insert(0, '/remote/stage')
import pocket_nomain                      # stage copy of pocket.py without its trailing main() (made by stage_from + sed)
ns = pocket_nomain.__dict__
gc.collect(); print("RESULT after_pocket_setup mem_free=%d" % gc.mem_free())
lcd = ns['lcd']; Assets = ns['Assets']; Bankroll = ns['Bankroll']; Buttons = ns['Buttons']
def run(photo):
    ctx = ns['Ctx'](); ctx.lcd = lcd; ctx.assets = Assets('/assets'); ctx.bankroll = Bankroll(1000); ctx.buttons = Buttons()
    if not photo: ctx.menu_art = False
    tag = 'photo' if ns['has_menu_art'](ctx) else 'styleA'
    gc.collect(); m0 = gc.mem_free()
    es = []
    for _ in range(3):
        t0 = utime.ticks_us(); ns['draw_menu'](ctx, 0); es.append(utime.ticks_diff(utime.ticks_us(), t0))
    print("RESULT %s entry_us: mean=%d max=%d" % (tag, sum(es) // 3, max(es)))
    top = 0; ts = []
    for old, new in ((0, 1), (1, 2), (2, 1), (1, 0), (0, 1), (1, 0)):
        t0 = utime.ticks_us(); top = ns['menu_select'](ctx, old, new, top); ts.append(utime.ticks_diff(utime.ticks_us(), t0))
    print("RESULT %s joystick_move_two_bands_us: mean=%d max=%d" % (tag, sum(ts) // len(ts), max(ts)))
    ss = []
    top = 0
    for old, new in ((2, 3), (3, 2), (2, 3), (3, 2)):          # row 3 ('Off') is off screen: a scroll
        t0 = utime.ticks_us(); top = ns['menu_select'](ctx, old, new, top); ss.append(utime.ticks_diff(utime.ticks_us(), t0))
    print("RESULT %s scroll_three_row_band_us: mean=%d max=%d" % (tag, sum(ss) // len(ss), max(ss)))
    gc.collect(); print("RESULT %s mem_free_before=%d after=%d (retained=%d)" % (tag, m0, gc.mem_free(), m0 - gc.mem_free()))
run(False)
run(True)
print("RESULT menu left on screen (photo path, as John's board shows it)")
