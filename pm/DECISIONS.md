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
