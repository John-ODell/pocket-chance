# Caribbean (Casino Hold'em with a low/high call) screens and input. Thin: rules live in
# caribbean_rules.py / caribbean_table.py. Rulings DR-062 to DR-071 (defaults John is confirming
# are flagged in pm/STATUS.md) and the expert's limits for Ultimate's layout (HR-043, HR-044,
# HR-047), which this screen reuses: three card rows with the seats' chip stacks in the side boxes,
# a 36 px bottom band with size-1 text only, card backs always code-drawn, a full redraw only when
# the hand is dealt or the result shows, the flop turned by band push 300 ms after the deal, the
# last two table cards and then the dealer's cards one by one 300 ms apart, with the seats settled
# BEFORE the first flip, then the result, the save, and the buttons drained.
#
# Controls   Betting:  UP/DOWN Ante +-5, LEFT/RIGHT +-25, A deal, X help, B menu
#            Flop:     A call high (4x), Y call low (2x), B fold
#            Result:   A next, B menu                       Broke: A take 1000, B menu

import sys
import utime

import font
from pixfmt import rgb
from cards import card_name
from caribbean_rules import WIN, LOSE, PUSH, FOLD
from caribbean_table import CaribbeanTable, BETTING, DECIDING, RESULT, BROKE

FELT = rgb(110, 20, 30)                 # burgundy (DR-065: a colour per game)
FELT_EDGE = rgb(70, 10, 20)
CREAM = rgb(240, 232, 200)
BLACK = rgb(0, 0, 0)
RED = rgb(200, 20, 20)
WHITE = rgb(255, 255, 255)
GOLD = rgb(240, 200, 60)
GREY = rgb(160, 160, 160)
BLUE = rgb(30, 60, 160)
UP = rgb(40, 220, 60)
DOWN = rgb(230, 40, 40)
CHIP_COL = (rgb(200, 30, 30), rgb(30, 140, 60), rgb(40, 40, 40), rgb(120, 30, 160))

CARD_W, CARD_H = 40, 56
TOP_H = 24
DEALER_TOP, COMM_TOP, PLAYER_TOP, BOTTOM_TOP = 24, 84, 144, 204
ROW_H = 60
DEALER_Y, COMM_Y, PLAYER_Y = 26, 86, 146
PAIR_X = (76, 120)
COMM_X = (12, 56, 100, 144, 188)
BOX_X = (8, 172)
BOX_W = 60
LINE_Y = (206, 218, 228)
REVEAL_MS = 300
SHORT = {0: 'high card', 1: 'pair', 2: 'two pair', 3: 'trips', 4: 'strt', 5: 'flush', 6: 'full',
         7: 'quads', 8: 'sflush', 9: 'royal'}


def signed(n):
    return '%s%d' % ('+' if n > 0 else '', n)


