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
