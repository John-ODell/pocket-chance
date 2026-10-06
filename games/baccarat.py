# Baccarat screens and input. Thin: rules live in baccarat_rules.py / baccarat_table.py.
# Rulings DR-052 to DR-060 and the expert's limits (HR-052, HR-055, HR-060): Stud's four bands;
# full redraw only at the deal and the result; each dealt card is one 72-row band push inside its
# 300 ms slot, clocked; the bottom band (bet boxes, prompt, history squares, seat rail) is one
# 12 ms push whenever the selection changes; save after the result; drain the buttons after the deal.
#
# Controls   Betting:  LEFT/RIGHT side, UP/DOWN stake +-5, A deal, X pays, B menu
#            Result:   A deal again (same side and stake), joystick changes first, B menu
#            Broke:    A take 1000, B menu

import sys
import utime

import font
from pixfmt import rgb
from cards import card_name
from baccarat_rules import PLAYER, BANKER, TIE, SIDE_NAMES, total
from baccarat_table import BaccaratTable, BETTING, RESULT, BROKE

FELT = rgb(0, 80, 80)
FELT_EDGE = rgb(0, 50, 50)
CREAM = rgb(240, 232, 200)
BLACK = rgb(0, 0, 0)
RED = rgb(200, 20, 20)
WHITE = rgb(255, 255, 255)
GOLD = rgb(240, 200, 60)
GREY = rgb(160, 160, 160)
PLATE = rgb(0, 40, 40)
SIDE_COLOURS = (rgb(60, 120, 230), rgb(220, 60, 60), rgb(60, 200, 90))      # Player, Banker, Tie
PAYS = ('1:1', '19:20', '8:1')                                              # indexed by side

CARD_W, CARD_H = 40, 56
CARD_X = (56, 100, 144)                 # three slots per hand (DR-052)
TOP_H = 24
BANKER_TOP, PLAYER_TOP, BOTTOM_TOP = 24, 96, 168
BAND_H = 72
BANKER_Y, PLAYER_Y = 28, 100
BOX_Y, BOX_H, BOX_W = 172, 24, 72
BOX_X = (8, 160, 84)                    # indexed by side: Player left, Banker right, Tie middle
PROMPT_Y = 202
HIST_Y, HIST_X0, HIST_STEP = 214, 8, 18
RAIL_Y = 228
RAIL_X = (10, 54, 98, 142, 186)
STACK_W = 30
SEAT_COLOURS = (rgb(220, 60, 60), rgb(60, 160, 220), rgb(240, 200, 60), rgb(120, 200, 100), rgb(200, 120, 220))
UP = rgb(40, 220, 60)
DOWN = rgb(230, 40, 40)
PUSH = rgb(150, 150, 150)
CHIP_DENOMS = (500, 100, 25, 5)
DEAL_MS = 300                           # DR-052


def signed(n):
    return '%s%d' % ('+' if n > 0 else '', n)


