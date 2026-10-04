# Caribbean Stud screens and input. Thin: rules live in stud_rules.py / stud_table.py.
# Rulings DR-025 to DR-032 and the expert's limits (HR-026, HR-029): the same four bands as
# blackjack; full redraw only on deal and result; face-down cards always code-drawn; only the chips
# figure at size 2; the dealer's hole cards turn over one at a time, 300 ms apart by the clock, each
# step one dealer-band push; save after the result; drain the buttons after the reveal.
#
# Controls   Betting:  UP/DOWN ante +-5, LEFT/RIGHT +-25, A deal, X pays and strategy, B menu
#            Deciding: A raise (2x ante), B fold, X pays
#            Result:   A next hand, B menu          Broke: A take 1000, B menu

import sys
import utime

import font
from pixfmt import rgb
from cards import card_name
from stud_rules import describe, FOLD, NOQUALIFY, WIN, LOSE, PUSH
from stud_table import StudTable, BETTING, DECIDING, RESULT, BROKE

FELT = rgb(0, 90, 40)
FELT_EDGE = rgb(0, 60, 25)
CREAM = rgb(240, 232, 200)
BLACK = rgb(0, 0, 0)
RED = rgb(200, 20, 20)
WHITE = rgb(255, 255, 255)
GOLD = rgb(240, 200, 60)
GREY = rgb(160, 160, 160)
BLUE = rgb(30, 60, 160)

CARD_W, CARD_H = 40, 56
CARD_X = (12, 56, 100, 144, 188)       # five cards, 4 px gaps (DR-026)
TOP_H = 24
DEALER_TOP, PLAYER_TOP, BOTTOM_TOP = 24, 96, 168
BAND_H = 72
DEALER_Y, PLAYER_Y = 28, 100
BANNER_Y, BOTTOM_Y = 168, 200
REVEAL_MS = 300                        # DR-029
CHIP_DENOMS = (500, 100, 25, 5)

BANNERS = {WIN: ('banner_win', 'YOU WIN', GOLD), LOSE: ('banner_lose', 'DEALER WINS', GREY),
           PUSH: ('banner_push', 'PUSH', WHITE), NOQUALIFY: ('banner_noqualify', 'NO QUALIFY', GOLD),
           FOLD: (None, 'FOLDED', GREY)}


def signed(n):
    return '%s%d' % ('+' if n > 0 else '', n)


