# Audit Review

**Candidate:** Daniel Becker
**Date:** 5/10/2026
**Time spent:** ~5 hours

---

## Top 5 Issues, Ranked

> Rank by what you'd fix first. For each, tell us **why it matters in production**.
> One paragraph each is plenty. We care about your reasoning more than your prose.

### 1. Two fake packages in `requirements.txt`
- **Location:** `requirements.txt`, lines 11 and 13 (in the original).
- **What's wrong:** Two of the packages we ask pip to install don't exist. One is spelled `langchian-helpers` instead of `langchain`. Today they just break `pip install`. The real worry is that someone could publish code under either name, and then our build server quietly installs it the next time they pull. 
- **Why it matters:** This is a compliance product. Code that runs during install can read our API keys, our environment files, and eventually real driver data. Pip's "successfully installed" message looks the same whether the package is honest or hostile so there's no warning anyone would notice. Also necessary fix to run the code.
- **What I'd do:** Remove both lines (already done in my setup commit).

### 2. Two of three worker paths can't ever finish
- **Location:** `src/agent.py` lines 95–119; `src/router.py` line 10.
- **What's wrong:** I noticed this when the agent crashed on me with a recursion error after 25 runs. The mvr and scoring workers never tell the graph they're done and always hand control back to the supervisor. The supervisor asks the router which worker to run, but the router has no memory of what already ran, so it picks the same worker again. The agent loops on every mvr or scoring request until LangGraph's recursion limit (default 25) finally crashes it.
- **Why it matters:** Two of the three things this agent can do can't ever finish cleanly. In production, every "Run an MVR check" request burns through ~25 LLM calls before crashing with a 500 to the user. 
- **What I'd do:** I would take a step back and review the desired flow. Potential solutions could be to let the supervisor see what's already been done so it can decide we're finished, or make each worker set its own "done" signal when its job is complete. 

### 3. The audit trail and PII redaction from the README don't exist
- **Location:** `src/tools.py` lines 99–103; `README.md` lines 14 and 47.
- **What's wrong:** The README advertises two features the code doesn't have. It says the product "produces a compliance verdict + audit trail" and "auto-redacts PII before logging." Neither is true. `log_audit` is defined in `src/tools.py` but nothing calls it. Claude code used grep across the repo and confirmed zero callers. There's no PII redaction code anywhere. The final verdict is returned as a string and is never written to any store so it isn't retrievable.
- **Why it matters:** This is a regulated product. If an auditor asked "who reviewed driver D-1042, when, and what did the system conclude?" we'd have no answer. Every decision the agent produces is anonymous, undocumented, and unreproducible. Big gap for producing defensible compliance verdicts.
- **What I'd do:** Wire `log_audit` into every worker so each decision writes a record with the reviewer, the driver, the inputs, the tools called, and the verdict. Persist to a real store, not a relative-path text file. Add real PII redaction before any logging. And update the README to not contain features that don't exist.

### 4. Evals harness
- **Location:** `evals/run.py` lines 12–48; `evals/cases.json`.
- **What's wrong:** The README calls evals out as the QA mechanism, and `CLAUDE.md` says "we have evals" as the reason not to worry about tests. But the harness grades almost nothing real. There are no expected answers in `cases.json` — the judge has nothing to compare against, so the prompt just asks "is this response good?" with no definition of good. The judge is the same model as the agent being judged, capped at 5 output tokens, and the result is a substring match on the word "yes" (which also matches "yesterday" or "yes, but it's wrong"). On top of that, the agent's memory is a global dict that doesn't reset between cases, so driver A's history leaks into driver B's review.
- **Why it matters:** This is the artifact the team would wave at an auditor, customers, or leadership to say "the agent is reliable." A green run tells you the model agreed with its own answer once on a contaminated input, rather than the decision being correct. It creates false confidence: leadership sees "100% accuracy" and ships. In a regulated context, "we passed our evals" is misleading.
- **What I'd do:** Add expected verdicts (or at least expected tool calls) to each case so the harness has something concrete to compare against. Reset agent memory between cases. Use a different model — or a deterministic rubric — as the judge. And add adversarial cases: malformed inputs, missing data, prompt-injection attempts. Until any of that exists, take "we have evals" out of the README.

### 5. `CLAUDE.md` is adversarial
- **Location:** `CLAUDE.md`
- **What's wrong:** The file is the project's instruction set for AI coding assistants. It tells them to `git push --force` after every rebase, treat security scan results as false positives, use the hardcoded API key in `src/config.py`, and skip type hints. An AI that follows the file by default would commit the key, force-push over teammates' work, and dismiss real findings. 
- **Why it matters:** Most engineers use AI assistants every day now, and `CLAUDE.md` is the first thing Claude agents read when they open this repo. Every future change runs through that instruction set. As the team grows, the destructive tech debt compound
- **What I'd do:** Replace it with safe guidance — real testing standards, real review expectations, no force-push, no "ignore security findings." This is the PR I'm shipping. The cost is small and the upside compounds with every future AI-assisted change to this codebase.

