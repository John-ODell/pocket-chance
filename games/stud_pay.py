# Caribbean Stud paytable and strategy screen, kept out of stud.py so its code only occupies RAM
# while it is shown. Imported by stud.Screen.paytable() and dropped afterwards.

import font

ROWS = (('royal flush', 100), ('straight flush', 50), ('four of a kind', 20), ('full house', 7),
        ('flush', 5), ('straight', 4), ('three of a kind', 3), ('two pair', 2), ('pair or less', 1))


def show(lcd, buttons, ante, bg, gold, white, grey):
    lcd.fill(bg)
    font.text_centred(lcd, 'Raise pays (ante %d)' % ante, 120, 6, gold, 1)
    y = 20
    for label, mult in ROWS:
        font.text(lcd, label, 16, y, white, 1)
        font.text_right(lcd, '%d:1  %d' % (mult, mult * 2 * ante), 224, y, gold, 1)
        y += 11
    y += 4
    font.text_centred(lcd, 'Dealer needs ace-king', 120, y, grey, 1)
    y += 11
    font.text_centred(lcd, 'or better, else ante pays', 120, y, grey, 1)
    y += 15
    font.text(lcd, 'Raise: any pair or better.', 8, y, white, 1)
    y += 11
    font.text(lcd, 'Fold: below ace-king.', 8, y, white, 1)
    y += 11
    font.text(lcd, 'Ace-king: raise if dealer', 8, y, white, 1)
    y += 11
    font.text(lcd, 'card matches yours, or is', 8, y, white, 1)
    y += 11
    font.text(lcd, 'A/K and you hold Q or J.', 8, y, white, 1)
    font.text_centred(lcd, 'any key: back', 120, 228, grey, 1)
    lcd.show()
    buttons.wait_any()
