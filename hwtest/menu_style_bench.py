# menu_style_bench.py: DR-072 menu styles, the drawing costs of each option's primitive mix on the real
# LCD (no menu code exists yet): A's 60-strip shade, double border, 3 pills with ellipse ends, suit
# signs, text and one show(); B's 24 bulbs, a 12-row band push (the chase step) and the idle-loop CPU
# share at 150 ms; C's cream panels and 8 mini cards. Numbers for HR-072; the built menu is benched later.
import gc, utime, machine
machine.freq(125_000_000, 125_000_000)
from lcd import LCD
from pixfmt import rgb
import font
lcd = LCD(62_500_000); gc.collect()
GOLD = rgb(240, 200, 60); CREAM = rgb(240, 232, 200); WHITE = rgb(255, 255, 255); BLACK = 0
def timed(name, fn, n=5):
    xs = []
    for _ in range(n):
        t0 = utime.ticks_us(); fn(); xs.append(utime.ticks_diff(utime.ticks_us(), t0))
    print("RESULT %s: mean_us=%d max_us=%d" % (name, sum(xs) // n, max(xs)))
def shade():
    for i in range(60):
        lcd.fill_rect(0, i * 4, 240, 4, rgb(0, 70 + i // 2, 30 + i // 4))
def border():
    for d in (4, 6):
        lcd.rect(d, d, 240 - 2 * d, 240 - 2 * d, GOLD)
def pills():
    for k, y in enumerate((70, 118, 166)):
        col = (rgb(0, 90, 40), rgb(20, 40, 110), rgb(110, 20, 30))[k]
        lcd.fill_rect(40, y, 160, 48, col)
        lcd.ellipse(40, y + 24, 24, 24, col, True); lcd.ellipse(200, y + 24, 24, 24, col, True)
        lcd.ellipse(212, y + 24, 6, 6, GOLD, True); lcd.ellipse(212, y + 24, 6, 6, WHITE, False)
        font.text(lcd, 'Blackjack', 72, y + 16, CREAM, 2)
def suits():
    for y in (70, 118, 166):
        lcd.ellipse(30, y + 20, 6, 6, CREAM, True); lcd.ellipse(22, y + 26, 6, 6, CREAM, True); lcd.ellipse(38, y + 26, 6, 6, CREAM, True)
        lcd.fill_rect(28, y + 28, 4, 12, CREAM)
def plaque():
    lcd.fill_rect(80, 40, 80, 20, CREAM); lcd.fill_rect(76, 44, 88, 12, CREAM)
    for x, y in ((80, 44), (160, 44), (80, 56), (160, 56)): lcd.ellipse(x, y, 4, 4, CREAM, True)
    font.text_centred(lcd, '$1000', 120, 46, BLACK, 1)
def title():
    font.text(lcd, 'Pocket Chance', 29, 13, BLACK, 2); font.text(lcd, 'Pocket Chance', 28, 12, GOLD, 2)
def style_a():
    shade(); border(); title(); plaque(); pills(); suits(); font.text_centred(lcd, 'A select', 120, 226, CREAM, 1); lcd.show()
timed("A_shade_60_strips", shade); timed("A_pills_3", pills); timed("A_suits_3", suits); timed("A_plaque", plaque)
timed("A_full_entry_with_show", style_a)
# B: bulbs and the chase
def bulbs():
    for i in range(24):
        if i < 8: x, y = 12 + i * 31, 6
        elif i < 12: x, y = 233, 40 + (i - 8) * 50
        elif i < 20: x, y = 229 - (i - 12) * 31, 233
        else: x, y = 6, 190 - (i - 20) * 50
        lcd.ellipse(x, y, 3, 3, GOLD if i % 3 == 0 else rgb(60, 50, 10), True)
timed("B_24_bulbs_draw", bulbs)
def chase_step():
    lcd.fill_rect(0, 0, 240, 12, 0); bulbs(); lcd.show_band(0, 12); lcd.show_band(228, 12)
timed("B_chase_step_top_bottom_bands", chase_step)
scratch = bytearray(16 * 1024)
timed("B_show_rect_12x240_side (16 KB scratch)", lambda: lcd.show_rect(0, 0, 12, 240, scratch))
timed("B_show_rect_12x240_both_sides", lambda: (lcd.show_rect(0, 0, 12, 240, scratch), lcd.show_rect(228, 0, 12, 240, scratch)))
def pill_row(y, col, sel):
    for i in range(y // 4, (y + 48) // 4): lcd.fill_rect(0, i * 4, 240, 4, rgb(0, 70 + i // 2, 30 + i // 4))
    lcd.fill_rect(40, y, 160, 48, col); lcd.ellipse(40, y + 24, 24, 24, col, True); lcd.ellipse(200, y + 24, 24, 24, col, True)
    if sel: lcd.ellipse(212, y + 24, 6, 6, GOLD, True); lcd.ellipse(212, y + 24, 6, 6, WHITE, False)
    font.text(lcd, 'Blackjack', 72, y + 16, CREAM, 2); lcd.show_band(y, 48)
timed("A_scroll_two_row_bands (redraw + push each)", lambda: (pill_row(70, rgb(0, 90, 40), False), pill_row(118, rgb(20, 40, 110), True)))
def pill_rect_ends(y, col):
    for i in range(y // 4, (y + 48) // 4): lcd.fill_rect(0, i * 4, 240, 4, rgb(0, 70 + i // 2, 30 + i // 4))
    lcd.fill_rect(16, y, 208, 48, col); lcd.fill_rect(12, y + 4, 216, 40, col); lcd.fill_rect(8, y + 8, 224, 32, col)
    font.text(lcd, 'Blackjack', 72, y + 16, CREAM, 2); lcd.show_band(y, 48)
timed("A_alt_row_band_stepped_pill_no_ellipse", lambda: pill_rect_ends(70, rgb(0, 90, 40)))
timed("ellipse_r24_filled_alone", lambda: lcd.ellipse(120, 120, 24, 24, GOLD, True))
timed("ellipse_r6_filled_alone", lambda: lcd.ellipse(120, 120, 6, 6, GOLD, True))
timed("B_full_show", lcd.show)
# C: panels and mini cards (poly fan approximated as a second offset rect)
def style_c():
    lcd.fill(rgb(0, 60, 25)); lcd.rect(4, 4, 232, 232, GOLD)
    for y in (70, 118, 166):
        lcd.fill_rect(56, y + 4, 168, 40, CREAM); lcd.rect(56, y + 4, 168, 40, GOLD)
        for dx in (0, 8):
            lcd.fill_rect(16 + dx, y + 10, 20, 28, CREAM); lcd.rect(16 + dx, y + 10, 20, 28, BLACK)
            lcd.poly(16 + dx, y + 10, bytearray(), BLACK) if False else None
            font.text(lcd, 'A', 19 + dx, y + 12, rgb(200, 20, 20), 1)
        font.text(lcd, 'Blackjack', 64, y + 16, BLACK, 2)
    lcd.show()
timed("C_full_entry_with_show", style_c)
gc.collect(); print("RESULT mem_free=%d" % gc.mem_free())