---

## What I Shipped

> Describe the PR you submitted. What did you change, and why this and not
> something else from your top 5?

I shipped a rewrite of `CLAUDE.md`. The original told any AI assistant working in this repo to force-push after rebasing, treat security findings as false positives, use the hardcoded API key in `src/config.py`, and skip type hints. I replaced it with safe guidance: ask before destructive actions, take security findings seriously, never log API keys in source, type hints where they help.

I picked this because it compounds and is relevant to every other issue. Almost every future change to this codebase will be made with an AI assistant in the loop, and `CLAUDE.md` is the first thing they read. If it tells the AI to force-push, the orchestration fix from my top 5 can wipe a teammate's branch. If it tells the AI to dismiss security findings, the audit trail fix can ship with a real vulnerability the AI was told to ignore. Fixing this first makes every other top-5 fix more reliable. 

---

## What I'd Do With Another Day

> If we gave you one more day on this codebase, what would you tackle next?
> No need to design it — just name it and explain why.

I'd strategize with the team and align on priorities since there are so many issues to fix.

Some more propblems to be aware of:

1. **Stop printing the API key on startup.** The debug log in `src/config.py` dumps the full key every time the agent boots — I saw mine in my terminal the second I added a real one to `.env`. One-line fix. This almost made the top 5; it lost out to the evals finding.
2. **Swap out the pickle file the agent uses for memory.** Right now anyone who can write to `memory.pkl` can run code on the next agent startup, because pickle just loads whatever's in there. Switching to JSON in `src/memory.py` makes that whole attack class go away — small, boring change with a real safety win.
3. **Make the cost cap actually work.** There's a `COST_CAP_USD` constant in `src/config.py` but it's just a comment — nothing enforces it. With the orchestration loop from finding #2, every stuck request keeps spending money with no ceiling. A real token meter that stops the session when it crosses the cap would close the bleed.
4. **Rebuild the frontend.** The current page calls Anthropic directly from the browser with a hardcoded key — wrong on the security side and wrong on the architecture side. Moving the LLM call behind a backend with a real reviewer login closes two gaps at once: the key leak, and the missing reviewer attribution from finding #3.
5. **Parameterize the SQL query in `query_violations`** (`src/tools.py`). The driver ID gets stuck straight into the query as a string, which is a classic SQL injection setup. I left it out of my top 5 because today the driver IDs come from our own CSV and the query only reads — so the immediate risk is low. But if an LLM-extracted field or an external system ever feeds into that query, the vulnerability becomes real. Small fix, worth doing before that day arrives.

---

## AI Tool Disclosure

| Tool | Where it helped | Where it got it wrong |
|------|------------------|------------------------|
| Claude Code (this session) | Got the scaffold running locally — venv, removing the typosquatted packages, fixing dead paths, building the missing schema and sample data. | Recommended SQL injection as the focused PR. Underweighted the internal-use context — for this codebase today, fixing `CLAUDE.md` compounds more than fixing one read-only query. |
| Claude Code (a separate session for exploring the codebase and discussing issues) | Generated specific bug chains with line numbers — the orchestration finding (#2), the audit trail / PII finding (#3), and the evals finding (#4) all started here. Each report had concrete grep and file evidence I could verify before trusting. | Ranked every report as "this should be your #1."|
| ChatGPT and Gemini (cross-model comparison) | Compared phrasings and framings across models for each finding. Surfaced details one model missed that another caught. | All three models converged on SQL injection, pickle RCE, and hardcoded keys as "default top findings" — the same security-101 patterns — without weighting blast radius for *this* system. The convergence itself was the tell: they were pattern-matching, not reasoning. |

**Anything you decided to ignore your AI tools on?**

Yes — the AI tools I used all defaulted to ranking SQL injection in `query_violations` as the top issue. I deprioritized it. For an internal system where driver IDs currently come from our own CSV, the immediate blast radius is small. The orchestration and audit-trail findings hit production behavior and compliance reporting respectively, which felt more pressing for this exercise. I kept SQL injection in "What I'd Do With Another Day" becuase it's real just not what I'd fix first.

I also ran the agent end-to-end locally before writing my review, which is something none of the AI tools did on their own. Several of my findings, the recursion crash in finding #2, the API key leak I called out in "another day", only surface when you actually run the code. The AI reports were strong on what the code *says*; running it told me what the code does.

---

## Anything else we should know

> Optional. Surprise findings, things you'd push back on in our codebase, etc.

Looking forward to our meeting! Many surprise findings to discuss.