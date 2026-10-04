# Slots screens and the spin animation. Thin: odds and money live in slots_rules.py / slots_table.py.
#
# Rulings: DR-017/018/019 (via slots_table), DR-020 rev 2 with John's fallback B (HR-020 update:
# option A's 44 KB does not fit beside the menu, so the spin uses three 6,272-byte window buffers,
# 18.8 KB, allocated once on entry), DR-021 rev 2 (order after the last reel stops: windows drawn,
# chips and win line drawn and pushed, save, then three blinks; X = paytable; no auto-spin), DR-023
# (window positions, dark zones), DR-006 (code-drawn stand-in symbols and cabinet without art).
#
# How a frame works (HR-020 limits: nothing opened, stat'ed, constructed or allocated per frame,
# at most one file open per frame, windows pushed straight to the panel):
#   each reel owns a 56x56 window buffer that always holds exactly what its window shows. Per frame
#   the buffer is scrolled up by the step (FrameBuffer.scroll, C memmove) and the rows that appear
#   at the bottom are read from the incoming symbol: a seek + readinto on that symbol's file, kept
#   open while it scrolls in (opened once per symbol change, and the reels are staggered so only one
#   reel changes per frame), or copied from a precomputed stand-in row pattern when the art is
#   missing. Then the buffer is pushed with LCD.show_buf. The main framebuffer is updated once when
#   the reels stop.
#
# Controls   Betting: UP/DOWN bet +-5, LEFT/RIGHT +-25, A spin, X paytable, B menu
#            Result:  A spin again, X paytable, B menu          Broke: A take 1000, B menu

import gc
import utime
import framebuf

import font
from pixfmt import rgb, swap
from slots_rules import SYMBOLS, STAR
from slots_table import SlotsTable, BETTING, RESULT, BROKE, SYM_PX

# Layout (DR-023): three fixed windows; four bands like blackjack.
WIN_X = (18, 92, 166)
WIN_Y = 92
TOP_H = 24                   # 0..23   chips and bet
BOTTOM_TOP = 168             # 168..239 result / banner 176..215, prompts 218 and 228
BAND_H = 72
WIN_LINE_Y = 156             # 156..166 the winning line's name
BLINK_TOP, BLINK_H = WIN_Y - 4, SYM_PX + 8      # band that holds the gold frames
ROW_BYTES = SYM_PX * 2
SYM_BYTES = SYM_PX * ROW_BYTES
HDR = 4
FRAME_US = 20000             # pace the spin at about 50 fps
MEM_REPORT_FRAME = 20        # print gc.mem_free() once, mid-spin (DR-020: the first bench reports it)

BG = rgb(18, 16, 28)
FRAME_COL = rgb(200, 160, 40)
GOLD = rgb(240, 200, 60)
WHITE = rgb(255, 255, 255)
GREY = rgb(160, 160, 160)
RED = rgb(200, 20, 20)
# stand-in symbols, one colour pair each: (background, ink). A bordered square of ink in the middle.
STANDIN = (
    ((120, 10, 20), (255, 80, 90)),      # cherry
    ((130, 120, 10), (255, 240, 80)),    # lemon
    ((150, 70, 0), (255, 160, 40)),      # orange
    ((90, 70, 10), (255, 210, 90)),      # bell
    ((20, 20, 20), (230, 230, 230)),     # bar
    ((100, 0, 0), (255, 60, 60)),        # seven
    ((0, 60, 110), (120, 220, 255)),     # diamond
    ((40, 20, 90), (255, 230, 80)),      # star
)
INNER0, INNER1 = 16, 40      # rows and columns of the stand-in's inner square


def _row_pattern(bg, ink, x0, x1):
    """One 56-pixel row as big-endian RGB565 bytes: bg with ink from x0 to x1-1."""
    out = bytearray(ROW_BYTES)
    b = swap(bg)
    i = swap(ink)
    for x in range(SYM_PX):
        v = i if x0 <= x < x1 else b
        out[2 * x] = v >> 8
        out[2 * x + 1] = v & 0xFF
    return bytes(out)


