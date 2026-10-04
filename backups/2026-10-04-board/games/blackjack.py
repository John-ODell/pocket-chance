# Blackjack screens and input. Thin: all rules live in blackjack_rules.py / blackjack_table.py.
# Rulings: DR-005 (table background read on scene entry only; bands pushed for small changes;
# full show() on scene change), DR-006 (code-drawn cards, chips and felt when art is missing),
# DR-007 (save once per finished round, after the redraw so the result shows instantly), DR-011 ("Shuffling" moment), DR-012/014 (controls, limits).
#
# Controls   Betting: UP/DOWN bet +-5, LEFT/RIGHT +-25, A deal, B back to menu
#            Playing: A hit, B stand, X double (when allowed)
#            Result:  A next hand, B menu      Broke: A take 1000 chips, B menu

import utime

import font
from pixfmt import rgb, KEY
from cards import card_name, hand_value
from blackjack_rules import BLACKJACK, WIN, LOSE, PUSH, BUST
from blackjack_table import Table, BETTING, PLAYING, RESULT, BROKE

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
TOP_H = 24                 # bankroll and bet line (art keeps it calm)
DEALER_Y = 30
PLAYER_Y = 104
BOTTOM_Y = 200             # prompts (art keeps the bottom 40 px calm)
BANNER_Y = 166
CHIP_DENOMS = (500, 100, 25, 5)

BANNERS = {BLACKJACK: ('banner_blackjack', 'BLACKJACK!', GOLD), WIN: ('banner_win', 'YOU WIN', GOLD),
           LOSE: ('banner_lose', 'DEALER WINS', GREY), PUSH: ('banner_push', 'PUSH', WHITE),
           BUST: ('banner_bust', 'BUST', RED)}


