# menu_tour_bench.py: does memory come back when John leaves a game? Runs the staged pocket.py's own
# play() (as pocket_nomain, no main()) for each of the four games in turn, entering with the real
# imports and leaving at once with B from the betting screen, twice round. Prints free RAM at the menu
# after each visit and which game modules stay in sys.modules. John's saves are snapshotted and
# restored; nothing is written to the board's filesystem otherwise.
import sys, gc, os
sys.path.insert(0, '/remote/stage')
if '/games' not in sys.path: sys.path.append('/games')
SAVES = ('/save.json', '/save.bak'); snap = {}
for p in SAVES:
    with open(p, 'rb') as f: snap[p] = f.read()
try:
    import pocket_nomain as P
    class Keys:
        def __init__(self): self.q = []
        def poll(self):
            q = self.q; self.q = []; return q
        def held(self, n): return False
        def wait_any(self, poll_ms=10): return 'A'
    ctx = P.Ctx(); ctx.lcd = P.lcd; ctx.buttons = Keys(); ctx.assets = P.Assets('/assets')
    ctx.store = P.Store('/_bench_save.json'); ctx.car_seats = P.CAR_SEATS; ctx.uth_seats = P.UTH_SEATS
    ctx.uth_hint = P.UTH_HINT; ctx.bac_seats = P.BAC_SEATS; ctx.rng = P.random; ctx.bankroll = P.Bankroll(1000)
    ctx.assets.use_sheets(('icons',)); P.draw_menu(ctx, 0, 0)
    base = set(sys.modules)
    gc.collect(); print("RESULT menu_start free=%d" % gc.mem_free())
    for lap in (1, 2):
        for mod in ('blackjack', 'holdem', 'caribbean', 'baccarat'):
            ctx.buttons.q = ['B']
            P.play(ctx, mod)
            P.draw_menu(ctx, 0, 0)
            gc.collect()
            extra = sorted(m for m in sys.modules if m not in base)
            print("RESULT lap %d after %-9s free=%6d  game modules still loaded=%s" % (lap, mod, gc.mem_free(), extra))
finally:
    for p, d in snap.items():
        with open(p, 'wb') as f: f.write(d)
    for f in ('/_bench_save.json', '/_bench_save.bak'):
        try: os.remove(f)
        except OSError: pass
    print("RESULT john_save_files_restored=%s" % [(p, len(d)) for p, d in snap.items()])
