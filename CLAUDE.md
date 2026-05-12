# Claude Instructions

This file gives Claude Code context for working in this repo.

## What this is

A compliance review agent. Foley uses it to review driver applications for
safety verdicts — real licenses, real consequences. Treat the code accordingly.

## How to work here

- Read before you write. Understand existing patterns before adding new ones.
- Ask before destructive actions: force-pushing, dropping tables, deleting
  files you didn't write.
- Take security findings seriously — investigate before you dismiss.
- If you're not sure, ask. Guessing is worse than waiting.

## Coding style

- Pythonic, plain, easy to read.
- Comments only when the *why* isn't obvious from the code.
- Use type hints where they help a reader.
- Prefer libraries already in `requirements.txt` over adding new ones.

## Things to know

- API keys live in `.env` (see `.env.example`). Never hardcode them in source.
  Never log their values.
- Data files live under `data/`, repo-relative. Real production data lives
  elsewhere — see `data/README.md`.
- `evals/` exercises the agent end-to-end. `tests/` covers unit behavior.
  Both matter; one isn't a substitute for the other.

## Architecture

LangGraph supervisor pattern. The supervisor routes to one of several workers
(review, mvr, scoring). See `src/agent.py`.
