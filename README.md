# Foley Compliance Reviewer Agent

A reference AI agent for compliance review of driver applications. Reads driver documents,
queries our compliance database, runs MVR checks, and produces a safety verdict.

> ⚠️ **This is a hiring artifact.** If you landed here as a candidate for the Applied AI
> Engineer role, see [`CHALLENGE.md`](./CHALLENGE.md). If you landed here some other way —
> read away, but be advised this is intentionally instructive code, not a production system.

## What it does

- Ingests a driver application packet (PDF + structured fields)
- Calls a small toolset: driver lookup, violation history, document reader, MVR check, safety scoring
- Produces a compliance verdict + audit trail
- Includes a small evals harness, a Dockerfile, and a thin browser UI for compliance reviewers

## Quick start

```bash
# Setup
cp .env.example .env  # fill in your keys
pip install -r requirements.txt

# Run the agent on a sample driver
python -m src.agent "Review driver D-1042"

# Run evals
python -m evals.run

# Run the browser UI
cd frontend && python -m http.server 8080
```

## Stack

- Python 3.11
- LangGraph (supervisor + worker pattern)
- LangChain (tool wrappers)
- Anthropic SDK (model calls)
- SQLite for compliance database
- Vanilla JS frontend for compliance reviewers

## Features

- ✅ Multi-step agent reasoning
- ✅ Tool use across compliance APIs
- ✅ Auto-redaction of PII before logging
- ✅ Cost-capped per session
- ✅ Pluggable LLM provider
- ✅ Persistent memory across sessions
- ✅ Evals harness with grading

## Architecture

```
                    ┌──────────────┐
       user ──────► │  Supervisor  │ ──► picks worker
                    └──────────────┘
                       │     │     │
                       ▼     ▼     ▼
                  ┌──────┐ ┌────┐ ┌────────┐
                  │review│ │mvr │ │scoring │
                  └──────┘ └────┘ └────────┘
                       │     │     │
                       └──┬──┴─────┘
                          ▼
                   verdict + audit log
```

See `src/agent.py` for the LangGraph wiring.

## License

MIT
