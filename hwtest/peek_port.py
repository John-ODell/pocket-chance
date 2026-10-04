# peek_port.py: read whatever a (possibly frozen) board has printed, WITHOUT resetting it,
# then send one Ctrl-C and read the KeyboardInterrupt traceback, which names the line the
# program was stuck on. Nothing is written to the filesystem; no soft reset is sent.
# Usage: <pipx mpremote venv python> hwtest/peek_port.py /dev/cu.usbmodemNNN [seconds]
import sys, time, serial
port = sys.argv[1]; wait = float(sys.argv[2]) if len(sys.argv) > 2 else 3.0
s = serial.Serial(port, 115200, timeout=0.2)
def drain(label, secs):
    t0 = time.time(); buf = b''
    while time.time() - t0 < secs:
        chunk = s.read(4096)
        if chunk: buf += chunk
    print("=== %s (%d bytes) ===" % (label, len(buf)))
    print(buf.decode('utf-8', 'replace'))
    return buf
drain("buffered output before touching the board", wait)
s.write(b'\r')                      # a bare newline: a live REPL echoes a prompt, a running program ignores it
a = drain("after newline", 1.5)
s.write(b'\x03')                    # Ctrl-C: interrupts a running program, prints the traceback
b = drain("after Ctrl-C", 3.0)
if b'>>>' in a or b'>>>' in b: print("RESULT interpreter_alive=True")
elif not a and not b: print("RESULT interpreter_alive=False (silent port: firmware hung, needs replug)")
else: print("RESULT interpreter_alive=unknown")
s.close()
