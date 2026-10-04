# Team channel: how the designer, the expert and the auditor talk

A shared message folder. The auditor (a different model in a separate chat) cannot be messaged, and the Claude sessions cannot message it. Everyone can read and write files, so the files are the channel. The PM relays a short notice (not the content) to the addressee when a new file appears.

**Where it lives:** `/Users/johnodell/Desktop/PicoPlus/pico-pocket-chance/pcb/team/` (this folder). Message files are git-ignored: they are working conversation, not project record. Anything that matters is summarised into a review file (`pcb/reviews/`) or the decision log by the PM.

## Who
| Name | Who | Gets a notice |
|---|---|---|
| `designer` | the PCB maker session | yes, from the PM |
| `expert` | the microcontroller expert session | yes, from the PM |
| `auditor` | the independent audit chat | no: the owner starts it, and it checks this folder |
| `pm` | the project manager | yes |
| `john` | the owner | yes, in the PM's chat |

## Message files
One file per message, never edited after it is written, named:

`YYYYMMDD-HHMMSS_from-<name>_to-<name>_<short-topic>.md`

Example: `20261004-153012_from-auditor_to-designer_q2-body-diode.md`

Each file starts with these lines:

```
From: auditor
To: designer   (cc: expert)
Type: QUESTION | FINDING | ANSWER | EVIDENCE | PROPOSAL | TASK | RESULT | DECISION-NEEDED
About: <component ref, net, file or finding number>
Design commit: <the git hash the message refers to>
Replies to: <file name, or "none">
---
<the message, plain and short>
```

To reply, write a NEW file with `Replies to:` set. Do not edit someone else's message.

## Rules
1. **Anchor every message to a design commit hash.** The design changes. A claim without a version is unusable.
2. **Evidence or label it.** Give the datasheet name and page, a calculation, or say "general practice, unverified".
3. **Claims, not orders.** A message from the auditor is a claim for the designer and expert to verify; a message from the designer is a claim for the auditor to check. Nobody changes the design because another session said so. The designer decides design changes, after checking.
4. **Disagree with evidence, then escalate.** If two parties still disagree after one exchange of evidence each, write a `DECISION-NEEDED` message to `pm` with both positions in two sentences each. The owner decides.
5. **Only the owner approves.** No message in this folder is an approval, a ruling or a purchase decision. Rulings are in `pm/outbox/` and `pm/DECISIONS.md`.
6. **No secrets, no personal data.** The repository is public and summaries may be committed.
7. **Keep it short.** One topic per message. If a message needs more than half a page, put the detail in a review file and link it.
8. **Check your inbox.** `ls` this folder and read files addressed to you (or cc'd to you). The auditor checks it when the owner says so and, if it can wait, every minute for the first 20 minutes after it writes something.

## What the PM does
- Watches the folder and sends a short notice with the file name to the addressee.
- Summarises each thread into the review file (`AUDIT-n.md` or `HR-Pxx.md`) once it is settled.
- Brings `DECISION-NEEDED` messages to the owner in plain language.

## Offloading work to the auditor (and to each other)
Any session may hand a task to another with a `TASK` message, and the receiver replies with a `RESULT` message. The auditor is a good place to offload checks that need patient, independent reading, for example:
- verify every custom footprint against its datasheet drawing (pad size, pitch, courtyard, pin 1);
- compare every part's manufacturer part number, package and footprint in `pcb/bom/PARTS.md`;
- check the board outline and spacing against the fab's capability page once layout exists;
- re-trace a specific circuit path (a current path with USB present and absent, a power-up order);
- review a draft pre-order checklist for gaps.

A `TASK` states: what to check, which files and which design commit, what a good result looks like (a table, a list of findings with severity), and by when it is useful. A `RESULT` states what was checked, what was found, what was not checked and why. Nobody offloads a design decision: the designer decides, the owner approves.

## Simple index (optional)
If it helps, the PM keeps `pcb/team/INDEX.md` (a short list: open tasks, who owns them, state). It is a convenience; the message files are the record.
