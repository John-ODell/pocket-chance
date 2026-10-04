# Caribbean help screen (DR-071): the Ante table, the dealer rule, the taught strategy and the
# multiplier. Kept out of caribbean.py so its code only occupies RAM while shown.

import font

# at most 29 characters per line (size-1 text from x = 4 must end by x = 236)
LINES = (
    'Ante: royal 100  str flush 20',
    'quads 10  full 3  flush 2',
    'else 1:1. Call pays 1:1.',
    'Dealer needs a pair of 4s or',
    'better, else all bets push.',
    '',
    'HIGH 4x: two pair or better,',
    'or a pair using your card.',
    'LOW 2x: four to a flush or a',
    'straight, or your card beats',
    'the table. Else FOLD.',
    '',
    'If everyone beats a dealer',
    'hand, next call win pays x3.',
)


def show(lcd, buttons, bg, gold, white, grey):
    lcd.fill(bg)
    font.text_centred(lcd, 'Caribbean (Casino Hold\'em)', 120, 4, gold, 1)
    y = 18
    for text in LINES:
        if text:
            col = gold if text.startswith(('HIGH', 'LOW', 'If')) else white
            font.text(lcd, text, 4, y, col, 1)
        y += 11
    font.text_centred(lcd, 'Edge about 8% of the Ante', 120, y + 4, grey, 1)
    font.text_centred(lcd, 'any key: back', 120, 228, grey, 1)
    lcd.show()
    buttons.wait_any()
