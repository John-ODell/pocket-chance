# pocket_scripted.py: runs the REAL /pocket.py program end to end (import pocket, nothing stripped)
# with hwtest/fakes/buttons.py standing in for the pin reader. Zero harness overhead inside the game,
# so the game's own RESULT lines (boot, import, mid-spin mem_free) are the true figures.
# Run: mpremote connect <port> mount hwtest exec "import pocket_scripted"
import sys, gc
sys.path.insert(0, '/remote/fakes')
sys.path.append('/')          # cwd is /remote while the bench folder is mounted
# The real program saves through /save.json. Snapshot John's save files first and put them back after.
import os
SAVES = ('/save.json', '/save.bak')
snap = {}
for p in SAVES:
    try:
        with open(p, 'rb') as f: snap[p] = f.read()
    except OSError: snap[p] = None
gc.collect(); print("RESULT before_import_pocket free=%d" % gc.mem_free())
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
gc.collect(); print("RESULT after_exit free=%d" % gc.mem_free())
