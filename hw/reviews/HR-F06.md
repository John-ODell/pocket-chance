# HR-F06: Caribbean "freeze" on the board (step 1o build, main `e8244ec`), 2026-10-04 evening

- **Status: CLOSED, operator error** (John via the PM, 2026-10-05: he was playing it wrong). This is consistent with what the board showed: the program was alive in its key loop, waiting for a key the screen in front of him accepts. No hardware or code fault. The safety net (HR-073) stays filed, not installed. If a real freeze ever appears, the plan below still applies.
- Earlier status, kept for the record: open, not reproduced (PM's ruling 2026-10-04 late evening). Plan if it happens again: John leaves the board plugged in, I read the button pins live (`hwtest/bounce.py`) and `/save.json` (balance rule below), then the half-speed panel trial from the mount. The program had not crashed and had not hung: it was alive in its key-polling loop. The rules and state machine are clean under 860,000 scripted keys on the Mac, including John's reported path. What is left is on the board: either the A press never reached the program, or the panel stopped showing what the program drew. Two cheap discriminators are listed at the end.
- Reviewer: microcontroller expert. Second freeze of the day; the first (after a Stud session, same evening) was a different kind: the USB serial port went dead and only a replug brought it back (hw/BOARD.md).

## What the board said
John reported Caribbean frozen. The port still enumerated as a MicroPython board (not RPI-RP2, so his BOOT press did not enter the bootloader). `hwtest/peek_port.py` read the port without resetting: nothing buffered, no reply to a newline, and **one Ctrl-C returned at once**:
```
RESULT after caribbean mem_free=62096
Traceback (most recent call last):
  File "main.py", line 379, in <module>
  File "main.py", line 374, in main
  File "main.py", line 318, in play
  File "/games/caribbean.py", line 336, in run
  File "/games/caribbean.py", line 330, in run
KeyboardInterrupt:
```
Line 330 is `utime.sleep_ms(15)` in `Screen.run()`'s `while True: for key in buttons.poll(): ...` loop. So at the moment of the freeze the interpreter was running, the game loop was polling the buttons every 15 ms, and no exception had been raised (an exception would have ended the program and printed a traceback by itself). 62,096 B free after the game's teardown is normal (HR-066: 65.7 KB scripted boot, 50 KB in play).

A minute later John had replugged and restarted Caribbean; a read-only command of mine (pin levels, saves) sent its own Ctrl-C and ended his game (`RESULT after caribbean mem_free=60736`). My mistake, reported to the PM; nothing on the filesystem was touched. The port is John's until the PM says otherwise.

## What the code says (installed files, byte-identical to `e8244ec`)
- `caribbean.py` `handle()`: X = help in every state but Broke; Betting takes joystick/A/B; Deciding takes A/Y/B; Result and Broke take A/B. **No state lacks an exit; B leaves from everywhere except mid-flop, where B = fold.** Nothing answers the joystick PRESS, but no game does.
- `buttons.py`: edge detect on pull-up inputs; a held key fires once and re-arms on release; the deal and the showdown each end with one `poll()` to drop presses made during the 300 ms pauses (by design, DR-066).
- `lcd.py`: every panel write is a blocking `spi.write`; no DMA, nothing left running between calls. The result screen is one `show()` then `store.save()` (two small file writes and two renames).
- **Mac fuzz** (`hwtest/car_fuzz/fuzz.py`, the real `caribbean*.py` + `poker/cards/bankroll` with stubbed lcd/font/assets/utime): seats 0–4, 40 seeds each, 4,000 random keys each (all nine keys, including the unhandled ones, and presses queued "during the pauses"), starting banks 1000 and 30: **800,000 keys, no exception, longest run of keys that changed nothing 57** (random unhandled keys). 2,199 x3 results, 73,879 exits and re-entries, help from Betting/Deciding/Result, Broke → refill, 20 x3 hands followed by more play. **`targeted.py`, John's path**: bank 966 (his save), 4 seats, first three hands after entering, Ante 15 or 20, HIGH call: **20,000 seeds × 3 hands, every hand reached Result and Next**, outcomes spread as expected (lose 25,190 / win 17,316 / push 15,816 / x3 hands 1,678).

## What this rules out and what it leaves
Ruled out: a crash, a hard hang, an infinite loop, a state with no way out, a MicroPython-only exception path (that would have printed), a DMA/display race (there is no DMA). Left, both only testable at the board:
1. **The press was not registered.** The program would then sit on the flop screen with the prompt showing, which is what a "freeze on calling HIGH" looks like. Candidates: the A button itself (mechanical; A has been fine all day in the menu and Blackjack), or a press timed inside the deal's 300 ms pause and dropped by design, then no second press.
2. **The panel stopped showing updates while the game went on.** The ST7789 is driven at 62.5 MHz, about four times its specified write rate (DR-050; John's eyeball test at that rate was clean, but short). A single corrupted command byte, for instance the memory-write command 0x2C, makes the panel ignore the pixel data that follows, so the image stays while the program continues, exactly the observed state. The first "freeze" killing USB is not explained by this, so it would be a second mechanism.

## Discriminators (no install, no delete)
- **Balance check (John, now):** before the hand that freezes, note the balance in the top-left. After the replug the menu's Caribbean shows the saved balance. If it moved by that hand's result, the showdown ran and the save was written, so the panel froze (case 2). If it is unchanged, the press never reached the game (case 1). `/save.json` on the board gives the same answer to me when the port is free. Dev's refinement: at the flop the Ante is only displayed as taken (`stakes()`); the bankroll changes at settle, so the rule holds exactly, except that a PUSH hand (dealer fails to qualify, about one in three) leaves the balance unchanged either way and is ambiguous on its own.
- **`/error.log` (once step 1p is on the board, HR-073):** a freeze with no fresh `/error.log` afterwards proves no exception was involved; a fresh one names the line.
- **At the next freeze, do not replug first.** Tell me: a Ctrl-C gives the exact line again, and a live read of the nine button pins while John presses tells case 1 from case 2 directly (`hwtest/bounce.py` already does this).
- **Lower SPI clock trial (from the mount, nothing installed):** run the real program with the panel at 31.25 MHz for a long Caribbean session; if the freezes stop, case 2 is confirmed and the fix is a clock ruling, not a code change.
