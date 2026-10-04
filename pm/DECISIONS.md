# Decision log

Maintained by the PM. Newest at the bottom. Format: `DD-Mon | DR-NNN | decision | who approved`.

| Date | ID | Decision | Approved by |
|---|---|---|---|
| 2026-10-03 | D-000 | Project direction: a handheld casino app. Blackjack first, then slots. Baccarat optional later. Old five games stay in `main_monolith.py` for reference only. | John (chat) |
| 2026-10-03 | D-001 | Source art is 24-bit BMP made or converted by John. A Mac-side script converts it to RGB565 for the board. Exact spec in `assets/ASSETS.md` (draft, pending dev review). | John (chat), draft |
| 2026-10-03 | D-002 | Code is uploaded by John through Viper IDE. The dev keeps `UPLOAD.md` current. | John (chat) |
| 2026-10-03 | DR-004 | Pillow allowed in Mac-side tools only | John |
| 2026-10-03 | DR-009 | Dealer stands on all 17 (parameter `hit_soft_17`) | John |
| 2026-10-03 | DR-010 | Blackjack pays 3:2, winnings round down | John |
| 2026-10-03 | DR-011 | 6 decks, reshuffle after 75% dealt | John |
| 2026-10-03 | DR-012 | Hit, stand, double only; no insurance or surrender; splitting later as its own request | John |
| 2026-10-03 | DR-013 | Start at 1000 chips; free refill when broke | John |
| 2026-10-03 | DR-014 | Bets 5 to 500 in steps of 5; `chip_1` art not needed | John |
| 2026-10-03 | HR-F01 | Reflash board to MicroPython v1.29.0 RP2040-Plus 16 MB build (done by John; main.py restored from backup). Resulting SPI clock regression under investigation. | John |
| 2026-10-04 | DR-001 | Layout A: `/lib`, `/games`, thin entry; new entry installs as `/pocket.py` | John |
| 2026-10-04 | DR-002 | Raw RGB565 with 4-byte size header, `.565` | John |
| 2026-10-04 | DR-003 | Big-endian RGB565, no swap on load. Confirmed on the panel (left half red); orientation upright landscape | John |
| 2026-10-04 | DR-005 | Stream assets from flash; one 16 KB scratch; push bands, not full frames | John |
| 2026-10-04 | DR-006 | Art sizes stand; 4 pilot images first | John |
| 2026-10-04 | DR-007 | `/save.json`, atomic write once per round | John |
| 2026-10-04 | DR-008 | Fall back to `/save.bak`, then fresh start, with messages | John |
| 2026-10-04 | DR-015 | Fast SPI fix at boot via `lib/clocks.py`, off switch `FAST_SPI`; fallback request is 12_000_000 | John |
| 2026-10-04 | D-003 | Erase the old `main.py` from the board (John: backed up as `backups/2026-10-03/main.py`, same as `main_monolith.py` in git and on GitHub). Expert verifies the hash first. | John |
| 2026-10-04 | D-004 | ~~No dedicated hardware reviewer.~~ **Reversed the same day.** John meant he would not add his usual PR/code reviewer. The hardware expert and the `Needs HW review` step stay in force. | John |
| 2026-10-04 | D-005 | PM and John text each other over iMessage. PM texts start with "J-boy"; John replies start with "JBoy:". The PM ignores texts starting "PM:" or "Wordle:". Used for: asking John to look at the board or take an action. | John |
| 2026-10-04 | D-006 | No separate PR/code reviewer is added to this project (the dev's tests and the PM's review are enough for now). The hardware expert stays on call. | John |
| 2026-10-04 | DR-016 | Split pairs: split once, Y button, aces one card each, double after split OK, 21 after split pays 1:1. House edge about 0.55%. | John |
| 2026-10-04 | D-007 | Add a `menu_background` image (240x240, same .565 pipeline as `table`) behind the main menu. John supplied the art (`image_assets/menu_background.bmp`, 451x258, centre-cropped to 240x240). | John |
| 2026-10-04 | D-008 | Scope: add slots, then Caribbean Stud, then Ultimate Texas Hold'em (in that order; each needs its own rules/odds rulings before build). Menu will need scrolling or a submenu for 5 items. Other players are not simulated (they do not affect odds). | John |
| 2026-10-04 | DR-017 | Slots: 3 reels, one centre payline, 8 symbols, 32-stop virtual strips | John |
| 2026-10-04 | DR-018 | Slots paytable A: RTP 93.84%, 1000x fixed jackpot (three stars), hit 1 in 3.6 | John |
| 2026-10-04 | DR-019 | Slots bets 5 to 100, steps of 5, shared bankroll | John |
| 2026-10-04 | DR-022 | Menu: scrolling 3-row list; short names "Carib. Stud", "Ult. Hold'em" | John |
| 2026-10-04 | DR-023 | Slots art list adopted; pilot sym_cherry, sym_star, sym_bar | John |
| 2026-10-04 | DR-020 | Slots spin animation rev 2: real symbols scroll, symbols in RAM, staggered reels, direct push; RAM option A (about 44 KB), fallback B if mid-spin free RAM under about 20 KB | John |
| 2026-10-04 | DR-021 | Slots wins rev 2: show result, then save, then 3 blinks; no auto-spin; X shows paytable; jackpot banner on three stars | John |
| 2026-10-04 | DR-024 | Sprite sheets: one .565 per family (cards, chips, banners, icons, slot symbols); John still draws separate BMPs and the converter packs them | John |
| 2026-10-04 | D-009 | Slots dropped. A classic multi-line 5-reel machine does not fit the board's RAM, and a 3-reel single line is not worth the cost. Next game is Caribbean Stud, then Ultimate Texas Hold'em. Slots rulings DR-017 to DR-023 stay on file as history. John no longer needs to draw slot art. | John |
| 2026-10-04 | DR-025 to DR-032 | Caribbean Stud approved as filed: ante, 5+5 cards, dealer shows one, fold or raise 2x, dealer qualifies A-K or better, raise paytable 1/2/3/4/5/7/20/50/100, no progressive; A deal/raise, B fold/menu, X paytable; ante 5-100 capped at a third of the bankroll; hole cards flip 300 ms apart; save once per hand; menu label "Caribbean"; reuse cards/chips/table, optional banner_noqualify and icon_stud. House edge about 5.2% of the ante. Expert limits apply (HR-026, HR-029). | John |
| 2026-10-04 | D-011 | PCB maker may download the public reference documents into the local, ignored `pcb/refs/`: Raspberry Pi RP2040 datasheet, "Hardware design with RP2040", Winbond W25Q128JV datasheet, ST7789 datasheet, Waveshare Pico-LCD-1.3 wiki page, and one PCB fab capabilities page. Official sources only; nothing committed or published; each URL and date recorded in `pcb/refs/SOURCES.md`. | John |
