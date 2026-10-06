# stage_bench_bac.py: the REAL pocket.py from hwtest/stage/ (main b102960, step 1q) end to end with
# hwtest/fakes_bac/buttons.py scripting a Baccarat session. John's save files snapshotted and restored.
import sys, gc, os
sys.path.insert(0, '/remote/fakes_bac')
sys.path.insert(0, '/remote/stage')
sys.path.append('/')
SAVES = ('/save.json', '/save.bak')
snap = {}
for p in SAVES:
    try:
        with open(p, 'rb') as f: snap[p] = f.read()
    except OSError: snap[p] = None
gc.collect(); print("RESULT before_import_pocket free=%d" % gc.mem_free())
try:
    import pocket
    print("RESULT pocket_from=%s" % pocket.__file__)
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
gc.collect(); print("RESULT after_exit free=%d" % gc.mem_free())