class Screen:
    def __init__(self, ctx):
        self.lcd = ctx.lcd
        self.assets = ctx.assets
        self.buttons = ctx.buttons
        self.store = ctx.store
        self.table = Table(ctx.rng, bankroll=ctx.bankroll)
        self.has_table_art = self.assets.size('table') is not None

    # ---- background -------------------------------------------------------------------------
    def felt(self, y=0, h=240):
        lcd = self.lcd
        if self.has_table_art and self.assets.background_rows(lcd, 'table', y, h):
            return
        lcd.fill_rect(0, y, 240, h, FELT)
        # plain border when there is no art
        for yy in (0, 239):
            if y <= yy < y + h:
                lcd.hline(0, yy, 240, FELT_EDGE)
        lcd.vline(0, y, h, FELT_EDGE)
        lcd.vline(239, y, h, FELT_EDGE)

    # ---- sprites with fallbacks ---------------------------------------------------------------
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
        lcd = self.lcd
        if self.assets.blit(lcd, 'c_back', x, y):
            return
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

    def hand(self, cards, y, hide_second=False):
        n = len(cards)
        step = CARD_W if n <= 5 else (236 - CARD_W) // (n - 1)
        x = (240 - (CARD_W + step * (n - 1))) // 2
        for i, c in enumerate(cards):
            if hide_second and i == 1:
                self.card_back(x, y)
            else:
                self.card(c, x, y)
            x += step

    # ---- regions ----------------------------------------------------------------------------
    def draw_top(self):
        lcd = self.lcd
        self.felt(0, TOP_H)
        bank = self.table.bankroll
        font.text(lcd, '$%d' % bank.balance, 6, 4, GOLD, 2)
        self.chip(bank.bet, 150, 0)
        font.text_right(lcd, '%d' % bank.bet, 234, 4, WHITE, 2)

    def draw_dealer(self):
        r = self.table.round
        self.felt(DEALER_Y - 6, PLAYER_Y - DEALER_Y)
        if r is None:
            return
        hide = r.hole_hidden()
        self.hand(r.dealer, DEALER_Y, hide)
        shown = r.dealer[:1] if hide else r.dealer
        font.text(self.lcd, 'Dealer %d' % hand_value(shown)[0], 6, DEALER_Y + CARD_H + 2, WHITE, 1)

    def draw_player(self):
        r = self.table.round
        self.felt(PLAYER_Y - 6, BANNER_Y - PLAYER_Y + 6)
        if r is None:
            return
        self.hand(r.player, PLAYER_Y)
        total, soft = hand_value(r.player)
        font.text(self.lcd, 'You %d%s' % (total, ' soft' if soft else ''), 6, PLAYER_Y + CARD_H + 2, WHITE, 1)

    def draw_bottom(self):
        lcd = self.lcd
        self.felt(BANNER_Y, 240 - BANNER_Y)
        st = self.table.state
        if st == BETTING:
            font.text_centred(lcd, 'Bet: joystick', 120, BOTTOM_Y + 4, GREY, 1)
            font.text_centred(lcd, 'A deal   B menu', 120, BOTTOM_Y + 18, WHITE, 1)
        elif st == PLAYING:
            font.text_centred(lcd, 'A hit   B stand', 120, BOTTOM_Y + 4, WHITE, 1)
            if self.table.can_double():
                font.text_centred(lcd, 'X double', 120, BOTTOM_Y + 18, WHITE, 1)
        elif st == RESULT:
            art, label, col = BANNERS[self.table.round.outcome]
            if not self.assets.blit(lcd, art, 40, BANNER_Y):
                font.text_centred(lcd, label, 120, BANNER_Y + 8, col, 2)
            net = self.table.round.net
            if net:
                font.text_centred(lcd, '%s%d' % ('+' if net > 0 else '', net), 120, BOTTOM_Y + 4, col, 1)
            font.text_centred(lcd, 'A next   B menu', 120, BOTTOM_Y + 18, WHITE, 1)
        elif st == BROKE:
            font.text_centred(lcd, 'Out of chips', 120, BANNER_Y + 8, RED, 2)
            font.text_centred(lcd, 'A take 1000   B menu', 120, BOTTOM_Y + 18, WHITE, 1)

    def draw_all(self):
        """Scene change: full redraw then one show() (DR-005)."""
        lcd = self.lcd
        if not (self.has_table_art and self.assets.background(lcd, 'table')):
            self.felt()
        if self.table.round is None:
            # an idle table: show the card back as decoration
            self.card_back(100, DEALER_Y)
        self.draw_top()
        self.draw_dealer()
        self.draw_player()
        self.draw_bottom()
        lcd.show()

    def shuffling(self):
        lcd = self.lcd
        self.felt(BANNER_Y, 240 - BANNER_Y)
        font.text_centred(lcd, 'Shuffling...', 120, BANNER_Y + 8, WHITE, 2)
        lcd.show_band(BANNER_Y, 240 - BANNER_Y)
        utime.sleep_ms(700)

    # ---- input -------------------------------------------------------------------------------
    def finish_round(self):
        self.draw_all()                                  # show the result first (HR-F02: save is ~50-100 ms)
        self.store.save(self.table.bankroll.balance)     # once per finished round (DR-007)

    def handle(self, key):
        """Return False to leave the game."""
        t = self.table
        st = t.state
        if st == BETTING:
            delta = {'UP': 5, 'DOWN': -5, 'RIGHT': 25, 'LEFT': -25}.get(key)
            if delta:
                t.adjust_bet(delta)
                self.draw_top()
                self.lcd.show_band(0, TOP_H)
            elif key == 'A':
                t.deal()
                if t.shuffled:
                    self.shuffling()
                if t.state == RESULT:
                    self.finish_round()
                else:
                    self.draw_all()
            elif key == 'B':
                return False
        elif st == PLAYING:
            if key == 'A':
                t.hit()
            elif key == 'B':
                t.stand()
            elif key == 'X' and t.can_double():
                t.double()
            else:
                return True
            if t.state == RESULT:
                self.finish_round()
            else:
                self.draw_player()
                self.draw_bottom()
                self.lcd.show_band(PLAYER_Y - 6, 240 - PLAYER_Y + 6)
        elif st == RESULT:
            if key == 'A':
                t.next_hand()
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
        while True:
            for key in buttons.poll():
                if not self.handle(key):
                    return
            utime.sleep_ms(15)


def run(ctx):
    Screen(ctx).run()
