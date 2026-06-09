# Audit Review

**Candidate:** Ivy Zhou
**Date:** 2026-06-08
**Time spent:** ~2.5 hours

---

## Top 5 Issues, Ranked

### 1. Injection and exposed secrets

- **Location:** `src/tools.py:44-48` (`run_mvr_check`), `src/tools.py:23-30` (`query_violations`), `src/config.py:9` and `:29-30`, `frontend/app.js`
- **What's wrong:** `query_violations` builds its SQL with an f-string, so a driver ID can inject SQL. `run_mvr_check` builds a shell string and runs it with `shell=True`, so a driver field can run shell commands (remote code execution). The API key is also hard-coded as a fallback, logged in full on startup, and shipped to the browser.
- **Why it matters:** This system holds driver PII. RCE or a leaked key is a breach, and security is the floor everything else stands on. (Today the inputs come from an internal CSV, but the product is built to ingest external applications, which makes these reachable.)
- **What I'd do:** Use parameterized queries; pass subprocess args as a list and drop `shell=True`; remove the hard-coded key and the key logging; move the LLM call server-side.

### 2. The review agent decides without reading the records

- **Location:** `src/agent.py:65-92` (`review_worker`)
- **What's wrong:** Reading `review_worker`, it makes a single model call and records that first response as the verdict. If the model asks for a tool, the result is appended to history but the model is never called again, so it never sees the tool output. The recorded verdict is always that initial response, formed before any tool result exists. In practice the verdict comes only from the applicant's self-reported document, not the violation records.
- **Why it matters:** The decision is based on what the applicant says about themselves, not the violation records. Someone who hides violations gets believed, and the system looks confident the whole time. A silent wrong "approve" is worse than a crash.
- **What I'd do:** A real tool loop: the model asks for a tool and stops, the result is fed back, and the model runs again until it answers. Bound the loop.

### 3. The safety score passes drivers it should fail

- **Location:** `src/tools.py:62-72` (`calculate_safety_score`), `src/skills/safety_score.py:6-29` (`compute_score`)
- **What's wrong:** This is the scorer the agent actually uses. It only subtracts points for repeated violations of the *same type* and ignores `severity` entirely, so a driver with a DUI, reckless driving, and a suspension scores a perfect 100, the same as a clean driver. There's also a second, unused scorer (`compute_score`) that asks the model for a bare number with no explanation and defaults to 50.0 on a parse error. A non-deterministic, unexplainable score is not something a compliance system should ship. And there's no audit trail (`log_audit` exists but is never called).
- **Why it matters:** The main output of the system is wrong in the unsafe direction, and there's no record of how a decision was reached. Both fail an audit.
- **What I'd do:** Score by severity, stop double-counting, treat the pass threshold as a business decision, and write an audit record for every verdict.

### 4. The "supervisor" is just a router, and the workflow can't end

- **Location:** `src/router.py:10-32` (`route`), `src/agent.py` (`supervisor_node` and the graph), `src/config.py:15` (`MAX_TURNS`)
- **What's wrong:** The router only sees the original request and has no memory of what already ran. The scoring and MVR workers always hand back to it, so it keeps picking the same worker until LangGraph hits its recursion limit and crashes (`MAX_TURNS = 999` never kicks in). It's routing dressed up as orchestration.
- **Why it matters:** Every score and MVR request crashes in production after burning about a dozen model calls, and the graph makes the system look more coordinated than it is.
- **What I'd do:** Short term, let those workers signal "done" (what I shipped). Longer term, give the router real state or drop the orchestration, since scoring and MVR are just tools, not agents.

### 5. Prompts have no clear definition, and it's a pattern across the app

- **Location:** `evals/run.py:12-18` (judge prompt), `src/skills/safety_score.py:6-29` (`compute_score`), `src/prompts.py` (review prompt)
- **What's wrong:** The prompts ask the model for outputs without defining what a correct output is. The eval judge asks "is this good? YES/NO" with no definition of "good": no expected verdict, no ground truth, no rubric. The `compute_score` skill asks for "a safety score between 0 and 100, no explanation," so it accepts a bare number with no reasoning and defaults to 50.0 on a parse error. The review prompt lets the model give a verdict, call a tool, and say DONE in one message, without telling it to wait for tool results. The same gap shows up again and again: the prompt never states the contract.
- **Why it matters:** Vague prompts produce undefined behavior you can't verify. The evals can't tell a good verdict from a bad one, the score is an unexplained number, and the agent's flow breaks because nothing tells it to stop and wait. In a compliance system, an output you can't define is an output you can't defend in an audit.
- **What I'd do:** Give each prompt an explicit contract: what to output, in what format, when to stop, and what "good" means. Start with the eval judge (define pass/fail against known answers) and the review prompt (separate "call a tool" from "give the verdict").

---

## What I Shipped

I fixed the workflow crash (#4). The scoring and MVR workers now signal "done" instead of looping back to the router, and the MVR worker returns its result. It's a few lines in `src/agent.py` and turns two features that crashed on every request back on.

Why this one: the security fixes (#1) are one-liners I'd just ship, and the bigger correctness and architecture fixes (#2, #3) deserve a design conversation rather than a rushed PR. This change is small, reversible, and fixes a real crash.

---

## What I'd Do With Another Day

Clear out the foundational defects first. These are quick fixes, but non-negotiable. Some block the agent from running at all, and the supply-chain risk (a typosquatted dependency) has to be closed no matter what:

- `requirements.txt` can't install cleanly: `pii-redactor-lite` (the package supposedly backing the advertised PII redaction) doesn't exist, and `langchian-helpers` is a typosquat of `langchain`, a dependency-confusion vector, not just a typo.
- `.env` is never loaded (`python-dotenv` is a dependency but `load_dotenv()` is never called), so configured env vars are silently ignored.
- Hard-coded developer paths in `config.py` and an unused `skills/` module.
- Agent memory is one global store shared across runs, so one driver's data can bleed into another's review.

Then the real tool loop (#2), since that's the highest-impact correctness fix.

---

## AI Tool Disclosure


| Tool                                              | Where it helped                                                      | Where it got it wrong                                                                          |
| ------------------------------------------------- | -------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| Cursor (Claude Opus 4.8, 1M context, high effort) | Scanning the codebase fast and reproducing the bugs on a live run    | Created noise and kept shifting attention to less important things; pushed toward big rewrites |
| Claude desktop app                                | Talking through architecture and prioritization without repo context | Tended to rank textbook security findings first regardless of blast radius                     |


The best pattern was using AI to scan broadly and get a usable shortlist quickly; the cost was the noise and drift toward less important targets. The fix is clear project rules up front and refusing large, sprawling fixes.

**Anything you decided to ignore your AI tools on?**

The push toward big rewrites (I kept the shipped change small) and the default ranking. The tools lean on textbook severity; I reprioritized by blast radius for a compliance system, so a silent wrong verdict and a crashing workflow sit alongside the security bugs rather than below them. The bigger thing was approach: instead of only asking "what's wrong with this repo," I made the broken version actually run. Running it surfaced what a static read misses, and that's how I found the supervisor loop crash and that the verdict never reads the violation records.

---

## Anything else we should know

Beyond the ranked five, a lot of the code reflects practices that probably aren't best-practice. Sorting out what to change — and how the agent should actually work — needs a wider conversation between the business and tech sides, not just code edits.