class Screen:
    def __init__(self, ctx):
        self.lcd = ctx.lcd
        self.assets = ctx.assets
        self.buttons = ctx.buttons
        self.store = ctx.store
        self.table = SlotsTable(ctx.rng, ctx.bankroll)
        self.has_cabinet = self.assets.size('cabinet') is not None
        # Fallback B RAM (DR-020): three window buffers, 18,816 bytes, allocated once here.
        self.win = [bytearray(SYM_BYTES) for _ in range(3)]
        self.win_mv = [memoryview(b) for b in self.win]
        self.win_fb = [framebuf.FrameBuffer(b, SYM_PX, SYM_PX, framebuf.RGB565) for b in self.win]
        self.files = [None, None, None]          # open file of the symbol scrolling into reel i
        self.incoming = [None, None, None]       # symbol id scrolling into reel i (for stand-ins)
        self.mem_mid_spin = None
        self.patterns = {}            # stand-in rows per symbol, built only for symbols without art
        line = self.table.reels.line()
        for i in range(3):
            self.fill_window(i, line[i])
        gc.collect()
        mf = getattr(gc, 'mem_free', None)
        if mf:
            print('RESULT slots mem_free after init=%d' % mf())

    # ---- symbol rows --------------------------------------------------------------------------
    def standin_row(self, sym, row, dst):
        pats = self.patterns.get(sym)
        if pats is None:              # 3 x 112 bytes per symbol, only when its art is missing
            bg, ink = STANDIN[sym]
            b = rgb(*bg)
            i = rgb(*ink)
            pats = (_row_pattern(b, i, 0, SYM_PX), _row_pattern(b, i, 0, 0), _row_pattern(b, i, INNER0, INNER1))
            self.patterns[sym] = pats
        border, plain, square = pats
        if row < 3 or row >= SYM_PX - 3:
            dst[:] = border
        elif INNER0 <= row < INNER1:
            dst[:] = square
        else:
            dst[:] = plain
        # left and right border columns on plain and square rows
        if 3 <= row < SYM_PX - 3:
            b = border
            dst[0:6] = b[0:6]
            dst[ROW_BYTES - 6:] = b[ROW_BYTES - 6:]

    def fill_window(self, i, sym):
        """Load a whole symbol into reel i's window buffer (screen entry and reel reset)."""
        if not self.assets.load('sym_' + SYMBOLS[sym], self.win[i]):
            mv = self.win_mv[i]
            for r in range(SYM_PX):
                self.standin_row(sym, r, mv[r * ROW_BYTES:(r + 1) * ROW_BYTES])

    def begin_incoming(self, i, sym):
        """The symbol that will scroll into reel i next: open its file once (or use stand-in rows)."""
        self.end_incoming(i)
        self.incoming[i] = sym
        r = self.assets.open_sprite('sym_' + SYMBOLS[sym])
        if r is not None:
            self.files[i] = r[0]

    def end_incoming(self, i):
        f = self.files[i]
        if f is not None:
            f.close()
            self.files[i] = None

    def scroll_in(self, i, step, rows_in):
        """Scroll reel i's window up by `step` rows and fill the bottom with rows
        rows_in - step .. rows_in - 1 of the incoming symbol."""
        self.win_fb[i].scroll(0, -step)
        mv = self.win_mv[i]
        dst = mv[(SYM_PX - step) * ROW_BYTES:]
        first = rows_in - step
        f = self.files[i]
        if f is not None:
            f.seek(HDR + first * ROW_BYTES)
            if f.readinto(dst) == step * ROW_BYTES:
                return
        sym = self.incoming[i]
        for k in range(step):
            self.standin_row(sym, first + k, dst[k * ROW_BYTES:(k + 1) * ROW_BYTES])

    # ---- background and bands -----------------------------------------------------------------
    def background(self, y, h):
        """Restore rows y..y+h-1 of the cabinet: from the art, else a code-drawn frame."""
        lcd = self.lcd
        if self.has_cabinet and self.assets.background_rows(lcd, 'cabinet', y, h):
            return
        lcd.fill_rect(0, y, 240, h, BG)
        if y < WIN_Y + SYM_PX + 4 and y + h > WIN_Y - 4:       # the band crosses the windows
            for x in WIN_X:
                lcd.rect(x - 4, WIN_Y - 4, SYM_PX + 8, SYM_PX + 8, FRAME_COL)
                lcd.rect(x - 3, WIN_Y - 3, SYM_PX + 6, SYM_PX + 6, FRAME_COL)
        if y < 2:
            lcd.hline(0, 0, 240, FRAME_COL)
        if y + h > 238:
            lcd.hline(0, 239, 240, FRAME_COL)

    def draw_top(self, balance=None, bet=None):
        lcd = self.lcd
        self.background(0, TOP_H)
        b, w = self.table.stakes()
        if balance is None:
            balance = b
        if bet is None:
            bet = w
        font.text(lcd, '$%d' % balance, 6, 4, GOLD, 2)
        font.text_right(lcd, 'bet %d' % bet, 234, 4, WHITE, 2)

    def draw_windows(self):
        """Blit the window buffers into the framebuffer (so band redraws show the reels)."""
        for i in range(3):
            self.lcd.blit(self.win_fb[i], WIN_X[i], WIN_Y)

    def draw_win_line(self):
        self.background(WIN_LINE_Y - 2, 14)
        last = self.table.last
        if last and self.table.state == RESULT:
            win, label = last
            font.text_centred(self.lcd, label if win else 'no win', 120, WIN_LINE_Y, GOLD if win else GREY, 1)

    def draw_bottom(self):
        lcd = self.lcd
        self.background(BOTTOM_TOP, BAND_H)
        st = self.table.state
        if st == RESULT:
            win, label = self.table.last
            if label == 'three ' + SYMBOLS[STAR]:
                if not self.assets.blit(lcd, 'banner_jackpot', 20, 176):
                    font.text_centred(lcd, 'JACKPOT!', 120, 184, GOLD, 2)
            elif win:
                font.text_centred(lcd, 'WIN +%d' % win, 120, 184, GOLD, 2)
            else:
                font.text_centred(lcd, 'no win', 120, 184, GREY, 2)
        elif st == BROKE:
            font.text_centred(lcd, 'Out of chips', 120, 184, RED, 2)
        if st == BROKE:
            font.text_centred(lcd, 'A take 1000   B menu', 120, 218, WHITE, 1)
        else:
            font.text_centred(lcd, 'A spin  X paytable  B menu', 120, 218, WHITE, 1)
            font.text_centred(lcd, 'joystick: bet', 120, 228, GREY, 1)

    def draw_all(self):
        """Scene change: full redraw then one show() (DR-005)."""
        lcd = self.lcd
        if not (self.has_cabinet and self.assets.background(lcd, 'cabinet')):
            self.background(0, 240)
        self.draw_top()
        self.draw_windows()
        self.draw_win_line()
        self.draw_bottom()
        lcd.show()

    # ---- the spin -----------------------------------------------------------------------------
    def spin(self):
        t = self.table
        balance_before, bet = t.stakes()
        win, label = t.spin()                        # stops are chosen now and the balance settled,
        self.draw_top(balance_before - bet, bet)     # but the screen only shows the stake taken
        self.background(WIN_LINE_Y - 2, 14)
        self.lcd.show_band(0, TOP_H)
        self.lcd.show_band(WIN_LINE_Y - 2, 14)
        plan = t.plan()
        strips = t.reels.strips
        for i in range(3):                           # reposition each reel on its start symbol
            self.fill_window(i, strips[i][plan.top[i]])
            self.begin_incoming(i, strips[i][(plan.top[i] + 1) % len(strips[i])])
        lcd = self.lcd
        prev_pos = [0, 0, 0]
        frame = 0
        done = False
        while not done:
            done = plan.step()                       # the landing frame is drawn too
            t0 = utime.ticks_us()
            frame += 1
            for i in range(3):
                step = plan.pos[i] - prev_pos[i]
                if step == 0:
                    continue                         # this reel rests (or has not started yet)
                prev_pos[i] = plan.pos[i]
                off = plan.off[i]
                if plan.changed[i]:
                    # the incoming symbol finished scrolling in this frame: its last `tail` rows,
                    # then the first `off` rows of the symbol after it
                    tail = step - off
                    if tail:
                        self.scroll_in(i, tail, SYM_PX)
                    if plan.moving(i):
                        s = strips[i]
                        self.begin_incoming(i, s[(plan.top[i] + 1) % len(s)])
                        if off:
                            self.scroll_in(i, off, off)
                    else:
                        self.end_incoming(i)         # landed: nothing more scrolls in
                else:
                    self.scroll_in(i, step, off)
                lcd.show_buf(WIN_X[i], WIN_Y, SYM_PX, SYM_PX, self.win[i])
            if frame == MEM_REPORT_FRAME:
                mf = getattr(gc, 'mem_free', None)
                self.mem_mid_spin = mf() if mf else None
                print('RESULT slots mem_free mid-spin=%s' % self.mem_mid_spin)
            spent = utime.ticks_diff(utime.ticks_us(), t0)
            if spent < FRAME_US:
                utime.sleep_us(FRAME_US - spent)
        for i in range(3):
            self.end_incoming(i)
        # HR-021 order: windows into the framebuffer, chips and win line, pushed; save; blink.
        self.draw_windows()
        self.draw_top()
        self.draw_win_line()
        self.draw_bottom()
        lcd.show_band(0, TOP_H)
        lcd.show_band(WIN_LINE_Y - 2, 240 - (WIN_LINE_Y - 2))
        self.store.save(t.bankroll.balance)
        if win:
            self.blink()
        self.buttons.poll()                          # drop presses made during the spin

    def blink(self):
        lcd = self.lcd
        for _ in range(3):
            for x in WIN_X:
                lcd.rect(x - 2, WIN_Y - 2, SYM_PX + 4, SYM_PX + 4, GOLD)
                lcd.rect(x - 1, WIN_Y - 1, SYM_PX + 2, SYM_PX + 2, GOLD)
            lcd.show_band(BLINK_TOP, BLINK_H)
            utime.sleep_ms(120)
            self.background(BLINK_TOP, BLINK_H)
            self.draw_windows()
            lcd.show_band(BLINK_TOP, BLINK_H)
            utime.sleep_ms(120)

    # ---- paytable -----------------------------------------------------------------------------
    def paytable(self):
        lcd = self.lcd
        lcd.fill(BG)
        bet = self.table.bankroll.bet
        font.text_centred(lcd, 'Pays at bet %d' % bet, 120, 8, GOLD, 2)
        y = 34
        for label, pay in self.table.paytable_rows(bet):
            font.text(lcd, label, 24, y, WHITE, 1)
            font.text_right(lcd, '%d' % pay, 216, y, GOLD, 1)
            y += 16
        font.text_centred(lcd, 'one line, 93.8% return', 120, 206, GREY, 1)
        font.text_centred(lcd, 'any key: back', 120, 222, GREY, 1)
        lcd.show()
        self.buttons.wait_any()
        self.draw_all()

    # ---- input --------------------------------------------------------------------------------
    def handle(self, key):
        """Return False to leave the game."""
        t = self.table
        st = t.state
        if key == 'B':
            return False
        if key == 'X' and st != BROKE:
            self.paytable()
            return True
        delta = {'UP': 5, 'DOWN': -5, 'RIGHT': 25, 'LEFT': -25}.get(key)
        if st == BETTING:
            if delta:
                t.adjust_bet(delta)
                self.draw_top()
                self.lcd.show_band(0, TOP_H)
            elif key == 'A':
                self.spin()
        elif st == RESULT:
            if key == 'A':
                t.next()
                if t.state == BETTING:
                    self.spin()
                else:
                    self.draw_all()
            elif delta:
                t.next()
                if t.state == BETTING:
                    t.adjust_bet(delta)
                self.draw_all()
        elif st == BROKE:
            if key == 'A':
                t.refill()
                self.draw_all()
                self.store.save(t.bankroll.balance)
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
            for i in range(3):
                self.end_incoming(i)


def run(ctx):
    Screen(ctx).run()
