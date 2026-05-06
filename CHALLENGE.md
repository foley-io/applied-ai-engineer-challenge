# The Foley Applied AI Engineer Challenge

Welcome. This repo is the take-home portion of the interview for the Applied AI
Engineer role. We respect your time — the target is **2 hours of focused work**.
If you're spending a full weekend on this, stop and submit what you have.

## What you're looking at

A small, working AI agent that reviews driver compliance applications. It runs.
It calls tools. It produces output. It's the kind of code an enthusiastic
intermediate engineer might ship after a hackathon — half-finished, half-broken,
half-thoughtful. It is **intentionally flawed**. Your job is to find what
matters and tell us why.

## What we want from you

### 1. A review (`REVIEW.md`)

Use the template in `REVIEW_TEMPLATE.md`. Identify the **top 5 issues** you'd
fix and rank them. For each, tell us:
- Where it is (file + line range)
- What's wrong
- Why it matters in *production*, not in theory
- What you'd do about it

We are **not** scoring on completeness. A cleanly argued top-5 beats a dump
of 30 issues. Prioritization is the point.

### 2. One pull request

Pick **one** thing to actually fix or build. Could be:
- A fix for one of the issues you ranked
- A small new capability (e.g. a tool, a guardrail, an eval)
- A refactor that unlocks something specific

Keep it small. Keep it defensible. We'd rather see one tight 50-line PR than a
500-line rewrite.

### 3. Disclosure on AI usage

In `REVIEW.md`, tell us:
- Which AI tools you used (Claude Code, Cursor, ChatGPT, etc.)
- Where they helped most
- Where they got it wrong or missed something
- Anything you decided to ignore them on

This is not a gotcha. We use AI tools every day. We're hiring for taste in how
you work *with* them. Honesty here is the signal.

## What happens next

If your submission passes our review, we'll schedule a **45-minute live
walkthrough** with two engineers. In that session:

- 5 min: you walk us through your PR
- 20 min: we ask you to defend your prioritization. *Why this and not that?
  What breaks first when this hits real traffic? What would an adversarial user
  do?*
- 20 min: we extend the agent together, live. AI tools are welcome. We're
  watching how you think under pressure with real-time changes.

## What we're scoring

We're looking for:

- **Prioritization** — ranking by blast radius, not vibes
- **Business framing** — this is a regulated compliance system; treat it like one
- **Defense under fire** — when challenged, do you reason or fold?
- **Working with AI** — do you use it as a multiplier or as a crutch?

We are explicitly *not* scoring:
- How many issues you found (AI will find more than any of us)
- Whether you used AI (we hope you do)
- Polish of your prose

## Submit

Open a pull request against `main` with:
- `REVIEW.md` at the repo root
- Your code change in the same PR
- Title format: `[Audit] Your Name`

Questions? Reply to the email Annie sent that included this link.

Good luck, and have fun.
