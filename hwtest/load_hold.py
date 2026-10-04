# load_hold.py: for John's multimeter. Puts the board at its heaviest steady draw: backlight PWM at
# 100 %, CPU busy redrawing and pushing full frames at 62.5 MHz, for DUR_S seconds, then backlight
# back to the game's default (20000/65535). Measure 3V3 (and VSYS if exposed) during the hold.
# Run: mpremote connect <port> mount hwtest exec "import load_hold"
DUR_S = 60
from clocks import fast_peripherals; fast_peripherals()
from lcd import LCD
import utime, gc
lcd = LCD(62_500_000, backlight=65535)
print("RESULT HOLD START: backlight 100%%, full-frame pushes, %d s. Measure 3V3 now." % DUR_S)
t_end = utime.ticks_add(utime.ticks_ms(), DUR_S * 1000); n = 0; c = 0
while utime.ticks_diff(t_end, utime.ticks_ms()) > 0:
    lcd.fill((0xF800, 0x07E0, 0x001F, 0xFFFF)[c & 3]); lcd.show(); c += 1
print("RESULT HOLD END: %d frames in %d s (%.1f fps)" % (c, DUR_S, c / DUR_S))
lcd.backlight(20000); lcd.fill(0); lcd.show()
print("RESULT backlight back to 20000/65535, screen black")
