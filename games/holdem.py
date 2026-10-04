# Ultimate Texas Hold'em screens and input. Thin: rules live in holdem_rules.py / holdem_table.py.
# Rulings DR-042 to DR-049 and the expert's limits (HR-043, HR-044, HR-047): three card rows with
# the seats' chip stacks in the side boxes, a 36 px bottom band with size-1 text only (the chips
# figure at the top is the one size-2 string), card backs always code-drawn, a full redraw only when
# cards turn or the result shows, the community cards turned by band push 300 ms after the decision,
# the dealer's two cards one by one at the showdown with the seats settled BEFORE the first flip,
# then the result, the save, and the buttons drained. River outs hint (DR-042 addendum) computed
# after the river band is pushed, before the prompt appears.
#
# Controls   Betting:  UP/DOWN Ante +-5, LEFT/RIGHT +-25, A deal, X help, B menu
#            Pre-flop: A raise 4x, Y raise 3x, B check      Flop: A raise 2x, B check
#            River:    A raise 1x, B fold                   Result: A next, B menu
#            Broke:    A take 1000, B menu

import gc
import sys
import utime

import font
from pixfmt import rgb
from cards import card_name
from holdem_rules import PREFLOP, FLOP, RIVER, WIN, LOSE, PUSH, FOLD
from holdem_table import HoldemTable, BETTING, RESULT, BROKE

