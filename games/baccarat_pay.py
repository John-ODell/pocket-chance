# Baccarat help screen (ruling DR-058): pays, card values, the drawing rules and the edges. Kept
# out of baccarat.py so its code only occupies RAM while shown.

import font

# at most 29 characters per line (size-1 text from x = 4 must end by x = 236)
LINES = (
    'Player 1:1   Tie 8:1',
    'Banker 1:1 less 5%: 19 for 20,',
    'rounded down. Tie: Player',
    'and Banker bets push.',
    '',
    'CARDS: A=1, 2-9 face value,',
    '10 J Q K = 0. Only the last',
    'digit counts. 8 or 9 on two',
    'cards is a natural: no draw.',
    'PLAYER draws on 0-5, stands',
    'on 6-7.',
    'BANKER if Player stood: same.',
    'If Player drew card v: draws',
    'on 0-2; 3 unless v=8; 4 on',
    '2-7; 5 on 4-7; 6 on 6-7.',
)


def show(lcd, buttons, bg, gold, white, grey):
    lcd.fill(bg)
    font.text_centred(lcd, 'Baccarat (punto banco)', 120, 4, gold, 1)
    y = 18
    for text in LINES:
        if text:
            col = gold if text.startswith(('CARDS', 'PLAYER', 'BANKER')) else white
            font.text(lcd, text, 4, y, col, 1)
        y += 11
    font.text_centred(lcd, 'Edge: Banker 1.1% Player 1.2%', 120, y + 2, grey, 1)
    font.text_centred(lcd, 'Tie 14.4%', 120, y + 13, grey, 1)
    font.text_centred(lcd, 'any key: back', 120, 228, grey, 1)
    lcd.show()
    buttons.wait_any()
