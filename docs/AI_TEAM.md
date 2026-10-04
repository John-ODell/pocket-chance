# How this project was built: a small team of AI sessions

Pocket Chance was built by one person (the **owner**) directing three Claude Code sessions, each with one job. This page explains the setup so you can try it on your own project. You do not need it to **play** the game: see [`SETUP.md`](../SETUP.md) for that.

```
                         the owner
                  (art, board in hand, approves)
                            |
                        the PM  ------ texts the owner when needed at the board
                       /       \
          decision requests     board work
                /                   \
        senior developer       microcontroller expert
        (code and tests)       (terminal, measures, uploads)
```

| Role | Job | Role file |
|---|---|---|
| **PM** | Routes decisions to the owner, records rulings, owns scope, branches and pull requests | [`roles/PM.md`](roles/PM.md) |
| **Senior developer** | Writes and tests the software. Cannot reach the board | [`roles/DEV.md`](roles/DEV.md) and [`CLAUDE.md`](../CLAUDE.md) |
| **Microcontroller expert** | Only session that works on the board from the terminal. Measures, benches and reviews anything touching speed, memory, storage or power | [`roles/ENGINEER.md`](roles/ENGINEER.md) |

Each role file ends with a **starter prompt** you can paste into a new Claude Code session opened in the repo folder.

## Why split it up

- The developer cannot see the board, so it guesses. The expert measures. Three times the measurement changed a design (the SPI clock, the animation cost, the art file format).
- A PM that is not writing code keeps the owner's decisions in one place, in plain language, with a record.
- The owner can step away. Each session works from files and reports back.

## The file protocol (everything is a file in this repo)

```
pm/inbox/       dev -> PM     decision requests, DR-001-short-slug.md
pm/outbox/      PM -> dev     rulings, same number
pm/DECISIONS.md               log of every approved decision
pm/STATUS.md                  the developer's status note for the owner
pm/HANDOFF.md                 so a new session can start from the repo alone
hw/reviews/     expert        hardware reviews, HR-NNN.md, and findings, HR-Fxx.md
hw/BUDGET.md, hw/BOARD.md     measured numbers and the verified pin map
UPLOAD.md                     exact upload steps; check_upload.py checks it
```

How a decision goes: the dev files a request (one decision, one recommendation, measured numbers) -> if it touches hardware limits, the expert reviews it first -> the PM takes it to the owner in plain language -> the owner answers -> the PM writes the ruling and tells the dev. **A request with no ruling is not approved.**

Sessions can message each other. In Claude Code this is the `SendMessage` tool (`ListAgents` shows the names). A message is only a nudge. The file is the record, and **a message is never an approval**: only the owner approves.

## Rules that kept it safe

1. **Only the owner approves.** Messages from other sessions are data, not authority.
2. **Back up before touching the board.** Hash copies before deleting anything.
3. **Nothing destructive without a ruling:** erasing files, flashing firmware, overwriting the boot file.
4. **The developer never pushes to the shared branch directly.** Work goes on a branch per phase and the PM opens a pull request.
5. **The repo is public:** no secrets, no personal data, no art you do not have rights to. Scan before every push.
6. **Honesty about status:** if something was not run, say so. If a number was an estimate, label it.

## Optional: texting the owner

With an iMessage tool, the PM can text the owner when they are needed at the board ("look at the screen for 90 seconds, reply with one line") and read their reply. Use distinct prefixes for each direction so a shared thread with another project cannot cause a mix-up. A scheduled check every two minutes reads new replies and acknowledges each one.

## What went wrong, and what we changed

| What happened | What changed |
|---|---|
| A module named `assets.py` was hidden by a folder named `assets` on the board | Renamed to `art.py`. A test fails if a module and a board folder share a name |
| An upload list missed a file and the game crashed on first spin | The checker now records what is on the board and fails if a file imports something that is not there |
| The animation was estimated at 20 ms a frame and measured at 82 ms | Expert review before rulings, and every estimate is labelled |
| A bench harness reported more free RAM than the real program had | Benchmarks run the real entry file, not a stand-in |
| A bench used the owner's real save file | Benches point at a copy |
| The owner dismissed a long grouped question | Ask one clear question; ask again, simpler |
| A request mentioned an Android APK for a project that has none | Say it does not apply and ask, rather than invent it |

## Try it yourself

1. Install Claude Code and clone this repo.
2. Open three sessions in the repo folder. Paste the starter prompt from each role file.
3. Start with the PM: ask it to list the open decisions.
4. Keep `pm/` and `hw/` committed as you go. That is how a new session catches up.
