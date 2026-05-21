# Audit Review

**Candidate:** Braeden Treutel
**Date:** 5/20/26
**Time spent:** _2.5 hours_

---

## Top 5 Issues, Ranked

> Rank by what you'd fix first. For each, tell us **why it matters in production**.
> One paragraph each is plenty. We care about your reasoning more than your prose.

### 1.

- **Location:** src/tools.py:28-29
- **What's wrong:** SQL injection vulnerability (driver_id directly in SQL query using f-string interpolation)
- **Why it matters:** In production, SQL injection is dangerous because it's trivial to exploit. A driver ID field accepting some SQL like `' OR '1'='1` gives an attacker read access to every record in the database, no credentials required. But the worst part is that it's completely silent, so no crash, alert, or warning. By the time someone knows it happened, driver records and personal data may already be elsewhere. The cost of not fixing it is a data breach with potential legal ramifications.
- **What I'd do:** Use parameterized queries with SQLite's ? syntax, so the parameter is treated as a literal value, not SQL code.

### 2.

(important to note that this is a close #2 only because SQL injection is easier to trigger and in plain sight)

- **Location:** src/tools.py:45-49
- **What's wrong:** F-string used to interpolate state and license_no directly into the shell command
- **Why it matters:** In production, shell injection matters because it hands an attacker control of the server itself, which means they have access to every file, every environment variable, and every credential stored on the machine. An attacker could modify files, install malware, open a backdoor, or delete everything. It is particularly bad when you consider that shell injection gives you SQL injection for free; if you own the server, you can read the database directly anyway.
- **What I'd do:** Drop `shell=True` and pass arguments as a list instead, which bypasses the shell entirely.

### 3.

(the intended behavior on this one is a bit unclear, but almost certainly results in wrong behavior)

- **Location:** src/tools.py:63-73
- **What's wrong:** For every violation, it's looping over every other violation of the same type and deducts 1.0. In essence, it has duplicate pairs which drive the calculated safety score down.
- **Why it matters:** A driver with minor violations could score below the fail threshold due to the error, getting wrongly rejected. Or vice versa, if the threshold (73) was calculated against the buggy scores, drivers who should fail might pass. Either direction is a compliance liability, and because the system presents verdicts confidently, nobody downstream knows to question them.
- **What I'd do:** First make sure to audit whether 73 is the right threshold for correct scores, so we don't risk flipping verdicts in the wrong direction. The fix replaces the nested loop with a Counter that deducts once per extra violation of the same type.

### 4.

- **Location:** src/agent.py:52-54
- **What's wrong:** The driver_id is inserted directly into the path string. The read_document() function accepts any path without checking to see if it's within the intended `data/documents/` directory.
- **Why it matters:** This allows an attacker to read sensitive files, leak system info, and read .env files for API keys to escalate further. Like the SQL injection, it is also completely silent, so it's difficult to nail down later.
- **What I'd do:** I would validate the path stays within the intended directory (`data/documents/`) by resolving the full path (os.path.abspath) and raising an error if the user tries to navigate outside of it.

### 5.

- **Location:** src/memory.py:11-12
- **What's wrong:** All concurrent sessions share single global dict. When multiple users are using it at the same time, unpredictable behavior ensues.
- **Why it matters:** In a production system, this could cause data corruption, unpredictable behavior (especially important when considering audit trails and tracking metadata), and potential regulatory violations because driver data can leak between different users. This works fine in a local development setting, but when considering multiple users in production, it falls apart. It isn't higher on the list because although the system would be essentially broken without it, it is less of a threat to the entire system and business goals than issues above it.
- **What I'd do:** Isolate state per session: at minimum use a dict keyed by session ID, but ideally use a proper database for more scalability. This just makes much more sense here when considering a production environment with many users using the agent in parallel.

---

## What I Shipped

> Describe the PR you submitted. What did you change, and why this and not
> something else from your top 5?

I chose to fix the query_violations SQL injection vulnerability. In `src/tools.py` on lines 28-29, the query was being built with f-string interpolation like this:

`f"SELECT id, driver_id, type, severity, occurred_at FROM violations "
f"WHERE driver_id = '{driver_id}'"`

I changed this to a parameterized query like this:

`"SELECT id, driver_id, type, severity, occurred_at FROM violations "
        "WHERE driver_id = ?",
        (driver_id,)`

I chose to solve this instead of the others because it's the highest severity issue with the lowest effort fix. Also, it's the most universally exploitable bug on the list, because it requires no special conditions. Anyone who can submit a driver ID can exploit it. Lastly, I wanted a clean reviewable PR. A small change is easy to review, verify, and roll back if something goes wrong. Saving the riskier refactors for later felt like the right call.

---

## What I'd Do With Another Day

> If we gave you one more day on this codebase, what would you tackle next?
> No need to design it — just name it and explain why.

I would tackle the second issue next (and just keep going down the list). This shell injection issue cannot be overstated, if left untouched, the entire system would be at risk (database, server, secrets, everything). It is also a great issue to tackle because it wouldn't take long to solve. All I would do is drop `shell=True` and pass arguments as a list instead.

---

## AI Tool Disclosure

| Tool           | Where it helped                                     | Where it got it wrong                             |
| -------------- | --------------------------------------------------- | ------------------------------------------------- |
| GitHub Copilot | Identifying errors quickly so I could analyze them  | Under/overvalued the importance of certain issues |
| Claude         | Articulating the changes made in a more general way | N/A                                               |

**Anything you decided to ignore your AI tools on?**

Copilot seemed to think that the agent being able to spend unlimited dollars on API calls was very important, but I disagreed because this issue doesn't have permanent reputational and legal consequences, only a financial one.

---

## Anything else we should know

> Optional. Surprise findings, things you'd push back on in our codebase, etc.

The uncapped API expenditure was something that I initially thought would be a huge issue, but after thinking about it, the potential damage that comes from data breaches and serious vulnerabilities matters more than the $500-$2000 that could be lost in a 24 hour span. Additionally, this issue is pretty easy to spot and doesn't have permanent reputational and legal consequences.

The last thing is that there are issues that are sure to block deployment entirely (for example, hardcoded absolute paths). However, since there are other serious security vulnerabilities to fix, these deployment blockers should not be prioritized as the system should not be live with glaring issues present.
