# Ultimate Texas Hold'em help screen: Blind pays and the full published simple strategy (ruling
# DR-042 rev 2). Kept out of holdem.py so its code only occupies RAM while shown.

import font

# at most 29 characters per line (size-1 text from x = 4 must end by x = 236)
LINES = (
    'Blind: royal 500  strfl 50',
    'quads 10  full 3  flush 3:2',
    'straight 1. Dealer needs a',
    'pair or the Ante pushes.',
    '',
    'RAISE 4x: pair (not 2s),',
    'any ace, K5+ (K2+ suited),',
    'Q8+ (Q6+ s), J10 (J8+ s).',
    'Else check.',
    'FLOP 2x: two pair+, a pair',
    'with your card (not 2s), or',
    'a 4-flush with your 10+.',
    'RIVER 1x: pair with your',
    'card, or dealer outs < 21',
    '(on the prompt). Else fold.',
)


def show(lcd, buttons, bg, gold, white, grey):
    lcd.fill(bg)
    font.text_centred(lcd, 'Ultimate Texas Hold\'em', 120, 4, gold, 1)
    y = 18
    for text in LINES:
        if text:
            col = gold if text.startswith(('RAISE', 'FLOP', 'RIVER')) else white
            font.text(lcd, text, 4, y, col, 1)
        y += 11
    font.text_centred(lcd, 'House edge 2.4% of the Ante', 120, y + 4, grey, 1)
    font.text_centred(lcd, 'any key: back', 120, 228, grey, 1)
    lcd.show()
    buttons.wait_any()
