# stage_bench.py: bench a NOT-YET-UPLOADED build. Files copied into hwtest/stage/ are put first on
# sys.path (the bench folder is mounted at /remote), so the real program runs the new lib/ and
# pocket.py while the board's own files are untouched. Scripted blackjack keys from fakes_bj/.
# John's save files are snapshotted and restored.
import sys, gc, os
sys.path.insert(0, '/remote/fakes_bj'); sys.path.insert(0, '/remote/stage'); sys.path.append('/')
SAVES = ('/save.json', '/save.bak'); snap = {}
for p in SAVES:
    try:
        with open(p, 'rb') as f: snap[p] = f.read()
    except OSError: snap[p] = None
gc.collect(); print("RESULT before_import free=%d staged=%s" % (gc.mem_free(), sorted(os.listdir('/remote/stage'))))
try:
    import pocket
except SystemExit as e:
    print("RESULT script finished: %s" % (e,))
finally:
    for p, data in snap.items():
        if data is None:
            try: os.remove(p)
            except OSError: pass
        else:
            with open(p, 'wb') as f: f.write(data)
    print("RESULT john_save_files_restored=%s" % [(p, len(d) if d else None) for p, d in snap.items()])
import art, lcd, sheets
print("RESULT modules_used: art=%s lcd=%s sheets=%s pocket=%s" % (art.__file__, lcd.__file__, sheets.__file__, pocket.__file__ if 'pocket' in dir() else '?'))
