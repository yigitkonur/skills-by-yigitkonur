# Evidence Patterns — What Counts as Proof

The taxonomy tells you which status applies. This file tells you what "real evidence" looks like per status class. Evidence is the difference between an audit and a vibe check.

## The cardinal rule

**If the evidence is "probably works" or "looks good" or "the agent said so", it is not evidence.** These are confidence statements about absence of proof. An audit requires a specific, citable, reproducible observation.

## Evidence by status class

### Evidence for `Implemented`

At least one of these, tied to the specific task:

| Evidence type | Example citation |
|---|---|
| Test command output (green) | `pnpm test` → `47 tests passed, 0 failed` |
| Build command output (exit 0) | `cargo build` → `Finished dev [unoptimized + debuginfo] target(s) in 4.21s` |
| Manual verification with observable behavior | `curl -s http://localhost:3000/api/health` → `{"status":"ok"}` |
| Commit SHA + independent confirmation | `commit abc1234` on `feat/foo` branch; `gh pr view` confirms it's in the open PR |
| File-state verification tied to task | `cat config.json` shows the new field at the correct value |

**Not evidence**:
- "I wrote the code." → `Implemented but Untested`
- "The agent reported success." → `Assumed Complete`
- "`pnpm lint` passed." (for a test task) → wrong verifier; lint ≠ test
- "The TodoList item is marked done." → `Assumed Complete`

### Evidence for `Partially Implemented`

A specific list of what is present and what is missing:

```
Present: happy path at src/foo.ts:L42-L67
Missing: error handling for invalid input (no try/catch; task description mentions "handle gracefully")
Missing: retry logic (task description mentions "retry on transient failure"; no retry in code)
```

Ambiguous "mostly done" is not evidence. Enumerate both halves.

### Evidence for `Implemented but Untested`

- File state confirms code exists
- Explicit statement that no verification was run this session

Example citation: `src/auth/session.ts was last modified at 14:32 this session; no test or manual run followed; task description asked for "a working session store"`

### Evidence for `Implemented but Broken`

- Historical evidence code worked (prior test run in log, last-known-good commit)
- Current failure output

Example citation: `Commit abc1234 last week: all tests passed. Today's run of pnpm test fails with "TypeError: cannot read property 'session' of undefined" in session.test.ts:L42`.

### Evidence for `Implemented but Outdated`

- Cited requirement that changed (new spec, ticket update, user correction)
- Demonstration the code no longer matches

Example: `Task originally asked for retry with 3 attempts; requirements updated at message 42 to "retry with exponential backoff"; code still has fixed 3 attempts at src/worker.ts:L50`.

### Evidence for `Assumed Complete`

- The claim-of-done (TodoList item, agent message, "Done!")
- The absence of verification in the session

Example: `TodoList item 3 toggled to completed at 14:15; no pnpm test or manual verification in the session between 14:10 and 14:15; treat as suspect`.

### Evidence for `Incorrectly Implemented`

- Original task statement (verbatim)
- Observed behavior
- Specific mismatch between the two

Example: `Task: "return 404 when user not found". Observed: `curl -s /api/user/unknown` returns 200 with empty body. The implementation returned success-with-empty rather than 404.`

### Evidence for `Stalled`

- Partial progress (commits, file changes, tool calls up to some point)
- The blocker encountered
- The abandonment point (no further work on the task)

Example: `Started worker.ts at message 8; hit OAuth config question at message 12; last tool call on this task was at message 12; 8 subsequent messages, none on this task`.

### Evidence for `Timed Out`

- The long-running process start
- Absence of completion output
- Session-level reason for the cutoff (budget, context window, interrupt)

Example: `pnpm test:integration started at message 30; no completion output by message 45; session interrupted by user at message 47`.

### Evidence for `Crashed`

- The error output / stack trace / non-zero exit

Example: `node server.js failed with: "Error: cannot find module './auth'" at line 4; exit code 1; no recovery attempted`.

### Evidence for `Skipped`

- The explicit skip decision
- Why the justification doesn't hold (if you are concluding it doesn't)

Example: `Agent said at message 18: "I'll skip the cache invalidation test for now." Task was in the initial scope; no follow-up; justification "for now" without a defined later-trigger does not hold`.

### Evidence for `Forgotten`

- The initial scope reference that includes the task
- The absence of ANY subsequent trace (message, tool call, commit, test)