class Screen:
    def __init__(self, ctx):
        self.lcd = ctx.lcd
        self.assets = ctx.assets
        self.buttons = ctx.buttons
        self.store = ctx.store
        self.table = BaccaratTable(ctx.rng, ctx.bankroll, seats=getattr(ctx, 'bac_seats', 5))
        self.has_table_art = self.assets.size('table') is not None
        self.assets.use_sheets(('cards', 'chips'))
        self.shown = 0                                # cards of the coup on the table

    # ---- drawing helpers ----------------------------------------------------------------------
    def felt(self, y=0, h=240):
        lcd = self.lcd
        if self.has_table_art and self.assets.background_rows(lcd, 'table', y, h):
            return
        lcd.fill_rect(0, y, 240, h, FELT)
        for yy in (0, 239):
            if y <= yy < y + h:
                lcd.hline(0, yy, 240, FELT_EDGE)
        lcd.vline(0, y, h, FELT_EDGE)
        lcd.vline(239, y, h, FELT_EDGE)

    def card(self, c, x, y):
        lcd = self.lcd
        name = card_name(c)
        if self.assets.blit(lcd, 'c_' + name, x, y):
            return
        lcd.fill_rect(x, y, CARD_W, CARD_H, CREAM)
        lcd.rect(x, y, CARD_W, CARD_H, BLACK)
        col = RED if name[1] in 'HD' else BLACK
        rank = '10' if name[0] == 'T' else name[0]
        font.text(lcd, rank, x + 3, y + 3, col, 2)
        font.text(lcd, name[1], x + 3, y + 22, col, 2)
        font.text(lcd, name[1], x + CARD_W - 11, y + CARD_H - 11, col, 1)

    def chip(self, value, x, y):
        denom = 5
        for d in CHIP_DENOMS:
            if value >= d:
                denom = d
                break
        if self.assets.blit(self.lcd, 'chip_%d' % denom, x, y):
            return
        col = {5: RED, 25: rgb(20, 140, 40), 100: BLACK, 500: rgb(120, 30, 160)}[denom]
        self.lcd.ellipse(x + 11, y + 11, 11, 11, col, True)
        self.lcd.ellipse(x + 11, y + 11, 7, 7, WHITE, False)

    def revealing(self):
        c = self.table.coup
        return c is not None and self.shown < len(c.order)

    # ---- bands --------------------------------------------------------------------------------
    def draw_top(self):
        lcd = self.lcd
        self.felt(0, TOP_H)
        balance, stake = self.table.stakes(self.revealing())
        s = '$%d' % balance
        font.text(lcd, s, 6, 4, GOLD, 2)
        if 6 + font.width(s, 2) < 118:                                      # a balance of a million
            self.chip(stake, 120, 0)                                        # or more needs the room
        font.text_right(lcd, '%s %d' % (SIDE_NAMES[self.table.side], stake), 234, 8, WHITE, 1)

    def hand_band(self, side):
        """The Banker or Player band with the cards dealt so far and the total line."""
        lcd = self.lcd
        top = BANKER_TOP if side == BANKER else PLAYER_TOP
        y = BANKER_Y if side == BANKER else PLAYER_Y
        self.felt(top, BAND_H)
        coup = self.table.coup
        label = SIDE_NAMES[side]
        if coup is None:
            font.text(lcd, label, 6, y + CARD_H + 2, GREY, 1)
            return
        player, banker = coup.shown(self.shown)
        cards = banker if side == BANKER else player
        for i, c in enumerate(cards):
            self.card(c, CARD_X[i], y)
        line = '%s  %d' % (label, total(cards)) if cards else label
        if coup.natural and len(cards) == 2 and self.shown >= 4 and total(cards) >= 8:
            line += '  natural'
        font.text(lcd, line, 6, y + CARD_H + 2, WHITE, 1)

    def draw_banker(self):
        self.hand_band(BANKER)

    def draw_player(self):
        self.hand_band(PLAYER)

    def draw_boxes(self):
        lcd = self.lcd
        t = self.table
        for side in (PLAYER, TIE, BANKER):
            x = BOX_X[side]
            lcd.fill_rect(x, BOX_Y, BOX_W, BOX_H, PLATE)
            chosen = side == t.side
            lcd.rect(x, BOX_Y, BOX_W, BOX_H, GOLD if chosen else SIDE_COLOURS[side])
            font.text(lcd, SIDE_NAMES[side], x + 3, BOX_Y + 3, SIDE_COLOURS[side], 1)
            font.text(lcd, PAYS[side], x + 3, BOX_Y + 13, GREY, 1)
            if chosen:
                font.text_right(lcd, '%d' % t.bankroll.bet, x + BOX_W - 3, BOX_Y + 13, GOLD, 1)

    def draw_history(self):
        """The last twelve results as coloured squares, oldest on the left (DR-060)."""
        lcd = self.lcd
        for k, w in enumerate(self.table.history):
            lcd.fill_rect(HIST_X0 + HIST_STEP * k, HIST_Y, 8, 8, SIDE_COLOURS[w])

    def draw_rail(self):
        """Other players' chip stacks (DR-055): one line per 200 chips, a green, red or grey marker
        once the coup is settled."""
        lcd = self.lcd
        seats = self.table.seats
        for i in range(seats.count):
            x = RAIL_X[i]
            n = seats.stack_height(i)
            for k in range(n):
                lcd.fill_rect(x + 8, RAIL_Y + 11 - 2 * k, STACK_W, 1, SEAT_COLOURS[i])
            if seats.settled[i] and not self.revealing():
                d = seats.delta[i]
                lcd.fill_rect(x + 1, RAIL_Y + 4, 4, 4, UP if d > 0 else (DOWN if d < 0 else PUSH))

    def draw_bottom(self):
        lcd = self.lcd
        t = self.table
        st = t.state
        self.felt(BOTTOM_TOP, BAND_H)
        if st == BROKE:
            font.text_centred(lcd, 'Out of chips', 120, BOX_Y + 4, RED, 2)
            font.text_centred(lcd, 'A take 1000   B menu', 120, PROMPT_Y, WHITE, 1)
            return
        self.draw_boxes()
        if st == BETTING or self.revealing():
            font.text_centred(lcd, 'A deal   X pays   B menu' if st == BETTING else '', 120, PROMPT_Y, WHITE, 1)
        else:
            c = t.coup
            p, b = c.totals()
            if c.winner == TIE:
                line = 'TIE %d-%d   %s' % (p, b, signed(t.net) if t.net else 'push')
            else:
                line = '%s WINS %d-%d   %s' % (SIDE_NAMES[c.winner], p, b, signed(t.net))
            font.text_centred(lcd, line, 120, PROMPT_Y, GOLD if t.net > 0 else WHITE, 1)
        self.draw_history()
        self.draw_rail()

    def draw_all(self):
        """Scene change: full redraw then one show() (deal start and result only, HR-052)."""
        lcd = self.lcd
        if not (self.has_table_art and self.assets.background(lcd, 'table')):
            self.felt()
        self.draw_top()
        self.draw_banker()
        self.draw_player()
        self.draw_bottom()
        lcd.show()

    def push_bottom(self):
        self.draw_bottom()
        self.lcd.show_band(BOTTOM_TOP, BAND_H)

    def shuffling(self):
        lcd = self.lcd
        self.felt(BOTTOM_TOP, BAND_H)
        font.text_centred(lcd, 'Shuffling...', 120, BOX_Y + 4, WHITE, 2)
        lcd.show_band(BOTTOM_TOP, BAND_H)
        utime.sleep_ms(700)

    # ---- the deal (DR-052 / HR-052) -----------------------------------------------------------
    def deal(self):
        """Table settles at once; the screen turns the cards one by one, 300 ms apart by the clock,
        each a hand-band push; the last card comes with the result redraw."""
        t = self.table
        t.deal()
        if t.shuffled:
            self.shuffling()
        coup = t.coup
        self.shown = 0
        self.draw_all()                               # empty table, stake off the bankroll
        lcd = self.lcd
        n = len(coup.order)
        while self.shown < n - 1:
            t0 = utime.ticks_us()
            self.shown += 1
            side = coup.order[self.shown - 1]
            self.hand_band(side)
            lcd.show_band(BANKER_TOP if side == BANKER else PLAYER_TOP, BAND_H)
            spent = utime.ticks_diff(utime.ticks_us(), t0) // 1000
            if spent < DEAL_MS:
                utime.sleep_ms(DEAL_MS - spent)
        self.shown = n
        self.draw_all()                               # result scene
        self.store.save(t.bankroll.balance)           # DR-056: after the result, never mid-deal
        self.buttons.poll()                           # drop presses made during the deal

    def paytable(self):
        import baccarat_pay                           # loaded only while shown
        baccarat_pay.show(self.lcd, self.buttons, FELT_EDGE, GOLD, WHITE, GREY)
        if 'baccarat_pay' in sys.modules:
            del sys.modules['baccarat_pay']
        self.draw_all()

    # ---- input --------------------------------------------------------------------------------
    def handle(self, key):
        """Return False to leave the game."""
        t = self.table
        st = t.state
        if key == 'X' and st != BROKE:
            self.paytable()
            return True
        if st == RESULT and key in ('UP', 'DOWN', 'LEFT', 'RIGHT', 'A'):
            t.next_coup()                             # a joystick move or A leaves the result
            st = t.state
            if st == BROKE:
                self.draw_all()
                return True
        if st == BETTING:
            if key in ('UP', 'DOWN'):
                t.adjust_stake(5 if key == 'UP' else -5)
                self.draw_top()
                self.lcd.show_band(0, TOP_H)
                self.push_bottom()
            elif key in ('LEFT', 'RIGHT'):
                t.select(1 if key == 'RIGHT' else -1)
                self.draw_top()
                self.lcd.show_band(0, TOP_H)
                self.push_bottom()
            elif key == 'A':
                self.deal()
            elif key == 'B':
                return False
        elif st == RESULT:
            if key == 'B':
                return False
        elif st == BROKE:
            if key == 'A':
                t.refill()
                self.draw_all()
                self.store.save(t.bankroll.balance)
            elif key == 'B':
                return False
        return True

    def run(self):
        self.draw_all()
        buttons = self.buttons
        try:
            while True:
                for key in buttons.poll():
                    if not self.handle(key):
                        return
                utime.sleep_ms(15)
        finally:
            self.assets.release_sheets()


def run(ctx):
    Screen(ctx).run()
