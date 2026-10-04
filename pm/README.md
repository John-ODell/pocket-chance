# PM channel

How the senior developer and the PM talk. Everything is a file in this repo, so it works across separate sessions and leaves a record.

```
pm/inbox/       dev -> PM   decision requests   DR-001-short-slug.md
pm/outbox/      PM -> dev   rulings             DR-001.md  (same number)
pm/DECISIONS.md PM-maintained log of every approved decision
pm/STATUS.md    dev-maintained status note for John
pm/templates/   decision-request.md
```

## Flow

1. The dev hits a decision that needs approval (see `CLAUDE.md`). They copy `templates/decision-request.md` to `inbox/DR-NNN-slug.md`. NNN is the next unused number.
2. The dev **recommends one option**, with reasons, and moves on to other work. They do not wait idle and do not guess.
3. The PM reads the request, takes it to John in plain language, and gets his answer.
4. The PM writes `outbox/DR-NNN.md` (decision: approved, approved with changes, rejected, or needs more info), then appends a line to `DECISIONS.md`.
5. The dev checks `outbox/` at the start of every session and before starting any task that depends on a pending request. A request without a ruling is **not approved**.

## Hardware review step

Requests marked `Needs HW review: yes` go to the microcontroller expert before the PM takes them to John.

- The expert files `hw/reviews/HR-NNN.md` (NNN matches the DR number it reviews) with a verdict: **fits**, **fits with limits**, or **does not fit**. It includes measured numbers where it can.
- The PM reads the review alongside the request. If the review says **does not fit**, the PM sends the request back to the dev.
- The expert can also raise its own findings (for example "the stock firmware only uses 2 MB of flash"). These go in `hw/reviews/` and the PM treats them as decision requests.

## Rules

- One decision per request. Split bundles.
- Keep requests short enough that John can decide in two minutes. Put detail in an appendix section.
- Rulings are binding. If a ruling turns out to be wrong, file a new request that references the old one. Do not quietly deviate.
- Never edit another party's files: the dev writes `inbox/` and `STATUS.md`, the PM writes `outbox/` and `DECISIONS.md`.
