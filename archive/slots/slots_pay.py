# Slots paytable screen, kept out of slots.py so its code only occupies RAM while it is shown
# (HR-F04: module size counts). Imported by slots.Screen.paytable() and dropped afterwards.

import font

GOLD = None   # colours are passed in so this module imports nothing but font


def show(lcd, buttons, table, bg, gold, white, grey):
    lcd.fill(bg)
    bet = table.bankroll.bet
    font.text_centred(lcd, 'Pays at bet %d' % bet, 120, 8, gold, 2)
    y = 34
    for label, pay in table.paytable_rows(bet):
        font.text(lcd, label, 24, y, white, 1)
        font.text_right(lcd, '%d' % pay, 216, y, gold, 1)
        y += 16
    font.text_centred(lcd, 'one line, 93.8% return', 120, 206, grey, 1)
    font.text_centred(lcd, 'any key: back', 120, 222, grey, 1)
    lcd.show()
    buttons.wait_any()
