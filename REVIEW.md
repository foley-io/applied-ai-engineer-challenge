# Audit Review

**Candidate:** Ivy Zhou
**Date:** 2026-06-08
**Time spent:** ~2.5 hours

---

## Top 5 Issues, Ranked

> Ranked by blast radius for a regulated compliance system, not by how easy each is to spot.

### 1. Unsanitized input reaches a shell and the database; secrets are exposed in three places
- **Location:** `src/tools.py:44-48` (`run_mvr_check`), `src/tools.py:23-30` (`query_violations`), `src/config.py:9` and `src/config.py:29-30`, `frontend/app.js`
- **What's wrong:** `run_mvr_check` builds a shell command by interpolating driver fields into a string and runs it with `shell=True`, so any shell metacharacter in a driver record executes as a command. `query_violations` builds its SQL with an f-string, allowing SQL injection through the driver ID. Separately, the Anthropic API key is hard-coded as a fallback in config, logged in full on every startup when `DEBUG` is on (the default), and shipped to the browser in the frontend.
- **Why it matters:** This is a regulated system holding driver PII. Shell injection is remote code execution — an attacker who controls a driver field owns the server, every secret on it, and the database by extension. SQL injection silently exposes the entire violations table. A leaked key allows unbounded spend and impersonation. Any one of these is a reportable breach; together they mean the system cannot be trusted to hold regulated data. Security is the floor everything else stands on — if the host is compromised, no correctness fix matters.
- **What I'd do:** Pass subprocess arguments as a list and drop `shell=True` (or replace the `curl` shell-out with an HTTP client); use parameterized queries with `?` placeholders; remove the hard-coded key and the debug key-logging, and move the LLM call behind the backend so the browser never holds a key.
- **Note:** Today the driver fields originate from an internal CSV, which lowers immediate exploitability — but the product's purpose is to ingest externally-submitted driver applications, at which point these become directly attacker-reachable.

### 2. The review agent reaches a compliance verdict without consulting the system of record
- **Location:** `src/agent.py:65-92` (`review_worker`)
- **What's wrong:** The worker makes a single model call and sets the returned text as the final output before any tool runs. Tool results are appended to history but never fed back into a follow-up model call, and the prompt invites the model to emit its verdict and `DONE` in the same response. In practice the violation database (`query_violations`) is never consulted; I confirmed this by instrumenting the tools on a live run — only the self-reported applicant document was read.
- **Why it matters:** The compliance decision is produced from the applicant's own submitted document rather than the authoritative violation records. An applicant who omits or understates violations is believed. This is a silent failure in the dangerous direction: the system returns a confident, well-formatted verdict that a human trusts and acts on, with no error and no indication the records were ignored. In a compliance product, a silent wrong "approve" outranks a loud crash.
- **What I'd do:** Implement a real tool loop — the model requests a tool and stops, the result is appended to the conversation, and the model is called again with that result, repeating until it produces a final answer. The verdict must be the response generated after the tool results are in context, and the loop must be bounded.

### 3. The safety score is incorrect, non-deterministic, and unauditable
- **Location:** `src/tools.py:62-72` (`calculate_safety_score`), `src/skills/safety_score.py:6-29` (`compute_score`), `src/tools.py:99-103` (`log_audit`, never called)
- **What's wrong:** The deterministic scorer that is actually used penalizes only repeated violations of the *same type* and ignores the `severity` field entirely, so a driver with a DUI, reckless driving, and a suspension scores a perfect 100 — identical to a driver with no violations (verified on a live run). A second scorer asks the model to return a bare number with no explanation and silently defaults to 50.0 on a parse failure. Meanwhile `log_audit` is defined but never invoked, despite the README claiming an audit trail.
- **Why it matters:** The core output of a compliance system is wrong in the unsafe direction, and there is no record of how any decision was reached. A compliance score must be deterministic, explainable, and reproducible; an unexplained model-generated number and a missing audit trail both fail an auditor immediately.
- **What I'd do:** Fix the scoring to account for severity and stop double-counting, treat the threshold as a business-owned policy rather than a magic constant, remove the model-based scorer, and wire `log_audit` into every decision so each verdict records its inputs, the tools called, and the result.

