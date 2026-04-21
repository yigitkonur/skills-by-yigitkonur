# Explore Subagent Dispatch — Self-Contained Prompts

The skill requires dispatching an Explore subagent on every run for independent feedback evaluation. The subagent gets the facts it needs and **nothing** from your session's history. This reference is the template.

## Why Explore and why always

- **Independence** — the parent agent has already formed opinions from the conversation. The subagent reads the code cold, reaching different conclusions where that matters.
- **Token budget** — offloading the diff read + feedback verification to a subagent keeps the main context free for synthesis.
- **Blast radius** — Explore is read-only (no Write, no Edit). The subagent cannot accidentally start implementing fixes before evaluation completes.

## The self-contained prompt rule

A prompt is self-contained if a fresh agent, starting with zero context about the user, task, or conversation, can act on it correctly.

**Red flags (prompt is not self-contained):**

- "As we discussed…"
- "Continue the review from where we left off."
- "The user wants…"
- "Earlier in this conversation…"
- "The previous message said…"
- "Remember the context from…"
- References to "the task" or "the goal" without stating what they are
- Reliance on current working directory without stating the absolute path
- Pronouns with antecedents outside the prompt ("review *it*", "apply *these* fixes")

**Signals the prompt is self-contained:**

- Begins with a one-sentence statement of the goal
- Names every file path as an absolute path
- Embeds the feedback-item list verbatim (short) or pastes the structured record
- States the expected output shape explicitly
- States the constraints (read-only, don't implement, report-only)

## Master template

```
You are evaluating code review feedback independently. Your output will be
combined with the parent agent's own evaluation into one action plan.
You have no prior context about the user or session — work from the prompt
only.

## The change set being reviewed

Base: <commit SHA or ref>
Head: <commit SHA or ref>
Mode: <commits | tool-trail | bash-ops | uncertain>
Files changed:
  <absolute-path-1>
  <absolute-path-2>
  ...

Commands to read the diff (if commit-based):
  git log --oneline <base>..<head>
  git diff <base>..<head>

If tool-trail-based, see the attached file manifest below (each file's
current state is on disk at its absolute path).

## The feedback items to evaluate

Item 1:
  source: <reviewer name / "human partner" / markdown doc / prev message>
  file: <absolute path or "general">
  line: <line number or range or "N/A">
  verbatim: |
    <the exact reviewer text, no paraphrase>

Item 2:
  source: ...
  ...

## What to produce

For each item, produce:

  Item N:
    verdict: <correct | incorrect | unverifiable>
    evidence: <file:line + reasoning — cite specific lines>
    severity: <critical | important | minor>
    suggested_action: <ACCEPT | PUSHBACK | CLARIFY | DEFER | DISMISS>
    reason_if_pushback: <technical reason, one or two sentences>
    clarification_if_needed: <specific question to the reviewer>

## The verification lens

For each item, check:
  1. Correctness — would the reviewer's suggestion break existing functionality?
  2. YAGNI — if the reviewer suggests adding a feature, grep the codebase
     for actual usage of the affected path; if unused, recommend removal
     instead of expansion.
  3. Stack fit — is the suggestion correct for this specific codebase?
  4. Compat — legacy or compatibility reasons for the current implementation?
  5. Context — does the reviewer have the full context? Look at related
     files, not just the reviewed one.
  6. Architecture — does the suggestion conflict with an architectural
     decision documented in this repo (check `docs/`, `CLAUDE.md`,
     `AGENTS.md`, or README)?

## Constraints

- Read-only. Do not Edit, Write, or modify any file. Report only.
- Output is only the structured per-item block above. No preamble, no
  summary, no commentary beyond the required fields.
- Cite specific file:line for every claim. Unsupported claims are
  discarded by the parent agent.
- If an item is unverifiable (needs running code, external data,
  human knowledge), mark it unverifiable and state what would unblock
  verification.
- Max response: 3000 characters. Prefer evidence over prose.
- Do not attempt to "look at the rest of the PR" or "review other files."
  Stay within the change set and the feedback-item list.

## Output format

Return only the per-item blocks, nothing else.
```

## Worked example

**Parent agent's context** (never passes to subagent):

- User said: "The reviewer's notes on PR #42 said three things; evaluate them."
- PR #42 is in `myorg/myrepo`, base `main`, head at `abc1234`
- The 3 items are line-pinned to `src/auth.ts`, `src/session.ts`, `README.md`

**Self-contained prompt passed to the Explore subagent:**

```
You are evaluating code review feedback independently. [...as above...]

## The change set being reviewed

Base: main (current origin/main → e5f6a78)
Head: abc1234
Mode: commits
Files changed:
  /Users/alice/repo/src/auth.ts
  /Users/alice/repo/src/session.ts
  /Users/alice/repo/README.md

Read diff with: git diff e5f6a78..abc1234
(Run from the repo root. `--` pathspec filters must be repo-relative, not absolute; omit them unless you actually need path filtering.)

## The feedback items to evaluate

Item 1:
  source: Copilot (PR review comment id 98765)
  file: /Users/alice/repo/src/auth.ts
  line: 42
  verbatim: |
    Consider adding rate limiting to the login endpoint.

Item 2:
  source: human partner (top-level PR comment)
  file: /Users/alice/repo/src/session.ts
  line: 87
  verbatim: |
    This mutex is held across an async call — potential deadlock?

Item 3:
  source: CodeRabbit (PR review comment id 98770)
  file: /Users/alice/repo/README.md
  line: 14
  verbatim: |
    Typo: "recieve" should be "receive".

## What to produce

[...as above...]
```

**Sample subagent output:**

```
Item 1:
  verdict: unverifiable
  evidence: /Users/alice/repo/src/auth.ts:42 shows the login handler;
    no rate limiter in the middleware stack per scan of
    /Users/alice/repo/src/server.ts:15-30. Whether a rate limiter
    is *needed* depends on deployment context.
  severity: important
  suggested_action: CLARIFY
  reason_if_pushback: N/A
  clarification_if_needed: Is login exposed externally (public internet)
    or internal only? Rate-limiting scope depends.

Item 2:
  verdict: correct
  evidence: /Users/alice/repo/src/session.ts:85-92 shows `mutex.acquire()`
    at L85, `await fetchUser(...)` at L87 (async, network call),
    `mutex.release()` at L91. Classic hold-across-await; risks
    cross-task deadlock if another task also acquires this mutex.
  severity: critical
  suggested_action: ACCEPT
  reason_if_pushback: N/A
  clarification_if_needed: N/A

Item 3:
  verdict: correct
  evidence: /Users/alice/repo/README.md:14 contains "recieve" (misspelled).
  severity: minor
  suggested_action: ACCEPT
  reason_if_pushback: N/A
  clarification_if_needed: N/A
```

The parent agent merges this with its own analysis and produces the final action plan.

## Combining parent + subagent evaluations

Both the parent agent and the subagent produce per-item verdicts. Merge rules:

- **Agreement** — both say ACCEPT or both say PUSHBACK → confident verdict.
- **Disagreement** — parent and subagent differ → surface the disagreement in the action plan. Favor the subagent's verdict only if it cites specific evidence the parent did not consider. Otherwise, mark the item as requiring a human tiebreaker.
- **Subagent unverifiable + parent certain** — if the parent has session context the subagent lacks (e.g., "we discussed deployment context earlier"), the parent's verdict wins, but the reasoning should note the context the subagent lacked.
- **Parent unverifiable + subagent certain** — subagent's verdict wins.

## Anti-patterns

| Anti-pattern | Fix |
|---|---|
| Prompt says "continue evaluating where we left off" | Restart cold; list items verbatim. |
| Prompt passes user's original message | Rewrite into a goal + facts; no user-attribution leakage. |
| Subagent asked to implement fixes | Explore is read-only; the prompt must say "report only". |
| Parent accepts subagent verdict without checking | The subagent is a second opinion, not an authority; weigh evidence. |
| Subagent dispatched with a too-large diff | If the diff is huge (>2000 lines), split by file cluster and dispatch multiple subagents. |

## When to split into multiple subagents

If the change set is large or spans domains:

- > 1500 lines of diff → split by logical cluster (one per domain or file-group)
- > 10 feedback items → split by item group (e.g., "items 1-5" and "items 6-10")
- multi-domain diff (backend + frontend + MCP) → dispatch one per domain; see the request-code-review skill's subagent-dispatch pattern for the fan-out approach

Combine the N subagent outputs in the parent agent per the merge rules above.