FELT = rgb(0, 90, 40)
FELT_EDGE = rgb(0, 60, 25)
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
PAIR_X = (76, 120)                      # the two dealer / player cards
COMM_X = (12, 56, 100, 144, 188)
BOX_X = (8, 172)                        # side boxes, 60 wide
BOX_W = 60
LINE_Y = (206, 218, 228)                # the three size-1 lines of the bottom band
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
        self.table = HoldemTable(ctx.rng, ctx.bankroll, seats=getattr(ctx, 'uth_seats', 4),
                                 hint=getattr(ctx, 'uth_hint', True))
        self.has_table_art = self.assets.size('table') is not None
        self.assets.use_sheets(('cards', 'chips'))
        self.dealer_shown = 0               # dealer cards face up (0, 1, 2)

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
        """A seat's chip stack in a 60 x 56 box: chip art (or discs) piled 4 px apart, one chip per
        200 chips up to six, the count under it, a green/red marker after a hand (DR-044 rev 2)."""
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
        """Two size-1 lines in a side box when seats are off: 'Dealer' / 'pair of 9s'."""
        font.text(self.lcd, label, x + 2, y + 18, col, 1)
        font.text(self.lcd, SHORT[value[0]] if value else '', x + 2, y + 30, col, 1)

    # ---- rows ---------------------------------------------------------------------------------
    def draw_top(self):
        lcd = self.lcd
        self.felt(0, TOP_H)
        balance, ante, play = self.table.stakes()
        font.text(lcd, '$%d' % balance, 6, 4, GOLD, 2)
        line = 'ante %d blind %d' % (ante, ante) if not play else 'ante %d play %d' % (ante, play)
        font.text_right(lcd, line, 234, 8, WHITE, 1)

    def draw_dealer_row(self):
        lcd = self.lcd
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
        lcd = self.lcd
        r = self.table.round
        self.felt(COMM_TOP, ROW_H)
        shown = r.shown_board() if r is not None else []
        for i in range(5):
            if i < len(shown):
                self.card(shown[i], COMM_X[i], COMM_Y)
            else:
                self.card_back(COMM_X[i], COMM_Y)

    def draw_player_row(self):
        lcd = self.lcd
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
        if st == BETTING:
            font.text_centred(lcd, 'Ante: joystick (Blind = Ante)', 120, LINE_Y[0], GREY, 1)
            font.text_centred(lcd, 'A deal   X help   B menu', 120, LINE_Y[1], WHITE, 1)
        elif st == PREFLOP:
            a = t.round.ante
            font.text_centred(lcd, 'A raise %d   Y %d   B check' % (a * t.rules.big_raise, a * t.rules.small_big_raise),
                              120, LINE_Y[1], WHITE, 1)
            font.text_centred(lcd, 'X help', 120, LINE_Y[2], GREY, 1)
        elif st == FLOP:
            font.text_centred(lcd, 'A raise %d   B check' % (2 * t.round.ante), 120, LINE_Y[1], WHITE, 1)
            font.text_centred(lcd, 'X help', 120, LINE_Y[2], GREY, 1)
        elif st == RIVER:
            line = 'A raise %d   B fold' % t.round.ante
            if t.outs is not None:
                line += '   outs %d' % t.outs
            font.text_centred(lcd, line, 120, LINE_Y[1], WHITE, 1)
            font.text_centred(lcd, 'X help', 120, LINE_Y[2], GREY, 1)
        elif st == RESULT:
            r = t.round
            if r.outcome == FOLD:
                line, col = 'FOLD %s' % signed(r.net), GREY
            elif r.outcome == WIN:
                line, col = 'WIN %s' % signed(r.net), GOLD
            elif r.outcome == LOSE:
                line, col = 'LOSE %s' % signed(r.net), GREY
            else:
                line, col = 'PUSH', WHITE
            if not r.qualified and r.outcome != FOLD:
                line += ', Ante back'
            font.text_centred(lcd, line, 120, LINE_Y[0], col, 1)
            font.text_centred(lcd, 'you %s / dlr %s' % (SHORT[r.pv[0]], SHORT[r.dv[0]]), 120, LINE_Y[1], WHITE, 1)
            font.text_centred(lcd, 'A next   B menu', 120, LINE_Y[2], WHITE, 1)
        elif st == BROKE:
            font.text_centred(lcd, 'Out of chips', 120, LINE_Y[0], RED, 1)
            font.text_centred(lcd, 'A take 1000   B menu', 120, LINE_Y[1], WHITE, 1)

    def draw_all(self):
        """Phase change or result: full redraw then one show() (HR-043)."""
        lcd = self.lcd
        if not (self.has_table_art and self.assets.background(lcd, 'table')):
            self.felt()
        self.draw_top()
        self.draw_dealer_row()
        self.draw_comm_row()
        self.draw_player_row()
        self.draw_bottom()
        lcd.show()

    # ---- phases (DR-047) ----------------------------------------------------------------------
    def turn_community(self):
        """The community cards of the new phase turn together: community band push, then after
        300 ms by the clock the prompt (and the river hint, computed in between)."""
        t0 = utime.ticks_us()
        self.draw_comm_row()
        self.lcd.show_band(COMM_TOP, ROW_H)
        if self.table.state == RIVER and self.table.outs is None and self.table.hint:
            gc.collect()
            self.table.outs = self.table.round.outs()      # about 228 ms on the board (HR outs bench)
        spent = utime.ticks_diff(utime.ticks_us(), t0) // 1000
        if spent < REVEAL_MS:
            utime.sleep_ms(REVEAL_MS - spent)
        self.draw_bottom()
        self.lcd.show_band(BOTTOM_TOP, 240 - BOTTOM_TOP)

    def showdown(self):
        """Seats are settled by the table already (before any flip, HR-044). Turn the dealer's
        cards one by one, 300 ms apart by the clock, then the result scene, the save, drain."""
        lcd = self.lcd
        if self.table.round.outcome != FOLD or True:
            # the board is fully shown at a showdown; after a 4x/2x raise it turns now
            self.draw_comm_row()
            lcd.show_band(COMM_TOP, ROW_H)
        for n in (1, 2):
            t0 = utime.ticks_us()
            self.dealer_shown = n
            if n == 2:
                break                                       # the last card arrives with the result redraw
            self.draw_dealer_row()
            lcd.show_band(DEALER_TOP, ROW_H)
            spent = utime.ticks_diff(utime.ticks_us(), t0) // 1000
            if spent < REVEAL_MS:
                utime.sleep_ms(REVEAL_MS - spent)
        self.dealer_shown = 2
        self.draw_all()
        self.store.save(self.table.bankroll.balance)       # DR-048: after the result, never mid-reveal
        self.buttons.poll()

    def help(self):
        import holdem_pay
        holdem_pay.show(self.lcd, self.buttons, FELT_EDGE, GOLD, WHITE, GREY)
        if 'holdem_pay' in sys.modules:
            del sys.modules['holdem_pay']
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
                t.deal()
                self.dealer_shown = 0
                self.draw_all()
            elif key == 'B':
                return False
        elif st == PREFLOP:
            if key == 'A':
                t.raise_(t.rules.big_raise)
                self.showdown()
            elif key == 'Y':
                t.raise_(t.rules.small_big_raise)
                self.showdown()
            elif key == 'B':
                t.check()
                self.turn_community()
        elif st == FLOP:
            if key == 'A':
                t.raise_(2)
                self.showdown()
            elif key == 'B':
                t.check()
                self.turn_community()
        elif st == RIVER:
            if key == 'A':
                t.raise_(1)
                self.showdown()
            elif key == 'B':
                t.fold()
                self.showdown()
        elif st == RESULT:
            if key == 'A':
                t.next_hand()
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