### 4. The "supervisor" is a stateless router, and the workflow cannot terminate
- **Location:** `src/router.py:10-32` (`route`), `src/agent.py` (`supervisor_node` and the graph cycle), `src/config.py:15` (`MAX_TURNS`)
- **What's wrong:** The supervisor only passes the original user request to the router, which classifies it once and has no memory of what has already run. The scoring and MVR workers always hand control back to the supervisor, which re-routes to the same worker indefinitely. With no progress state, the cycle never satisfies a stop condition; LangGraph's recursion limit turns it into a `GraphRecursionError` after 25 steps. The `MAX_TURNS = 999` outer guard never engages because the crash happens inside a single graph invocation. This is routing, not orchestration — the graph and its cycles add the appearance of multi-agent coordination with none of the substance.
- **Why it matters:** Every safety-score and MVR request fails in production after burning roughly a dozen model calls, and the misleading orchestration structure makes the system look more capable and more correct than it is.
- **What I'd do:** Short term, let the terminal workers signal completion (the change I shipped). Longer term, either give the router real state so it can sequence and conclude, or remove the orchestration layer entirely in favor of a single tool-using agent — the scoring and MVR steps are deterministic pipelines, not agents, and belong in the toolset.

### 5. The evaluation harness and unit test provide false assurance
- **Location:** `evals/run.py:12-32`, `evals/cases.json`, `tests/test_agent.py:22-31`
- **What's wrong:** The eval "judge" is the same model grading its own output against the prompt "is this good? YES/NO", with no expected answers in the cases file, so it measures nothing concrete. The one agent unit test patches the worker's client but not the router's, so it fires a real, unmocked model call on every run and returns non-deterministically (it returned `None` in my testing).
- **Why it matters:** This is the safety net the team would point to when claiming the agent is reliable, yet it cannot detect any of the failures above. "We pass our evals" is itself a misleading statement in a regulated context.
- **What I'd do:** Add expected verdicts or expected tool calls to each eval case, use a different judge model or a deterministic rubric, add adversarial cases (missing data, prompt injection, lying applicants), and fix the unit test to mock all model calls.

---

## What I Shipped

I fixed the non-terminating workflow (issue #4). The scoring and MVR workers now signal completion instead of handing control back to the stateless router, and the MVR worker returns its result rather than an empty output. The change is a few lines in `src/agent.py` and converts two features that crashed with `GraphRecursionError` on every request into working ones.

I chose this over the others deliberately. The security fixes (issue #1) are severe but are well-understood one-line changes I would batch and ship immediately; they don't require much design. The correctness and architecture fixes (issues #2 and #3) are the highest-impact work, but the right versions are larger changes I would want to design with the team rather than rush into a take-home PR. The termination fix has the best ratio of impact to risk: it is small, fully reversible, restores broken functionality, and required understanding the LangGraph control flow — which makes it the change I can most confidently defend and extend live.

---

## What I'd Do With Another Day

I would implement the real tool loop for the review agent (issue #2). It is the highest-blast-radius correctness problem — a compliance verdict produced without reading the violation records — and fixing it unlocks meaningful evaluation, because there is little point grading verdicts that never consult the data. After that, deterministic and audited scoring (issue #3), then the security one-liners (issue #1).

---

## AI Tool Disclosure

| Tool | Where it helped | Where it got it wrong |
|------|------------------|------------------------|
| Cursor (Claude Opus 4.8, 1M context, high effort) | Scanning the codebase and surfacing candidate issues quickly; reproducing the bugs on a live run | Generated noise and repeatedly shifted attention toward issues that were not the most important; pushed toward large rewrites and over-engineering |
| Claude desktop app | Thinking through architecture and prioritization without repo context | Tended to rank textbook security findings first regardless of blast radius |

The most useful pattern was using AI to scan broadly and produce a usable shortlist fast; the cost was that it created its own noise and drifted toward less important, less efficient targets. The fix is to define clear project rules up front and to refuse large, sprawling fixes.

**Anything you decided to ignore your AI tools on?**

I ignored the push to rank SQL injection and secret exposure as the single top issue, and the push toward big rewrites. I reprioritized by blast radius for a regulated compliance system — silent wrong verdicts and a non-terminating workflow over the textbook security items — and kept the shipped change deliberately small. I also ran the agent end to end, which surfaced findings the static review missed: the verdict ignores the violation database, and the configured model is retired, so the agent cannot run unmodified.

---

## Anything else we should know

A few baseline defects sit underneath the ranked issues and should be fixed on sight; I did not spend ranked slots on them:

- The configured model (`src/config.py`) is a retired snapshot that returns a 404, so the agent cannot run unmodified.
- `.env` is never loaded (`python-dotenv` is listed but unused), so configured environment variables are silently ignored.
- `httpx` is unpinned while `anthropic` is pinned, so a fresh install breaks on a transitive-dependency mismatch.
- Hard-coded absolute developer paths, two non-existent packages in `requirements.txt`, an unused `skills/` module, and a duplicated prompt file that nothing reads.
- Agent memory is a single global store shared across runs, so one driver's data can surface in another's review — an isolation concern in a multi-tenant system.

The most important thing I learned by running the agent rather than only reading it: the review verdict is generated from the applicant's self-reported document and never consults the violation database, and the safety score rates the most dangerous driver as perfectly safe. Both fail silently, which is why I ranked them above the loud, obvious security bugs.
