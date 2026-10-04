# clk_peri_fix.py: re-source clk_peri from clk_sys (125 MHz) so SPI can reach 62.5 MHz again.
# Datasheet 2.15.3.2: clk_peri has only an aux mux, so clear ENABLE, wait, set AUXSRC=0 (clk_sys),
# set ENABLE. Only UART baud generation depends on clk_peri; the USB REPL does not. Undone by reset.
import machine, utime
from machine import SPI, Pin
CTRL = 0x40008000 + 0x48
def spi_granted():
    s = SPI(1, 62_500_000, polarity=0, phase=0, sck=Pin(10), mosi=Pin(11), miso=None)
    r = repr(s); i = r.find('baudrate=') + 9; j = i
    while r[j].isdigit(): j += 1
    s.deinit(); return int(r[i:j])
v = machine.mem32[CTRL]
machine.mem32[CTRL] = v & ~(1 << 11)          # disable
utime.sleep_us(10)
machine.mem32[CTRL] = (v & ~(7 << 5)) & ~(1 << 11)   # auxsrc = 0 = clk_sys, still disabled
machine.mem32[CTRL] = (v & ~(7 << 5)) | (1 << 11)    # enable
utime.sleep_us(10)
print("RESULT after poke: CLK_PERI_CTRL=0x%08x spi_granted=%d" % (machine.mem32[CTRL], spi_granted()))
from lcdbench import Bench
b = Bench(baud=62_500_000); b.fb.fill(0x07E0); b.show()
ts = []
for i in range(50):
    b.fb.fill((0xF800, 0x07E0, 0x001F, 0xFFFF)[i & 3]); t = utime.ticks_us(); b.show(); ts.append(utime.ticks_diff(utime.ticks_us(), t))
print("RESULT frame_wire_us_mean=%d fps_wire=%.1f granted=%s" % (sum(ts)//50, 1e6*50/sum(ts), b.granted))
b.blank()