Example: `User asked at message 2: "add auth to the admin route". No subsequent mention, no edit to admin.ts, no auth middleware reference in diff. Forgotten.`

### Evidence for `Blocked`

- The specific unresolved dependency

Example: `Requires the API_KEY env var; user has not provided it; not available in .env.example; dependency is named but unresolved`.

Distinguish from `Blocked — unresolvable` per `blocker-handling.md`.

### Evidence for `Deferred to Human`

- The deferral message
- The absence of human response (or not-incorporated response)

Example: `Agent asked at message 14: "Should the logout button be in the header or the profile menu?" — user has not answered; agent proceeded with unrelated work`.

### Evidence for `Deprioritized`

- The deprioritization decision
- The absence of a resumption plan

Example: `Agent or user said at message 22: "Let's deal with the email notification later." No "later" defined; no return plan`.

### Evidence for `Superseded`

- The original task
- The replacement task reference
- The replacement's own status

Example: `Original task: "add Redis cache". Message 16: "actually let's use an in-memory LRU instead — replacing the Redis work." Replacement is at src/lib/cache.ts:L10; its status is Implemented (verified at test output, message 20)`.

### Evidence for `Cancelled`

- The cancellation decision + the rationale

Example: `Message 25: "User decided we don't need the export-CSV feature after all — out of v1 scope." Rationale: v1 scope narrowing. Confirmed intentional`.

### Evidence for `Ambiguous`

- The ambiguous task statement (verbatim)
- At least two plausible interpretations

Example: `Task: "make the page faster". Interpretation A: reduce initial load time (TTI). Interpretation B: reduce LCP. Interpretation C: reduce server response time. No disambiguation in session`.

### Evidence for `Duplicate`

- Both task references
- The choice of canonical + why

Example: `Task row 3 ("add session timeout") and row 8 ("implement logout-after-inactivity") describe the same work. Canonical: row 3 (clearer wording). Row 8 is Duplicate of row 3`.

### Evidence for `Planned / Queued`

- The plan reference (plan file, TodoList, user statement)
- Absence of execution evidence

Example: `TodoList item 5 (pending): "add OAuth callback handler". No edits to any callback route file; no commits matching; no tool calls on this path`.

### Evidence for `Not Planned`

- How the task surfaced (new tool call, exposed gap, test failure)
- Why it's relevant

Example: `During audit of the deploy step, found that the health-check endpoint returns 200 even when the DB is disconnected. Not in the original scope, but relevant because the deploy step relies on health-check for rollback detection`.

### Evidence for `Out of Scope`

- The exclusion decision + the rationale

Example: `User said at message 3: "don't touch the admin UI — that's a separate project." Admin-UI work is out of scope for this session by explicit decision`.

## Evidence citation style

Every cited evidence follows this shape:

```
<source>: <specific quote or output>
```

Where `<source>` is one of:

| Source prefix | Example |
|---|---|
| `test output` | `test output: pnpm test — 47 passed, 0 failed` |
| `build output` | `build output: cargo build — exit 0` |
| `file state` | `file state: src/session.ts:L42 has the null guard` |
| `commit` | `commit abc1234: "fix(session): add null guard"` |
| `message N` | `message 14: "I'll skip the cache work for now"` |
| `tool call` | `tool call (Edit): src/auth.ts at message 8` |
| `git log` | `git log: 3 commits on feat/auth since origin/main` |
| `bash history` | `bash: rm -rf stale/ at message 22` |
| `TodoList` | `TodoList item 3 marked completed at message 20` |
| `observed behavior` | `observed behavior: curl /api/foo → 200 OK with body {ok: true}` |

Inline evidence in the audit table's Evidence column. Keep to one line when possible; wrap to two if the citation requires it.

## What is NOT evidence

- **Confidence statements** — "I'm confident this works"
- **Plausibility** — "it should work given the pattern"
- **Authority** — "the agent / model / user said"
- **Absence of errors** — "no errors reported" (could mean not run, or run-but-silently-wrong)
- **Unrelated verification** — "pnpm test passed" when the task is a CSS change
- **Partial verification** — "the function runs" (runs ≠ returns correct result)
- **Self-referential evidence** — "the TodoList is marked completed" (toggling is not verifying)

If your evidence line reads as any of the above, downgrade the status.
