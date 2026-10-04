# unwedge.py: MAC-SIDE tool, not for the board. Run with the python that has pyserial, e.g.
#   "$HOME/Library/Application Support/pipx/venvs/mpremote/bin/python" hwtest/unwedge.py [port]
#
# Why: if an `mpremote exec` is killed while the board is running (a background run that hits its
# time limit, a closed terminal), the board stays in RAW-REPL mode with the program still running.
# The next `mpremote connect ...` then fails with "could not enter raw repl" even though the board
# is perfectly healthy. This happened twice on 2026-10-04 and cost one needless unplug.
# Fix: interrupt (Ctrl-C), return to the friendly REPL (Ctrl-B), soft reboot (Ctrl-D). Harmless:
# nothing on the filesystem is touched; with no main.py the board comes up idle at the REPL.
import sys, time, glob
import serial

ports = sys.argv[1:] or sorted(glob.glob('/dev/cu.usbmodem*'))
if not ports:
    sys.exit("no /dev/cu.usbmodem* port found")
port = ports[0]
p = serial.Serial(port, 115200, timeout=0.3)

def drain(secs):
    t = time.time(); buf = b''
    while time.time() - t < secs:
        buf += p.read(4096)
    return buf

drain(0.5)
p.write(b'\r\x03\x03'); drain(1.0)           # interrupt whatever runs
p.write(b'\r\x02'); drain(1.0)               # friendly REPL
p.write(b'\x04'); out = drain(3.0)           # soft reboot
p.write(b'print("UNWEDGE_OK")\r'); out += drain(1.0)
p.close()
ok = b'UNWEDGE_OK' in out
print("%s: %s" % (port, "board at friendly REPL, soft rebooted; mpremote will connect now" if ok else "no answer, try unplugging"))
print(out[-200:].decode('utf-8', 'replace'))
sys.exit(0 if ok else 1)
