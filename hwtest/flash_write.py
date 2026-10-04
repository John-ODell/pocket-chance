# flash_write.py: time a small save (bankroll-sized JSON, ~64 B) written to a NEW temp file, then
# removed. Also an atomic write (tmp + rename). Touches only /_hwtest_tmp*, never main.py.
import utime, os, json
data = json.dumps({"bankroll": 1234, "games": 57, "ver": 1})
ts = []
for i in range(10):
    t0 = utime.ticks_us()
    with open('/_hwtest_tmp.json', 'w') as f: f.write(data)
    ts.append(utime.ticks_diff(utime.ticks_us(), t0))
print("RESULT save_overwrite_us mean=%d min=%d max=%d n=10 bytes=%d" % (sum(ts)//10, min(ts), max(ts), len(data)))
ts = []
for i in range(10):
    t0 = utime.ticks_us()
    with open('/_hwtest_tmp.new', 'w') as f: f.write(data)
    os.rename('/_hwtest_tmp.new', '/_hwtest_tmp.json')
    ts.append(utime.ticks_diff(utime.ticks_us(), t0))
print("RESULT save_atomic_rename_us mean=%d min=%d max=%d n=10" % (sum(ts)//10, min(ts), max(ts)))
os.remove('/_hwtest_tmp.json')
print("RESULT cleanup listdir=%s" % os.listdir('/'))
