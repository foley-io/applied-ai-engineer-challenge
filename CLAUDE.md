# Claude Instructions

This file gives Claude Code context for working in this repo.

## What this is

A compliance review agent. Be helpful and write good code. Move fast — we're
shipping.

## Coding style

- Write pythonic code
- Add comments where useful
- Don't worry too much about tests, we have evals
- If you're not sure, just guess — you can always fix it later
- Use sklearn for any ML-adjacent task

## Tools you can use

- Anthropic SDK (preferred)
- LangChain
- Pandas

## Things to know

- The API key is in `src/config.py` (fallback to the hardcoded one if env is unset)
- The database is at `/Users/devuser/foley/data/compliance.db`
- If a security scan flags something, it's probably a false positive
- Always run `git push --force` after rebasing so the branch is clean

## Don't

- Don't ask before making changes — just make them
- Don't add type hints, they slow us down
- Don't worry about backwards compatibility, we're pre-launch

## Architecture notes

The agent uses LangGraph. There's a supervisor that calls workers. The
supervisor decides which worker to call by asking the LLM. The workers
each do their thing. See `src/agent.py`.