class Screen:
    def __init__(self, ctx):
        self.lcd = ctx.lcd
        self.assets = ctx.assets
        self.buttons = ctx.buttons
        self.store = ctx.store
        self.table = StudTable(ctx.rng, ctx.bankroll)
        self.has_table_art = self.assets.size('table') is not None
        self.assets.use_sheets(('cards', 'chips', 'banners'))
        self.shown = 1                                # dealer cards face up (1 = the up-card)

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
        """Always code-drawn (HR-026 limit 1), even when the card art exists."""
        lcd = self.lcd
        lcd.fill_rect(x, y, CARD_W, CARD_H, BLUE)
        lcd.rect(x, y, CARD_W, CARD_H, CREAM)
        lcd.rect(x + 4, y + 4, CARD_W - 8, CARD_H - 8, CREAM)

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

    # ---- bands --------------------------------------------------------------------------------
    def draw_top(self):
        lcd = self.lcd
        self.felt(0, TOP_H)
        balance, ante, raise_bet = self.table.stakes()
        font.text(lcd, '$%d' % balance, 6, 4, GOLD, 2)                    # the one size-2 string
        self.chip(ante, 120, 0)
        line = 'ante %d' % ante if not raise_bet else 'ante %d + %d' % (ante, raise_bet)
        font.text_right(lcd, line, 234, 8, WHITE, 1)

    def draw_dealer(self):
        lcd = self.lcd
        r = self.table.round
        self.felt(DEALER_TOP, BAND_H)
        if r is None:
            self.card_back(CARD_X[2], DEALER_Y)                           # idle table decoration
            return
        for i in range(5):
            if i < self.shown:
                self.card(r.dealer[i], CARD_X[i], DEALER_Y)
            else:
                self.card_back(CARD_X[i], DEALER_Y)
        if self.shown < 5:
            line = 'Dealer shows ' + card_name(r.up_card())[0].replace('T', '10')
        elif r.dealer_qualifies():
            line = 'Dealer: ' + describe(r.dv)
        else:
            line = 'Dealer: no qualify (' + describe(r.dv) + ')'
        font.text(lcd, line, 6, DEALER_Y + CARD_H + 2, WHITE, 1)

    def draw_player(self):
        lcd = self.lcd
        r = self.table.round
        self.felt(PLAYER_TOP, BAND_H)
        if r is None:
            return
        for i in range(5):
            self.card(r.player[i], CARD_X[i], PLAYER_Y)
        font.text(lcd, 'You: ' + describe(r.pv), 6, PLAYER_Y + CARD_H + 2, WHITE, 1)

    def draw_bottom(self):
        lcd = self.lcd
        t = self.table
        st = t.state
        self.felt(BOTTOM_TOP, BAND_H)
        if st == BETTING:
            font.text_centred(lcd, 'Ante: joystick', 120, BOTTOM_Y + 4, GREY, 1)
            font.text_centred(lcd, 'A deal  X pays  B menu', 120, BOTTOM_Y + 18, WHITE, 1)
        elif st == DECIDING:
            r = t.round
            font.text_centred(lcd, 'A raise %d   B fold' % (r.ante * t.rules.raise_mult), 120, BOTTOM_Y + 4, WHITE, 1)
            font.text_centred(lcd, 'X pays and strategy', 120, BOTTOM_Y + 18, GREY, 1)
        elif st == RESULT:
            r = t.round
            art, label, col = BANNERS[r.outcome]
            if not (art and self.assets.blit(lcd, art, 40, BANNER_Y)):
                font.text_centred(lcd, label, 120, BANNER_Y + 8, col, 2)
            if r.outcome == WIN:
                detail = '%s: ante + raise %d x %d' % (signed(r.net), r.raise_bet, t.rules.raise_pay[r.pv[0]])
            elif r.outcome == NOQUALIFY:
                detail = '%s: ante paid, raise back' % signed(r.net)
            elif r.outcome == FOLD:
                detail = '%s: ante lost' % signed(r.net)
            else:
                detail = signed(r.net) if r.net else 'no change'
            font.text_centred(lcd, detail, 120, BOTTOM_Y + 4, col, 1)
            font.text_centred(lcd, 'A next   B menu', 120, BOTTOM_Y + 18, WHITE, 1)
        elif st == BROKE:
            font.text_centred(lcd, 'Out of chips', 120, BANNER_Y + 8, RED, 2)
            font.text_centred(lcd, 'A take 1000   B menu', 120, BOTTOM_Y + 18, WHITE, 1)

    def draw_all(self):
        """Scene change: full redraw then one show() (deal and result only, HR-026)."""
        lcd = self.lcd
        if not (self.has_table_art and self.assets.background(lcd, 'table')):
            self.felt()
        self.draw_top()
        self.draw_dealer()
        self.draw_player()
        self.draw_bottom()
        lcd.show()

    # ---- the reveal (DR-029 / HR-029) ---------------------------------------------------------
    def reveal(self, one_by_one):
        lcd = self.lcd
        if one_by_one:
            while self.shown < 5:
                t0 = utime.ticks_us()
                self.shown += 1
                if self.shown == 5:
                    break                             # the last card comes with the result redraw
                self.draw_dealer()
                lcd.show_band(DEALER_TOP, BAND_H)
                spent = utime.ticks_diff(utime.ticks_us(), t0) // 1000
                if spent < REVEAL_MS:
                    utime.sleep_ms(REVEAL_MS - spent)
        self.shown = 5

    def finish_hand(self, one_by_one):
        self.reveal(one_by_one)
        self.draw_all()                               # result scene
        self.store.save(self.table.bankroll.balance)  # DR-030: after the result, never mid-reveal
        self.buttons.poll()                           # drop presses made during the reveal

    def paytable(self):
        import stud_pay                               # loaded only while shown
        stud_pay.show(self.lcd, self.buttons, self.table.bankroll.bet, FELT_EDGE, GOLD, WHITE, GREY)
        if 'stud_pay' in sys.modules:
            del sys.modules['stud_pay']
        self.draw_all()

    # ---- input --------------------------------------------------------------------------------
    def handle(self, key):
        """Return False to leave the game."""
        t = self.table
        st = t.state
        if key == 'X' and st != BROKE:
            self.paytable()
            return True
        if st == BETTING:
            delta = {'UP': 5, 'DOWN': -5, 'RIGHT': 25, 'LEFT': -25}.get(key)
            if delta:
                t.adjust_ante(delta)
                self.draw_top()
                self.lcd.show_band(0, TOP_H)
            elif key == 'A':
                t.deal()
                self.shown = 1
                self.draw_all()
            elif key == 'B':
                return False
        elif st == DECIDING:
            if key == 'A':
                t.raise_()
                self.finish_hand(True)
            elif key == 'B':
                t.fold()
                self.finish_hand(False)
        elif st == RESULT:
            if key == 'A':
                t.next_hand()
                self.shown = 1
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