class Screen:
    def __init__(self, ctx):
        self.lcd = ctx.lcd
        self.assets = ctx.assets
        self.buttons = ctx.buttons
        self.store = ctx.store
        self.table = CaribbeanTable(ctx.rng, ctx.bankroll, seats=getattr(ctx, 'car_seats', 4))
        self.has_table_art = self.assets.size('table') is not None
        self.assets.use_sheets(('cards', 'chips'))
        self.board_shown = 0                # table cards face up: 0, 3 or 5
        self.dealer_shown = 0               # dealer cards face up: 0, 1, 2

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

    def card_back(self, x, y):
        """Always code-drawn (HR-043 limit)."""
        lcd = self.lcd
        lcd.fill_rect(x, y, CARD_W, CARD_H, BLUE)
        lcd.rect(x, y, CARD_W, CARD_H, CREAM)
        lcd.rect(x + 4, y + 4, CARD_W - 8, CARD_H - 8, CREAM)

    def seat_box(self, i, x, y):
        """A seat's chip stack in a 60 x 56 box (DR-044 rev 2 / DR-069)."""
        lcd = self.lcd
        seats = self.table.seats
        n = seats.stack_height(i)
        cx = x + (BOX_W - 24) // 2
        base = y + 44 - 24
        for k in range(n):
            cy = base - 4 * k
            if not self.assets.blit(lcd, 'chip_25', cx, cy):
                lcd.ellipse(cx + 12, cy + 12, 11, 7, CHIP_COL[i], True)
                lcd.ellipse(cx + 12, cy + 12, 11, 7, WHITE, False)
        font.text_centred(lcd, '%d' % seats.chips[i], x + BOX_W // 2, y + 46, WHITE, 1)
        d = seats.delta[i]
        if d:
            lcd.fill_rect(x + BOX_W - 6, y + 2, 4, 4, UP if d > 0 else DOWN)

    def name_box(self, label, value, x, y, col):
        font.text(self.lcd, label, x + 2, y + 18, col, 1)
        font.text(self.lcd, SHORT[value[0]] if value else '', x + 2, y + 30, col, 1)

    # ---- rows ---------------------------------------------------------------------------------
    def draw_top(self):
        lcd = self.lcd
        self.felt(0, TOP_H)
        balance, ante, call = self.table.stakes()
        font.text(lcd, '$%d' % balance, 6, 4, GOLD, 2)
        line = 'ante %d' % ante if not call else 'ante %d call %d' % (ante, call)
        font.text_right(lcd, line, 234, 8, WHITE, 1)

    def draw_dealer_row(self):
        t = self.table
        r = t.round
        self.felt(DEALER_TOP, ROW_H)
        for i in range(2):
            if r is not None and i < self.dealer_shown:
                self.card(r.dealer[i], PAIR_X[i], DEALER_Y)
            else:
                self.card_back(PAIR_X[i], DEALER_Y)
        self.side_boxes(0, DEALER_Y, 'Dealer', r.dv if (r is not None and self.dealer_shown == 2) else None)

    def draw_comm_row(self):
        r = self.table.round
        self.felt(COMM_TOP, ROW_H)
        shown = self.board_shown if r is not None else 0
        for i in range(5):
            if i < shown:
                self.card(r.board[i], COMM_X[i], COMM_Y)
            else:
                self.card_back(COMM_X[i], COMM_Y)

    def draw_player_row(self):
        r = self.table.round
        self.felt(PLAYER_TOP, ROW_H)
        if r is not None:
            for i in range(2):
                self.card(r.player[i], PAIR_X[i], PLAYER_Y)
        self.side_boxes(2, PLAYER_Y, 'You', r.pv if (r is not None and r.pv is not None) else None)

    def side_boxes(self, first_seat, y, label, value):
        seats = self.table.seats
        for k in range(2):
            i = first_seat + k
            x = BOX_X[k]
            if i < seats.count:
                self.seat_box(i, x, y)
            elif k == 0:
                self.name_box(label, value, x, y, WHITE)

    def draw_bottom(self):
        lcd = self.lcd
        t = self.table
        st = t.state
        self.felt(BOTTOM_TOP, 240 - BOTTOM_TOP)
        mult = t.multiplier()
        if st == BETTING:
            font.text_centred(lcd, 'Ante: joystick', 120, LINE_Y[0], GREY, 1)
            font.text_centred(lcd, 'A deal   X help   B menu', 120, LINE_Y[1], WHITE, 1)
            if mult > 1:
                font.text_centred(lcd, 'x%d CALL WIN NEXT HAND' % mult, 120, LINE_Y[2], GOLD, 1)
        elif st == DECIDING:
            r = t.round
            if self.board_shown == 0:
                return                                              # the flop is about to turn
            a = r.ante
            font.text_centred(lcd, 'A high %d  Y low %d  B fold' % (a * t.rules.high, a * t.rules.low),
                              120, LINE_Y[1], WHITE, 1)
            if r.mult > 1:
                font.text_centred(lcd, 'call win pays x%d this hand' % r.mult, 120, LINE_Y[2], GOLD, 1)
            else:
                font.text_centred(lcd, 'X help', 120, LINE_Y[2], GREY, 1)
        elif st == RESULT:
            r = t.round
            if r.outcome == FOLD:
                line, col = 'FOLD %s' % signed(r.net), GREY
            elif r.outcome == WIN:
                line, col = 'WIN %s' % signed(r.net), GOLD
                if r.mult > 1:
                    line += ' (x%d)' % r.mult
            elif r.outcome == LOSE:
                line, col = 'LOSE %s' % signed(r.net), GREY
            else:
                line, col = 'PUSH', WHITE
            if not r.qualified:
                line += ', no dealer hand'
            font.text_centred(lcd, line, 120, LINE_Y[0], col, 1)
            font.text_centred(lcd, 'you %s / dlr %s' % (SHORT[r.pv[0]], SHORT[r.dv[0]]), 120, LINE_Y[1], WHITE, 1)
            if t.armed:
                font.text_centred(lcd, 'x%d NEXT HAND  A next  B menu' % t.multiplier(), 120, LINE_Y[2], GOLD, 1)
            else:
                font.text_centred(lcd, 'A next   B menu', 120, LINE_Y[2], WHITE, 1)
        elif st == BROKE:
            font.text_centred(lcd, 'Out of chips', 120, LINE_Y[0], RED, 1)
            font.text_centred(lcd, 'A take 1000   B menu', 120, LINE_Y[1], WHITE, 1)

    def draw_all(self):
        """Deal or result: full redraw then one show() (HR-043)."""
        lcd = self.lcd
        if not (self.has_table_art and self.assets.background(lcd, 'table')):
            self.felt()
        self.draw_top()
        self.draw_dealer_row()
        self.draw_comm_row()
        self.draw_player_row()
        self.draw_bottom()
        lcd.show()

    # ---- phases (DR-066) ----------------------------------------------------------------------
    def deal(self):
        """Player's cards up, everything else down; 300 ms later the flop turns and the prompt shows."""
        self.table.deal()
        self.board_shown = 0
        self.dealer_shown = 0
        t0 = utime.ticks_us()
        self.draw_all()
        spent = utime.ticks_diff(utime.ticks_us(), t0) // 1000
        if spent < REVEAL_MS:
            utime.sleep_ms(REVEAL_MS - spent)
        self.board_shown = 3
        self.draw_comm_row()
        self.lcd.show_band(COMM_TOP, ROW_H)
        self.draw_bottom()
        self.lcd.show_band(BOTTOM_TOP, 240 - BOTTOM_TOP)
        self.buttons.poll()                                 # drop presses made during the pause

    def showdown(self):
        """Seats are settled by the table already (before any flip, HR-044). Turn the last two table
        cards, then the dealer's cards one by one, 300 ms apart by the clock, then the result scene,
        the save, drain. A fold shows the same cards so John sees what he missed."""
        lcd = self.lcd
        t0 = utime.ticks_us()
        self.board_shown = 5
        self.draw_comm_row()
        lcd.show_band(COMM_TOP, ROW_H)
        self.draw_bottom()                                  # prompt gone while the cards turn
        lcd.show_band(BOTTOM_TOP, 240 - BOTTOM_TOP)
        spent = utime.ticks_diff(utime.ticks_us(), t0) // 1000
        if spent < REVEAL_MS:
            utime.sleep_ms(REVEAL_MS - spent)
        t0 = utime.ticks_us()
        self.dealer_shown = 1
        self.draw_dealer_row()
        lcd.show_band(DEALER_TOP, ROW_H)
        spent = utime.ticks_diff(utime.ticks_us(), t0) // 1000
        if spent < REVEAL_MS:
            utime.sleep_ms(REVEAL_MS - spent)
        self.dealer_shown = 2
        self.draw_all()
        self.store.save(self.table.bankroll.balance)       # DR-070: after the result, never mid-reveal
        self.buttons.poll()

    def help(self):
        import caribbean_pay
        caribbean_pay.show(self.lcd, self.buttons, FELT_EDGE, GOLD, WHITE, GREY)
        if 'caribbean_pay' in sys.modules:
            del sys.modules['caribbean_pay']
        self.draw_all()

    # ---- input --------------------------------------------------------------------------------
    def handle(self, key):
        """Return False to leave the game."""
        t = self.table
        st = t.state
        if key == 'X' and st != BROKE:
            self.help()
            return True
        if st == BETTING:
            delta = {'UP': 5, 'DOWN': -5, 'RIGHT': 25, 'LEFT': -25}.get(key)
            if delta:
                t.adjust_ante(delta)
                self.draw_top()
                self.lcd.show_band(0, TOP_H)
            elif key == 'A':
                self.deal()
            elif key == 'B':
                return False
        elif st == DECIDING:
            if key == 'A':
                t.call(t.rules.high)
                self.showdown()
            elif key == 'Y':
                t.call(t.rules.low)
                self.showdown()
            elif key == 'B':
                t.fold()
                self.showdown()
        elif st == RESULT:
            if key == 'A':
                t.next_hand()
                self.board_shown = 0
                self.dealer_shown = 0
                self.draw_all()
            elif key == 'B':
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
